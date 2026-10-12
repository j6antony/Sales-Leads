# Sales Call Modeling Project

## Overview

This project analyzes CRM sales data to understand which factors are associated with stronger outbound-call outcomes and to build a predictive model for identifying calls that are more likely to progress beyond the dominant voicemail-type outcomes.

The project uses three related CRM datasets:

- **Companies:** 15,604 records
- **Contacts:** 57,638 records
- **Calls:** 114,965 records

The project currently includes:

1. Data understanding
2. Data quality analysis
3. Data preprocessing
4. Exploratory data analysis
5. Business findings
6. Modeling target definition
7. Modeling dataset design

The next stage is to train and evaluate the first baseline model.

---

# 1. Data Understanding

The project uses three relational CRM tables.

## Companies

One row represents one company.

Important fields include:

- `Record ID`
- Company name
- Industry
- Number of Employees
- Annual Revenue
- Employee range
- Target Segment
- Lifecycle Stage
- Location
- Associated Contact IDs
- Associated Call IDs

## Contacts

One row represents one contact or prospect.

Important fields include:

- `Record ID`
- First Name
- Last Name
- Job Title
- Job function
- Department
- Management Level
- Industry
- Company Name
- Number of times contacted
- Associated Company IDs
- Associated Call IDs

## Calls

One row represents one logged sales call.

Important fields include:

- `Record ID`
- Activity date
- Call direction
- Call duration
- Call outcome
- Call status
- Connected count
- Activity assigned to
- Associated Contact IDs
- Associated Company IDs

The datasets can approximately be related as:

```text
Company
   ↓
Contact
   ↓
Call
```

Calls can also be linked directly to companies.

---

# 2. Data Quality and Preprocessing

## Primary-Key Validation

`Record ID` was validated as the primary identifier in all three datasets.

| Dataset | Rows | Unique Record IDs | Missing IDs | Duplicate IDs |
| --- | ---: | ---: | ---: | ---: |
| Companies | 15,604 | 15,604 | 0 | 0 |
| Contacts | 57,638 | 57,638 | 0 | 0 |
| Calls | 114,965 | 114,965 | 0 | 0 |

Each dataset therefore has a unique and complete primary key.

---

## Relationship Validation

CRM association IDs were initially stored inconsistently.

Examples included numeric IDs imported with `.0` suffixes:

```text
314292292340.0
```

and fields containing multiple semicolon-separated IDs:

```text
321810077406;177284935365
```

IDs were normalized by:

- converting them to strings
- removing accidental `.0` suffixes
- stripping whitespace
- splitting semicolon-separated associations when required

After normalization:

| Relationship | Invalid Associations |
| --- | ---: |
| Call → Contact | 0 / 114,423 |
| Call → Company | 0 / 111,001 |
| Contact → Company | 0 / 56,732 |

The three datasets can therefore be reliably joined.

---

## Missing Data

The HubSpot export contains many sparse or unused CRM fields.

| Dataset | Columns ≥90% Missing |
| --- | ---: |
| Companies | 156 |
| Contacts | 289 |
| Calls | 63 |

Completely empty columns were also identified:

- Companies: **105**
- Contacts: **141**
- Calls: multiple unused CRM and voice-agent fields

Completely empty and non-informative fields can be removed from the modeling dataset.

---

## Useful Partially Missing Features

Some incomplete fields may still contain useful business information.

Examples include:

### Company Features

- Year Founded
- Secondary Sub-Industry
- Web Technologies
- Description
- Is Public

### Contact Features

- Job function
- Department
- Management Level
- Number of times called
- Secondary Sub-Industry

Missingness was found to vary between call outcomes, meaning missing data is not necessarily random.

For useful variables, missingness indicators may therefore be retained during feature engineering.

---

## Features Excluded From Direct Modeling

Fields that should generally not be used directly as predictors include:

- Record IDs
- Phone numbers
- Email addresses
- LinkedIn URLs
- Website URLs
- Logo URLs
- raw association IDs
- completely empty fields
- single-value fields
- high-cardinality identifiers

IDs are still retained for joining and traceability.

---

## Potential Data Leakage

Some CRM fields may contain information that was only created after the call being predicted.

Examples include:

- `Date entered Sales Qualified Lead`
- `Date entered Marketing Qualified Lead`
- `Last Contacted`
- `Last Activity Date`
- `Last Logged Call Date`
- lifecycle-stage timestamps
- potentially `Transcript Available`

These fields should not be used unless they would have been available at prediction time.

---

# 3. Exploratory Data Analysis

The initial EDA investigated which contact, company, timing, and outreach characteristics were associated with calls progressing beyond the two dominant call outcomes.

For the current analysis:

```text
CVM + GVM = dominant voicemail-type outcomes
Other outcome = call progressed beyond CVM/GVM
```

