# Sales Call Modeling Project

## Overview

This project analyzes CRM sales data to understand which factors are associated with better outbound-call outcomes and to prepare the data for predictive modeling.

The source data consists of three related CRM datasets:

- **Companies:** 15,604 records
- **Contacts:** 57,638 records
- **Calls:** 114,965 records

The current work has focused on:

1. Data understanding
2. Data quality and preprocessing
3. Exploratory data analysis
4. Business findings

Predictive modeling is the next stage.

---

## 1. Data Understanding

The project uses three relational CRM tables.

### Companies

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

### Contacts

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

### Calls

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

The datasets can therefore be related approximately as:

```text
Company
   ↓
Contact
   ↓
Call
```

Calls can also be linked directly to companies.

---

## 2. Data Quality and Preprocessing

### Primary-Key Validation

`Record ID` was validated as the primary identifier in all three datasets.

| Dataset | Rows | Unique Record IDs | Missing IDs | Duplicate IDs |
| --- | ---: | ---: | ---: | ---: |
| Companies | 15,604 | 15,604 | 0 | 0 |
| Contacts | 57,638 | 57,638 | 0 | 0 |
| Calls | 114,965 | 114,965 | 0 | 0 |

This confirmed that each dataset has a unique and complete primary key.

---

### Relationship Validation

The CRM association fields originally appeared to contain invalid relationships because some IDs were imported as floating-point values such as:

```text
314292292340.0
```

instead of:

```text
314292292340
```

Some association columns also contain multiple IDs separated by semicolons:

```text
321810077406;177284935365
```

A normalization step was therefore introduced to:

- convert IDs to strings
- remove accidental `.0` suffixes
- strip whitespace
- split semicolon-separated IDs when validating relationships

After normalization:

| Relationship | Invalid Associations |
| --- | ---: |
| Call → Contact | 0 / 114,423 |
| Call → Company | 0 / 111,001 |
| Contact → Company | 0 / 56,732 |

The datasets therefore have strong referential integrity and can be reliably joined.

---

### Missing Data

The CRM export contains a large number of sparse or unused fields.

| Dataset | Columns ≥90% Missing |
| --- | ---: |
| Companies | 156 |
| Contacts | 289 |
| Calls | 63 |

Completely empty columns were also identified:

- Companies: **105**
- Contacts: **141**
- Calls: many unused CRM and voice-agent fields

These columns contain no analytical value and should be removed from the modeling dataset.

---

### Useful Partially Missing Features

Not every incomplete column should be removed.

Several potentially valuable variables contain moderate levels of missingness, including:

#### Company Features

- Year Founded
- Secondary Sub-Industry
- Web Technologies
- Description
- Is Public
- Number of times contacted

#### Contact Features

- Job function
- Department
- Management Level
- Number of times called
- Number of times contacted
- City
- Secondary Sub-Industry

Missingness was found to vary between call outcomes, suggesting that missing values are not completely random.

For useful features, missingness can therefore be preserved using indicators such as:

```python
contacts["management_level_missing"] = (
    contacts["Management Level"].isna().astype(int)
)
```

---

### Columns Not Suitable as Direct Model Features

The following fields should generally not be used directly as predictive features:

- Record IDs
- Phone numbers
- Email addresses
- LinkedIn URLs
- Website URLs
- Logo URLs
- Raw association IDs
- Raw association names
- Completely empty fields
- Single-value fields
- Very high-cardinality identifiers

IDs should still be retained for joins and traceability.

---

### Potential Data Leakage

Some CRM fields may contain information created after the event being predicted.

Examples include:

- `Date entered Sales Qualified Lead`
- `Date entered Marketing Qualified Lead`
- `Last Contacted`
- `Last Activity Date`
- `Last Logged Call Date`
- lifecycle-stage timestamps
- potentially `Transcript Available`

These variables should only be included if they would actually be available at the time the prediction is made.

---

## 3. Exploratory Data Analysis

The initial EDA focuses on understanding which characteristics are associated with calls progressing beyond the two dominant call outcomes.

For the current analysis, calls with outcomes other than `CVM` and `GVM` are treated as calls that progressed beyond the two dominant voicemail-type outcomes.

These labels are currently inferred business categories and should be confirmed before being used as a final modeling target.

---

### Call Outcome Distribution

The call outcome distribution is highly concentrated.

| Outcome | Calls | Share |
| --- | ---: | ---: |
| CVM | 59,228 | 51.52% |
| GVM | 43,026 | 37.43% |

Together, CVM and GVM account for approximately:

```text
88.95% of all calls
```

This suggests that reaching prospects beyond voicemail-type outcomes is one of the largest bottlenecks in the current sales process.

---

### Repeated Calling Shows Diminishing Returns

The probability of reaching a non-CVM/GVM outcome decreases as additional calls are made to the same contact.

| Call Attempt | Non-CVM/GVM Rate |
| --- | ---: |
| 1st call | 15.0% |
| 2nd call | 11.7% |
| 3rd call | 9.7% |
| 4th call | 8.9% |
| 5th call | 8.8% |
| Calls 6–10 | 7.6% |
| 11+ calls | 8.0% |

The first attempt performs substantially better than later attempts.

This suggests that after approximately 3–5 unsuccessful calls, a different communication channel or contact within the company may be worth testing.

