# Sales Call Modeling Project

## Overview

This project analyzes CRM sales data to understand which factors are associated with stronger outbound-call outcomes and to build a predictive model for identifying calls that are more likely to result in meaningful sales engagement.

The project uses three related CRM datasets:

- **Companies:** 15,604 records
- **Contacts:** 57,638 records
- **Calls:** 114,965 records

The workflow currently includes:

1. Data understanding
2. Data quality analysis
3. Relationship validation
4. Exploratory data analysis
5. Initial target definition
6. Baseline modeling
7. Target refinement
8. Historical feature engineering
9. Logistic Regression modeling
10. XGBoost modeling
11. Threshold tuning
12. Final model evaluation

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
- Employee range
- Target Segment
- Year Founded
- Associated Contact IDs
- Associated Call IDs

## Contacts

One row represents one contact or prospect.

Important fields include:

- `Record ID`
- Job Title
- Job function
- Department
- Management Level
- Industry
- Company Name
- Associated Company IDs
- Associated Call IDs

## Calls

One row represents one logged sales call.

Important fields include:

- `Record ID`
- Activity date
- Call outcome
- Call direction
- Activity assigned to
- Associated Contact IDs
- Associated Company IDs

The datasets can approximately be represented as:

```text
Company
   ↓
Contact
   ↓
Call
```

Calls can also be linked directly to companies.

---

# 2. Data Quality Analysis

## Primary-Key Validation

`Record ID` was validated as the primary identifier in all three datasets.

| Dataset | Rows | Unique IDs | Missing IDs | Duplicate IDs |
| --- | ---: | ---: | ---: | ---: |
| Companies | 15,604 | 15,604 | 0 | 0 |
| Contacts | 57,638 | 57,638 | 0 | 0 |
| Calls | 114,965 | 114,965 | 0 | 0 |

All three datasets therefore contain complete and unique primary keys.

---

## Relationship Validation

CRM association fields were stored inconsistently.

Some IDs were imported as numeric values with `.0` suffixes:

```text
314292292340.0
```

while other fields contained multiple semicolon-separated IDs:

```text
321810077406;177284935365
```

IDs were normalized by:

- converting values to strings
- removing `.0` suffixes
- stripping whitespace
- splitting multiple associations where necessary

After cleaning:

| Relationship | Invalid Associations |
| --- | ---: |
| Call → Contact | 0 / 114,423 |
| Call → Company | 0 / 111,001 |
| Contact → Company | 0 / 56,732 |

The datasets can therefore be reliably joined.

---

# 3. Missing Data

The CRM export contains many sparse or unused fields.

| Dataset | Columns ≥90% Missing |
| --- | ---: |
| Companies | 156 |
| Contacts | 289 |
| Calls | 63 |

Completely empty columns were also identified.

Many of these fields were excluded from modeling.

Useful partially populated fields were retained when they could provide business signal.

Examples include:

- Job function
- Department
- Management Level
- Secondary Sub-Industry
- Industry
- Year Founded

Missing values are handled inside the model preprocessing pipeline rather than simply dropping records.

---

# 4. Data Leakage Review

Potential leakage fields were identified and excluded.

Examples include:

- Last Contacted
- Last Activity Date
- Last Logged Call Date
- lifecycle-stage timestamps
- other fields created after the call occurred

The modeling process only uses information that would realistically have been available before the call being predicted.

This is especially important for historical call behavior.

For example, instead of using an exported total call count, the number of previous calls is recalculated chronologically.

---

# 5. Exploratory Data Analysis

Initial EDA showed several patterns associated with stronger call outcomes.

Examples included:

- earlier call attempts performed better than later attempts
- Wednesday and Thursday generally outperformed Friday
- afternoon calls generally performed better than early-morning calls
- managers showed stronger observed engagement rates than some more senior roles
- healthcare and operational contacts performed relatively well
- mid-sized organizations generally performed better than very large companies