The exact business definitions of the internal abbreviations should still be confirmed before deployment.

---

## Call Outcome Distribution

The call outcome variable is highly imbalanced.

| Outcome | Calls | Share |
| --- | ---: | ---: |
| CVM | 59,228 | 51.52% |
| GVM | 43,026 | 37.43% |

Together, CVM and GVM represent approximately:

```text
88.95% of all calls
```

This suggests that progressing beyond voicemail-type outcomes is one of the main bottlenecks in the current calling process.

---

# 4. Business Findings

## Repeated Calling Shows Diminishing Returns

| Call Attempt | Non-CVM/GVM Rate |
| --- | ---: |
| 1st call | 15.0% |
| 2nd call | 11.7% |
| 3rd call | 9.7% |
| 4th call | 8.9% |
| 5th call | 8.8% |
| Calls 6–10 | 7.6% |
| 11+ calls | 8.0% |

The first call performs substantially better than later attempts.

This suggests that after approximately 3–5 unsuccessful calls, switching communication channels or contacting another person within the company may be worth testing.

---

## Call Timing

Call performance varies by weekday.

| Day | Non-CVM/GVM Rate |
| --- | ---: |
| Monday | 10.1% |
| Tuesday | 10.0% |
| Wednesday | 10.8% |
| Thursday | 11.7% |
| Friday | 9.0% |

Thursday had the strongest observed performance and Friday the weakest.

Later calls also generally outperformed early-morning calls.

| Hour | Non-CVM/GVM Rate |
| --- | ---: |
| 7 AM | 4.8% |
| 8 AM | 6.8% |
| 9 AM | 9.8% |
| 12 PM | 10.3% |
| 2 PM | 11.0% |
| 3 PM | 11.7% |
| 4 PM | 11.3% |
| 6 PM | 12.7% |

This suggests that afternoon calling may be more effective than very early calling.

Timezone handling should be verified before converting this into a final recommendation.

---

## Management Level

| Management Level | Non-CVM/GVM Rate |
| --- | ---: |
| Manager | 20.2% |
| Director | 10.3% |
| C-Level | 10.2% |
| VP-Level | 8.3% |

Managers showed the strongest observed performance.

---

## Department

| Department | Non-CVM/GVM Rate |
| --- | ---: |
| Medical & Health | 17.7% |
| Operations | 12.3% |
| C-Suite | 10.0% |
| Finance | 9.7% |
| Information Technology | 8.2% |
| Marketing | 7.6% |
| Sales | 7.1% |

Healthcare and operational contacts appear particularly promising.

---

## Job Function

Examples of high-performing functions include:

| Job Function | Non-CVM/GVM Rate |
| --- | ---: |
| Medical Administration | 18.9% |
| Infrastructure | 15.0% |
| Accounting | 13.8% |
| Operations | 12.7% |
| Executive | 11.2% |

---

## Job Title Classification

| Job Classification | Non-CVM/GVM Rate |
| --- | ---: |
| Clinical Director | 20.8% |
| Director – General Management | 17.8% |
| Manager – Finance | 17.2% |
| Director – Revenue Cycle Management | 14.2% |
| Medical Doctor | 14.1% |
| Manager – Operations | 14.0% |
| Chief Medical Officer | 13.0% |
| CEO | 12.4% |
| COO | 10.2% |
| CIO | 9.2% |

Role-specific targeting may therefore be more effective than targeting solely by seniority.

---

## Company Size

| Employee Range | Non-CVM/GVM Rate |
| --- | ---: |
| 51–250 | 14.8% |
| 11–50 | 13.8% |
| 251–1,000 | 12.7% |
| 1–10 | 10.8% |
| 1,000–5,000 | 9.9% |
| 5,000–10,000 | 9.1% |
| 10,000–50,000 | 7.0% |

Mid-sized organizations appear more reachable than very large enterprises.

---

## Industry

| Industry | Non-CVM/GVM Rate |
| --- | ---: |
| Hospitality | 15.4% |
| Transportation | 14.4% |
| Real Estate | 14.0% |
| Oil & Energy | 13.1% |
| Hospital & Health Care | 12.2% |
| Financial Services | 8.8% |
| Retail | 8.6% |
| Insurance | 7.7% |
| Manufacturing | 5.6% |

Healthcare calls performed at more than twice the rate of manufacturing calls.

---

## Target Segment

| Target Segment | Non-CVM/GVM Rate |
| --- | ---: |
| Practice Groups | 14.1% |
| RCM Services | 12.5% |
| Venture Capital Invested | 12.3% |
| Unsegmented | 9.8% |

Existing CRM segmentation therefore appears to contain useful sales signal.

---

## Sales Representative Analysis

Raw non-CVM/GVM rates vary substantially between sales representatives.

These differences should **not yet be interpreted directly as salesperson performance**.

