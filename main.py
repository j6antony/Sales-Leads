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
    average_precision_score
)


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
    "prior_calls_to_contact",
    "Job function",
    "Department",
    "Management Level",
    "Job Title classification",
    "Secondary Sub-Industry",
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
)

model_data["prior_calls_to_contact"] = (
    model_data
    .groupby("contact_id")
    .cumcount()
)
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
    "Year Founded"
]

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
modelA = Pipeline([
    ("preprocessor", preprocessor),
    (
        "classifier",
        HistGradientBoosting
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