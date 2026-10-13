import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score
)
from xgboost import XGBClassifier


#load the csv files into pandas
calls = pd.read_csv(
    "data/calls data(Recorded calls).csv",
    dtype={"Record ID": "string", "Associated Contact IDs": "string", "Associated Company IDs": "string"},
    low_memory=False,
)
companies = pd.read_csv(
    "data/All Companies(All companies).csv",
    dtype={"Record ID": "string"},
    low_memory=False,
)
contacts = pd.read_csv(
    "data/All contacts(All contacts).csv",
    dtype={"Record ID": "string"},
    low_memory=False,
)


#model should take these into consideration when trying to predict 1 or 0
features = [
    "weekday",
    "hour",
    "Activity assigned to",

    # Historical behaviour
    "prior_calls_to_contact",
    "days_since_last_call",
    "prior_positive_calls",
    "prior_negative_calls",
    "prior_success_rate",
    "days_since_last_positive",

    # Contact information
    "Job function",
    "Department",
    "Management Level",
    "Job Title classification",
    "Secondary Sub-Industry",

    # Company information
    "Industry",
    "Year Founded"
]

# Build the dataset first
def clean_id(value: str):
    if pd.isna(value):
        return None
    value = str(value).strip()

    #this is a huge issue becuase some of the id's end with .0 which is make mismatches between tables and coloumns
    if value.endswith(".0"):
        value = value[:-2]
    return value
# This function returns the first id in a list seperated by ;
def first_associated_id(value: str):
    if pd.isna(value):
        return None
    return clean_id(str(value).split(";")[0])

#PREPARE CALLS
# remove any empty rows
model_calls = calls[
    calls["Call outcome"].notna() 
].copy()

#just assigning binary bool values for if outcome is CVM or GVM
model_calls["target"] = (
    ~model_calls["Call outcome"].isin(["CVM", "GVM"])
).astype(int)

#this is just setting the date and time to the pd datetime structure
model_calls["activity_dt"] = pd.to_datetime(
    model_calls["Activity date"],
    errors="coerce"
)

# not exactly sure how this works but it helps to merge the other tables information
model_calls["contact_id"] = (
    model_calls["Associated Contact IDs"]
    .apply(first_associated_id)
)
model_calls["company_id"] = (
    model_calls["Associated Company IDs"].apply(first_associated_id)
)

#PREPARE CONTACTS
contacts_model = contacts.copy()
#save record id as contact_id
contacts_model["contact_id"] = (
    contacts_model["Record ID"].apply(clean_id)
)

#PREPARE COMPANIES
companies_model = companies.copy()

companies_model["company_id"] = (
    companies_model["Record ID"].apply(clean_id)
)

#merge contacts with calls
contact_features = [
    "contact_id",
    "Job function",
    "Department",
    "Management Level",
    "Job Title classification",
    "Secondary Sub-Industry"
]

model_data = model_calls.merge(
    contacts_model[contact_features],
    on="contact_id",
    how="left"
)



#merge companies table with calls table
company_features = [
    "company_id",
    "Industry",
    "Year Founded"
]
model_data = model_data.merge(
    companies_model[company_features],
    on="company_id",
    how="left"
)

#add the timing coloumns to the table so like weekday and hour
model_data["weekday"] = (
    model_data["activity_dt"].dt.day_name()
)
model_data["hour"] = (
    model_data["activity_dt"].dt.hour
)

#calculate how many call attempts have been made
#this sort is necessary so it follows like a cronological order and you model cannot cheat
model_data = model_data.sort_values(
    ["contact_id", "activity_dt", "Record ID"]
).reset_index(drop = True)
# build call history so basically it is storing whether there has been previous calls when how long and as well how many days ago
model_data["prior_calls_to_contact"] = (
    model_data
    .groupby("contact_id")
    .cumcount()
)
model_data["previous_call_time"] = (
    model_data.groupby("contact_id")["activity_dt"].shift(1)
)
model_data["days_since_last_call"] = (
    model_data["activity_dt"] - model_data["previous_call_time"]
).dt.total_seconds()/86400

#using history to creat positive or negative calls
model_data["previous_target"] = (
    model_data.groupby("contact_id")["target"].shift(1)
)
model_data["prior_positive_calls"] = (
    model_data["previous_target"].eq(1).groupby(model_data["contact_id"]).cumsum()
)
model_data["prior_negative_calls"] = (
    model_data["previous_target"].eq(0).groupby(model_data["contact_id"]).cumsum()
)


#create historical success rate
model_data["prior_success_rate"] = (
    model_data["prior_positive_calls"] /
    model_data["prior_negative_calls"].replace(0, pd.NA)
)

#see how many days since last positive engagement
model_data["positive_call_time"] = (
    model_data["activity_dt"]
    .where(model_data["target"] == 1)
)

model_data["last_positive_time"] = (
    model_data.groupby("contact_id")["positive_call_time"]
    .transform(lambda x: x.shift(1).ffill())
)

model_data["days_since_last_positive"] = (
    model_data["activity_dt"] -
    model_data["last_positive_time"]
).dt.total_seconds() / 86400
#sanity check
""" #model_data table sanity check
print("Shape:", model_data.shape)

print("\nColumns:")
print(model_data.columns.tolist())

print("\nTarget distribution:")
print(model_data["target"].value_counts())
print(model_data["target"].value_counts(normalize=True).round(4))

print("\nMissing percentages:")
print(
    (model_data.isna().mean() * 100)
    .sort_values(ascending=False)
    .round(2)
) """

#redifine the features so we dont check empty and nonexistent coloumns
model_data = model_data.sort_values("activity_dt").reset_index(drop=True)