Representatives may receive different:

- industries
- lead quality
- company sizes
- campaigns
- territories
- target segments
- time periods

A multivariate model is required to separate rep effects from lead-assignment effects.

---

# 5. Binary Predictive Modeling Plan

The first predictive model will be a **binary classification model**.

## Target Definition

Calls without a recorded `Call outcome` are removed from the modeling dataset.

The binary target is defined as:

```text
target = 0 → Call outcome is CVM or GVM
target = 1 → Call outcome is any other recorded outcome
```

After excluding missing outcomes:

| Target | Meaning | Calls | Share |
| --- | --- | ---: | ---: |
| 0 | CVM / GVM | 102,254 | 89.6% |
| 1 | Other known outcome | 11,875 | 10.4% |

The model therefore attempts to estimate:

> **How likely is a call to progress beyond the dominant CVM/GVM outcomes?**

---

# 6. Modeling Dataset Design

The modeling dataset will contain:

```text
ONE ROW = ONE CALL
```

Contact and company attributes will be joined onto each call using the validated CRM relationships.

Conceptually:

```text
CALL
│
├── Call-level features
│
├── CONTACT
│   └── Contact characteristics
│
└── COMPANY
    └── Company characteristics
```

---

## Baseline Features

The first model will intentionally use a relatively small and interpretable feature set.

### Call Features

- weekday
- hour
- salesperson (`Activity assigned to`)
- number of previous calls to the same contact

### Contact Features

- Job function
- Department
- Management Level
- Job Title classification
- Secondary Sub-Industry

### Company Features

- Industry
- Year Founded

Potential features with very high missingness, such as `Employee range` and `Target Segment`, will initially be excluded from the baseline and can later be tested in an extended model.

---

# 7. Feature Engineering

## Call Time

`Activity date` will be converted into:

```text
weekday
hour
```

These features allow the model to evaluate whether call timing remains predictive after controlling for other variables.

---

## Previous Call Attempts

The exported CRM field representing total calls should not be used directly because it may include calls that occurred **after the call being predicted**.

Instead, calls will be sorted chronologically by contact and a feature will be generated:

```text
prior_calls_to_contact
```

Example:

```text
First call  → 0 previous calls
Second call → 1 previous call
Third call  → 2 previous calls
```

This prevents future call activity from leaking into earlier predictions.

---

## Missing Values

Useful categorical features with missing values can be represented using:

```text
Unknown
```

or additional missing-value indicators where appropriate.

Numerical features will be imputed using values derived from the training data only.

---

## Categorical Encoding

Categorical variables such as:

- Industry
- Department
- Management Level
- Job function
- weekday
- salesperson

will be transformed into machine-readable features using techniques such as one-hot encoding.

High-cardinality variables will be reviewed before inclusion.

---

# 8. Train/Test Strategy

The modeling data will be divided into separate training and testing sets.

The test set will remain unseen while the model is trained.

Because sales activity occurs over time, a chronological split should also be considered so that older calls are used to predict newer calls.

This more closely represents how the model would behave in production.

---

# 9. Baseline Model

The first model will be:

```text
Logistic Regression
```

Logistic regression was selected as the baseline because it is:

- simple
- fast
- interpretable
- appropriate for binary classification
- useful for understanding which factors increase or decrease predicted probability

The baseline can later be compared against more complex models such as:

- Random Forest
- Gradient Boosting
- XGBoost / LightGBM

---

# 10. Model Evaluation

Because the target is highly imbalanced:

```text
Class 0 ≈ 89.6%
Class 1 ≈ 10.4%
```

**accuracy alone will not be used as the primary evaluation metric.**

A model that predicts every call as `0` would already achieve approximately 89.6% accuracy while providing no useful business value.

Evaluation will therefore focus on:

- Precision
- Recall
- F1 Score
- ROC-AUC
- Precision-Recall AUC
- Confusion Matrix

Particular attention will be paid to performance on:

```text
Class 1 = calls predicted to progress beyond CVM/GVM
```

---

# 11. Modeling Goals

The model should help answer questions such as:

- Which contacts have the highest probability of producing meaningful engagement?
- Which industries are most promising after controlling for other factors?
- Does management level still matter after controlling for company and call characteristics?
- Does calling on Thursday remain beneficial after controlling for rep and lead mix?
- How strongly do previous failed call attempts reduce predicted engagement?
- Are apparent salesperson differences explained by lead allocation?
- Which combinations of prospect characteristics should sales prioritize?

The goal is not simply to predict call outcomes.

The final objective is to produce a **prospect prioritization system** that can help the sales team direct outbound effort toward calls with a higher probability of meaningful engagement.

---

# 12. Current Project Status