---

### Call Timing

Call performance varies by weekday.

| Day | Non-CVM/GVM Rate |
| --- | ---: |
| Monday | 10.1% |
| Tuesday | 10.0% |
| Wednesday | 10.8% |
| Thursday | 11.7% |
| Friday | 9.0% |

Thursday had the strongest observed performance, while Friday had the weakest.

Calls later in the day also generally outperformed very early calls.

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

This suggests that afternoon calling may be more effective than early-morning calling.

Timezone handling should be verified before converting this into a final operational recommendation.

---

## 4. Contact-Level Business Findings

### Management Level

| Management Level | Non-CVM/GVM Rate |
| --- | ---: |
| Manager | 20.2% |
| Director | 10.3% |
| C-Level | 10.2% |
| VP-Level | 8.3% |

Managers had the strongest observed performance among the major management-level groups.

---

### Department

Healthcare-related operational departments also performed well.

Examples include:

| Department | Non-CVM/GVM Rate |
| --- | ---: |
| Medical & Health | 17.7% |
| Operations | 12.3% |
| C-Suite | 10.0% |
| Finance | 9.7% |
| Information Technology | 8.2% |
| Marketing | 7.6% |
| Sales | 7.1% |

---

### Job Function

Examples of high-performing functions include:

| Job Function | Non-CVM/GVM Rate |
| --- | ---: |
| Medical Administration | 18.9% |
| Infrastructure | 15.0% |
| Accounting | 13.8% |
| Operations | 12.7% |
| Executive | 11.2% |

Healthcare and operational roles appear particularly promising.

---

### Job Title Classification

Some specific contact roles also showed higher rates.

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

This suggests that role-specific targeting may be more useful than simply targeting the highest-ranking executive.

---

## 5. Company-Level Business Findings

### Company Size

Mid-sized companies appear more reachable than very large enterprises.

| Employee Range | Non-CVM/GVM Rate |
| --- | ---: |
| 51–250 | 14.8% |
| 11–50 | 13.8% |
| 251–1,000 | 12.7% |
| 1–10 | 10.8% |
| 1,000–5,000 | 9.9% |
| 5,000–10,000 | 9.1% |
| 10,000–50,000 | 7.0% |

The 51–250 employee segment performs at more than twice the rate of the 10,000–50,000 employee segment.

---

### Industry

Industry is strongly associated with call outcomes.

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

### Target Segment

Existing CRM segmentation also contains useful signal.

| Target Segment | Non-CVM/GVM Rate |
| --- | ---: |
| Practice Groups | 14.1% |
| RCM Services | 12.5% |
| Venture Capital Invested | 12.3% |
| Unsegmented | 9.8% |

This suggests that the company's existing segmentation strategy already identifies prospect groups with different levels of responsiveness.

---

## 6. Sales Representative Analysis

Raw call outcome rates vary substantially between sales representatives.

However, these results should not yet be interpreted directly as salesperson performance.

Different representatives may receive different:

- industries
- lead quality
- territories
- company sizes
- target segments
- campaigns
- time periods

The next modeling stage should control for these factors before estimating salesperson effects.

---

## 7. Current Business Findings

The analysis so far suggests several potentially actionable patterns.

### Prospect Targeting

Priority may be worth shifting toward:

- healthcare organizations
- RCM-related companies
- practice groups
- mid-sized companies
- managers
- clinical directors
- revenue-cycle personnel
- healthcare operations roles

### Calling Strategy

The current data suggests testing:

- increased calling on Wednesday and Thursday
- increased calling during afternoon hours
- reduced reliance on very early-morning calling
- changing strategy after approximately 3–5 unsuccessful attempts

Alternative follow-up strategies could include:

- email
- LinkedIn outreach
- calling another contact at the same organization

### Sales Performance

Large differences exist between representatives, but lead quality must be controlled before drawing performance conclusions.

---

## 8. Limitations

The current findings are exploratory and represent associations rather than proven causal effects.

For example:

```text
Thursday calls → higher engagement
```

does not automatically mean:

```text
Calling on Thursday causes higher engagement
```

Thursday may contain:

- different sales representatives
- different lead segments
- different campaigns
- different prospect industries

The same issue applies to company size, contact role, and other variables.

The next stage therefore needs to control for multiple variables simultaneously.

---

## 9. Next Step: Predictive Modeling

The next phase is to build a baseline classification model that estimates the probability that a call progresses beyond the dominant `CVM` and `GVM` outcomes.

Potential predictors include:

- Industry
- Company size
- Target segment
- Department
- Management level
- Job title
- Previous call attempts
- Day of week
- Time of day
- Sales representative

The first model should be an interpretable baseline such as **Logistic Regression**.

This will help determine whether patterns discovered during EDA remain important after controlling for the other variables.

More complex models such as Random Forest or gradient-boosted trees can then be compared against the baseline.

---

## Current Project Status

```text
[✓] Data Understanding
[✓] Data Quality Analysis
[✓] Data Preprocessing Strategy
[✓] Exploratory Data Analysis
[✓] Initial Business Findings
[ ] Define Final Modeling Target
[ ] Feature Engineering
[ ] Baseline Model
[ ] Model Evaluation
[ ] Model Comparison
[ ] Final Recommendations
```