X = model_data[features].copy()
Y = model_data["target"].copy()

#split the older 80% for training and use the newer 20% for validation
split_index = int(len(model_data) * 0.80)

x_train = X.iloc[:split_index].copy()
x_test = X.iloc[split_index:].copy()

y_train = Y.iloc[:split_index].copy()
y_test = Y.iloc[split_index:].copy()

#dataset splitting and ordering sanity check
""" print("TRAIN")
print(y_train.value_counts())
print(y_train.value_counts(normalize=True).round(3))

print("\nTEST")
print(y_test.value_counts())
print(y_test.value_counts(normalize=True).round(3))

print(
    "Training dates:",
    model_data.iloc[:split_index]["activity_dt"].min(),
    "to",
    model_data.iloc[:split_index]["activity_dt"].max()
)

print(
    "Testing dates:",
    model_data.iloc[split_index:]["activity_dt"].min(),
    "to",
    model_data.iloc[split_index:]["activity_dt"].max()
) """

#TRAIN THE BALANCED LOGISTIC REGRESSION machine learning model

categorical_features = [
    "weekday",
    "Activity assigned to",
    "Job function",
    "Department",
    "Management Level",
    "Job Title classification",
    "Secondary Sub-Industry",
    "Industry"
]
numeric_features = [
    "hour",
    "prior_calls_to_contact",
    "days_since_last_call",
    "prior_positive_calls",
    "prior_negative_calls",
    "prior_success_rate",
    "days_since_last_positive",
    "Year Founded"
]

# Use NumPy missing values for sklearn, and keep numeric columns numeric.
for frame in (x_train, x_test):
    for column in categorical_features:
        values = frame[column].astype(object)
        frame[column] = values.where(values.notna(), np.nan)
    for column in numeric_features:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").astype(float)

categorical_pipeline = Pipeline([
    (
        "imputer",
        SimpleImputer(
            strategy="constant",
            fill_value="Unknown"
        )
    ),
    (
        "encoder",
        OneHotEncoder(
            handle_unknown="ignore"
        )
    )
])

numeric_pipeline = Pipeline([
    (
        "imputer",
        SimpleImputer(strategy="median")
    ),
    (
        "scaler",
        StandardScaler()
    )
])

preprocessor = ColumnTransformer([
    (
        "categorical",
        categorical_pipeline,
        categorical_features
    ),
    (
        "numeric",
        numeric_pipeline,
        numeric_features
    )
])
#balanced logistic regression
model = Pipeline([
    ("preprocessor", preprocessor),
    (
        "classifier",
        LogisticRegression(
            class_weight="balanced",
            max_iter=1000
        )
    )
])


model.fit(x_train, y_train)

y_pred = model.predict(x_test)

y_prob = model.predict_proba(x_test)[:, 1]

print("Classification Report:")
print(classification_report(y_test, y_pred))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

print(
    "\nROC-AUC:",
    round(roc_auc_score(y_test, y_prob), 4)
)

print(
    "PR-AUC:",
    round(average_precision_score(y_test, y_prob), 4)
)

#try the xgboost model


neg = (y_train == 0).sum()
pos = (y_train == 1).sum()

scale_pos_weight = neg/pos

print(scale_pos_weight)

xgb_model = Pipeline([
    ("preprocessort", preprocessor),
    (
        "classifier",
        XGBClassifier(
            n_estimators = 300,
            max_depth = 4,
            learning_rate = 0.05,
            subsample = 0.8,
            colsample_bytree = 0.8,
            scale_pos_weight = scale_pos_weight,
            eval_metric = "logloss",
            random_state = 42
        )
    )
])

xgb_model.fit(x_train, y_train)

y_pred_xgb = xgb_model.predict(x_test)
y_prob_xgb = xgb_model.predict_proba(x_test)[:, 1]

print("Classification Report:")
print(classification_report(y_test, y_pred_xgb))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred_xgb))

print(
    "\nROC-AUC:",
    round(roc_auc_score(y_test, y_prob_xgb), 4)
)

print(
    "PR-AUC:",
    round(average_precision_score(y_test, y_prob_xgb), 4)
)

#try with threshold 
split_val = int(len(x_train) * 0.80)
x_train2 = x_train.iloc[:split_val]
x_val = x_train.iloc[split_val:]

y_train2 = y_train.iloc[:split_val]
y_val = y_train.iloc[split_val:]

xgb_model.fit(x_train2, y_train2)
val_prob = xgb_model.predict_proba(x_val)[:, 1]

for threshold in [0.30, 0.35, 0.40, 0.45, 0.50,
                  0.55, 0.60, 0.65, 0.70, 0.75]:

    predictions = (val_prob >= threshold).astype(int)

    precision = precision_score(y_val, predictions)
    recall = recall_score(y_val, predictions)
    f1 = f1_score(y_val, predictions)

    print(
        f"Threshold: {threshold:.2f} | "
        f"Precision: {precision:.3f} | "
        f"Recall: {recall:.3f} | "
        f"F1: {f1:.3f}"
    )

#from analysis best threshold is 0.55

Best_Threshold = 0.55

xgb_model.fit(x_train, y_train)
test_prob = xgb_model.predict_proba(x_test)[:, 1]
y_pred_final = (
    test_prob >= Best_Threshold
).astype(int)


print(classification_report(y_test, y_pred_final))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred_final))

print(
    "\nROC-AUC:",
    round(roc_auc_score(y_test, test_prob), 4)
)

print(
    "PR-AUC:",
    round(average_precision_score(y_test, test_prob), 4)
)