```text
[✓] Data Understanding
[✓] Primary-Key Validation
[✓] Relationship Validation
[✓] Missing-Data Analysis
[✓] Data Quality Assessment
[✓] Preprocessing Strategy
[✓] Exploratory Data Analysis
[✓] Initial Business Findings

[✓] Binary Target Definition
[✓] Initial Feature Selection
[✓] Modeling Dataset Design
[✓] Leakage Review
[✓] Evaluation Strategy

[ ] Build Final Modeling Table
[ ] Train/Test Split
[ ] Preprocessing Pipeline
[ ] Logistic Regression Baseline
[ ] Baseline Evaluation
[ ] Feature Interpretation
[ ] Alternative Models
[ ] Model Comparison
[ ] Final Sales Recommendations
```

## Logistic Regression Baseline

Two Logistic Regression models were evaluated using the same chronological train/test split:

- **Unweighted Logistic Regression**
- **Balanced Logistic Regression** using `class_weight="balanced"`

The modeling target was defined as:

```text
0 = CVM or GVM
1 = Any other recorded call outcome
```

The test set contained:

- **19,498 class-0 calls**
- **3,328 class-1 calls**

This corresponds to a positive-class rate of approximately **14.6%** in the test period.

### Unweighted Logistic Regression

The standard Logistic Regression model strongly favored the majority class.

| Metric | Class 0 | Class 1 |
| --- | ---: | ---: |
| Precision | 0.85 | 0.16 |
| Recall | 0.99 | 0.01 |
| F1 Score | 0.92 | 0.02 |

Overall metrics:

- Accuracy: **0.85**
- ROC-AUC: **0.5278**
- PR-AUC: **0.1572**

Confusion matrix:

```text
[[19300   198]
 [ 3290    38]]
```

The model correctly identified only **38 of the 3,328 class-1 calls**, giving a class-1 recall of approximately **1%**.

Although the model achieved 85% accuracy, this result is misleading because approximately 85% of the test data belongs to class 0. The model achieved high accuracy primarily by predicting the majority class almost every time.

Therefore, the unweighted model is not useful for identifying calls likely to progress beyond CVM/GVM.

---

### Balanced Logistic Regression

A second Logistic Regression model was trained using:

```python
LogisticRegression(
    class_weight="balanced",
    max_iter=1000
)
```

This assigns greater importance to errors made on the minority class during training.

Results:

| Metric | Class 0 | Class 1 |
| --- | ---: | ---: |
| Precision | 0.87 | 0.17 |
| Recall | 0.62 | 0.46 |
| F1 Score | 0.72 | 0.25 |

Overall metrics:

- Accuracy: **0.59**
- ROC-AUC: **0.5269**
- PR-AUC: **0.1553**

Confusion matrix:

```text
[[12004  7494]
 [ 1795  1533]]
```

The balanced model identified **1,533 of the 3,328 class-1 calls**, increasing class-1 recall from approximately **1% to 46%**.

However, this improvement came with a large increase in false positives.

---

### Model Comparison

| Model | Accuracy | Class-1 Precision | Class-1 Recall | Class-1 F1 | ROC-AUC | PR-AUC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Unweighted Logistic Regression | 0.85 | 0.16 | 0.01 | 0.02 | 0.5278 | 0.1572 |
| Balanced Logistic Regression | 0.59 | 0.17 | 0.46 | 0.25 | 0.5269 | 0.1553 |

The balanced model performs much better at detecting the minority class, but both models have very similar ROC-AUC and PR-AUC values.

This indicates that class weighting changes the decision behavior of the classifier but does not substantially improve its ability to separate class 0 from class 1.

The balanced model is therefore preferable for the current objective because it identifies substantially more class-1 calls, but the overall predictive signal remains weak.

---

### Interpretation

The Logistic Regression results suggest that the main limitation is not only class imbalance.

Both models achieve an ROC-AUC of approximately **0.53**, which is only slightly above random classification.

The PR-AUC values are also only slightly above the test-set positive rate of approximately **14.6%**.

This suggests that the current pre-call features do not strongly separate:

```text
CVM/GVM
```

from:

```text
all other call outcomes
```

One likely issue is the definition of the positive class.

The current class `1` includes many different outcomes, such as successful engagement, callbacks, wrong numbers, negative responses, and other call results. These outcomes do not necessarily represent a single consistent business behavior.

---

### Current Conclusion

The initial Logistic Regression experiment established three key findings:

1. **Class imbalance must be explicitly handled.**  
   The unweighted model almost completely ignores the minority class.

2. **Class weighting improves minority-class detection.**  
   Class-1 recall increased from approximately 1% to 46%.

3. **The current target remains difficult to predict.**  
   Similar ROC-AUC and PR-AUC values across both models indicate that the feature set provides limited separation between the two current target classes.

The next modeling step is to reconsider the target definition so that class `1` represents a more meaningful positive sales-engagement outcome, then retrain the baseline before testing more complex nonlinear models.