These relationships were useful for business understanding but did not necessarily provide enough signal for reliable prediction at the individual-call level.

---

# 6. Initial Modeling Target

The first modeling attempt used:

```text
0 = CVM or GVM
1 = any other recorded call outcome
```

This resulted in:

| Target | Calls | Share |
| --- | ---: | ---: |
| 0 | 102,254 | 89.6% |
| 1 | 11,875 | 10.4% |

This target was highly imbalanced.

More importantly, class `1` contained many different types of outcomes and did not necessarily represent one consistent business event.

This became an important limitation during modeling.

---

# 7. Chronological Train/Test Split

Instead of randomly splitting calls, the dataset was split chronologically.

This more closely represents production use:

```text
Past calls
   ↓
Train model
   ↓
Future calls
   ↓
Test model
```

Training period:

```text
2024-01-09 → 2026-05-07
```

Testing period:

```text
2026-05-07 → 2026-09-28
```

Training distribution:

| Target | Count | Share |
| --- | ---: | ---: |
| 0 | 82,756 | 90.6% |
| 1 | 8,547 | 9.4% |

Test distribution:

| Target | Count | Share |
| --- | ---: | ---: |
| 0 | 19,498 | 85.4% |
| 1 | 3,328 | 14.6% |

The increase in positive outcomes over time suggests that the sales process or lead population changed during the period.

---

# 8. Initial Logistic Regression Models

Two Logistic Regression models were evaluated.

## Unweighted Logistic Regression

Results:

| Metric | Class 0 | Class 1 |
| --- | ---: | ---: |
| Precision | 0.85 | 0.16 |
| Recall | 0.99 | 0.01 |
| F1 | 0.92 | 0.02 |

Overall:

- Accuracy: **0.85**
- ROC-AUC: **0.5278**
- PR-AUC: **0.1572**

Confusion matrix:

```text
[[19300   198]
 [ 3290    38]]
```

The model predicted almost every call as class `0`.

Although accuracy appeared high, the model identified only **38 of the 3,328 positive calls**.

This demonstrated that accuracy was not an appropriate primary metric for the imbalanced target.

---

## Balanced Logistic Regression

A second model used:

```python
LogisticRegression(
    class_weight="balanced",
    max_iter=1000
)
```

Results:

| Metric | Class 0 | Class 1 |
| --- | ---: | ---: |
| Precision | 0.87 | 0.17 |
| Recall | 0.62 | 0.46 |
| F1 | 0.72 | 0.25 |

Overall:

- Accuracy: **0.59**
- ROC-AUC: **0.5269**
- PR-AUC: **0.1553**

Confusion matrix:

```text
[[12004  7494]
 [ 1795  1533]]
```

Class weighting increased positive-class recall from approximately **1% to 46%**, but ranking performance remained close to random.

This suggested that the main problem was not simply class imbalance.

The original feature set and target definition contained limited predictive signal.

---

# 9. Target Refinement

The modeling target was then redefined to better represent meaningful sales engagement.

Instead of treating every non-CVM/GVM outcome as positive, outcomes were grouped based on business meaning.

The refined modeling objective became:

```text
0 = clearly unsuccessful interaction
1 = clearly positive sales engagement
```

Ambiguous outcomes can be excluded until their CRM definitions are confirmed.

This produces a more coherent target for supervised learning.

---

# 10. Historical Feature Engineering

The original model relied heavily on relatively static characteristics such as:

- industry
- job role
- department
- management level
- call timing

These variables were useful for segmentation but provided limited predictive power.

The model was therefore expanded with historical behavior features calculated using only information available before each call.

Historical features include:

- `prior_calls_to_contact`
- `days_since_last_call`
- `prior_positive_calls`
- `prior_negative_calls`
- `prior_success_rate`
- `days_since_last_positive`

Calls were sorted chronologically by contact before generating these variables.

For example:

```text
First call
prior_calls_to_contact = 0

Second call
prior_calls_to_contact = 1

Third call
prior_calls_to_contact = 2
```

Previous outcomes were shifted so the current call outcome could not leak into its own predictors.

---

# 11. Improved Logistic Regression

The balanced Logistic Regression model was retrained after adding historical behavior features.

Results:

| Metric | Class 0 | Class 1 |
| --- | ---: | ---: |
| Precision | 0.90 | 0.22 |
| Recall | 0.63 | 0.61 |
| F1 | 0.74 | 0.32 |

Overall:

- Accuracy: **0.62**
- ROC-AUC: **0.6554**
- PR-AUC: **0.2655**

Confusion matrix:

```text
[[12228  7270]
 [ 1298  2030]]
```

This was a substantial improvement over the original Logistic Regression.

Comparison:

| Metric | Original Balanced LR | Historical-Feature LR |
| --- | ---: | ---: |
| Precision | 0.17 | **0.22** |
| Recall | 0.46 | **0.61** |
| F1 | 0.25 | **0.32** |
| ROC-AUC | 0.5269 | **0.6554** |
| PR-AUC | 0.1553 | **0.2655** |

This demonstrated that historical behavior contained significantly more predictive signal than static CRM attributes alone.

---

# 12. XGBoost Model

A nonlinear XGBoost classifier was then trained using the same features and chronological data split.

Class imbalance was handled using `scale_pos_weight`.

Default-threshold results:

| Metric | Class 0 | Class 1 |
| --- | ---: | ---: |
| Precision | 0.91 | 0.23 |
| Recall | 0.62 | 0.64 |
| F1 | 0.74 | 0.33 |

Overall:

- Accuracy: **0.63**
- ROC-AUC: **0.6952**
- PR-AUC: **0.2943**

Confusion matrix:

```text
[[12139  7359]
 [ 1190  2138]]
```

XGBoost outperformed Logistic Regression across the most important minority-class and ranking metrics.

---

# 13. Model Comparison

| Model | Class-1 Precision | Class-1 Recall | Class-1 F1 | ROC-AUC | PR-AUC |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original Unweighted LR | 0.16 | 0.01 | 0.02 | 0.5278 | 0.1572 |
| Original Balanced LR | 0.17 | 0.46 | 0.25 | 0.5269 | 0.1553 |
| Historical Balanced LR | 0.22 | 0.61 | 0.32 | 0.6554 | 0.2655 |
| XGBoost | **0.23** | **0.64** | **0.33** | **0.6952** | **0.2943** |

The largest performance increase came from **feature engineering**, while XGBoost provided an additional improvement by learning nonlinear relationships and feature interactions.

---

# 14. Threshold Tuning

The default classifier threshold of `0.50` was not assumed to be optimal.

Thresholds were evaluated on validation data.

| Threshold | Precision | Recall | F1 |
| ---: | ---: | ---: | ---: |
| 0.30 | 0.183 | 0.890 | 0.303 |
| 0.35 | 0.204 | 0.854 | 0.330 |
| 0.40 | 0.223 | 0.816 | 0.351 |
| 0.45 | 0.246 | 0.772 | 0.373 |
| 0.50 | 0.263 | 0.728 | 0.387 |
| **0.55** | **0.305** | **0.662** | **0.417** |
| 0.60 | 0.322 | 0.532 | 0.402 |
| 0.65 | 0.335 | 0.422 | 0.373 |
| 0.70 | 0.448 | 0.242 | 0.314 |
| 0.75 | 0.573 | 0.159 | 0.249 |

A threshold of:

```text
0.55
```

was selected because it produced the highest F1 score among the tested thresholds while maintaining relatively strong recall.

---

# 15. Final XGBoost Evaluation

The XGBoost model was retrained on the full training dataset and evaluated on the untouched chronological test set using the selected threshold of `0.55`.

Final results:

| Metric | Class 0 | Class 1 |
| --- | ---: | ---: |
| Precision | 0.90 | 0.23 |
| Recall | 0.66 | 0.59 |
| F1 | 0.77 | 0.33 |

Overall:

- Accuracy: **0.65**
- ROC-AUC: **0.6952**
- PR-AUC: **0.2943**

Final confusion matrix:

```text
[[12930  6568]
 [ 1374  1954]]
```

The model identified:

```text
1,954 / 3,328
```

positive-engagement calls.

This corresponds to approximately:

```text
59% recall
```

while reducing false positives compared with the default `0.50` threshold.

---

# 16. Main Modeling Findings

Several important findings emerged from the modeling process.

## Static demographic features alone were weak predictors

Features such as:

- industry
- management level
- department
- job title
- call timing

contained useful business-level patterns but were not sufficient for strong individual-call prediction.

---

## Historical behavior significantly improved performance

Adding pre-call historical features increased ROC-AUC from approximately:

```text
0.53 → 0.66
```

for Logistic Regression.

This indicates that previous interaction history is much more informative than static CRM attributes alone.

---

## Nonlinear modeling provided additional improvement

XGBoost increased ROC-AUC further:

```text
0.6554 → 0.6952
```

and PR-AUC:

```text
0.2655 → 0.2943
```

This suggests that useful nonlinear relationships and feature interactions exist in the sales data.

---

## Threshold selection should reflect business priorities

A threshold of `0.55` produced the best observed F1 balance on validation data.

However, the threshold can be adjusted depending on sales capacity.

For example:

```text
Lower threshold
→ more prospects flagged
→ higher recall
→ more false positives
```

while:

```text
Higher threshold
→ fewer prospects flagged
→ higher precision
→ lower recall
```

The final operating threshold should therefore eventually be selected based on the sales team's cost of missed opportunities versus unnecessary calls.

---

# 17. Current Best Model

The current best-performing model is:

```text
Model: XGBoost
Decision Threshold: 0.55

ROC-AUC: 0.6952
PR-AUC: 0.2943

Class-1 Precision: 0.23
Class-1 Recall:    0.59
Class-1 F1:        0.33
```

The model is substantially better than the original Logistic Regression baseline but still has room for improvement.

It should currently be interpreted primarily as a **lead-ranking / prioritization model**, rather than a perfect binary predictor.

---

# 18. Current Project Status

```text
[✓] Data Understanding
[✓] Primary-Key Validation
[✓] Relationship Validation
[✓] Missing-Data Analysis
[✓] Leakage Review
[✓] Exploratory Data Analysis
[✓] Initial Business Findings

[✓] Initial Binary Target
[✓] Initial Logistic Regression
[✓] Class-Imbalance Analysis
[✓] Target Refinement
[✓] Historical Feature Engineering
[✓] Chronological Train/Test Split
[✓] Improved Logistic Regression
[✓] XGBoost Model
[✓] Model Comparison
[✓] Validation-Based Threshold Tuning
[✓] Final XGBoost Test Evaluation

[ ] Feature Importance Analysis
[ ] SHAP Explainability Analysis
[ ] Lead-Priority Scoring
[ ] High / Medium / Low Priority Segmentation
[ ] Additional Feature Engineering
[ ] Model Calibration
[ ] Business-Level Evaluation
[ ] Final Sales Recommendations
```

# 19. Next Step

The immediate next step is to analyze **feature importance and SHAP values** for the XGBoost model.

This will help determine which factors are actually driving predictions and translate the model into business insights such as:

- which historical behaviors matter most
- whether industry remains important after controlling for call history
- whether salesperson assignment affects predictions
- which roles or departments are associated with higher engagement likelihood
- how recency and previous engagement influence future calls

After explainability analysis, predicted probabilities can be converted into practical lead-priority groups such as:

```text
High Priority
Medium Priority
Low Priority
```

for use in sales prioritization.
