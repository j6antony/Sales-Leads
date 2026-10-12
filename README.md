# Sales Data Initial Understanding and Quality analysis
The three datasets join cleanly after ID normalization: 0 invalid Call→Contact, Call→Company, or Contact→Company relationships after cleaning.
The raw HubSpot export is very bloated: Companies, Contacts, and Calls contain many fields that are 90–100% empty, so a large amount of CRM metadata can be discarded.
The important call variables are actually well populated. Call direction, Call duration, Call status, Activity date, and several others have essentially no missing data; Call outcome is missing in only about 0.73% of records.
Missingness is not random. Contact and company information is more complete for some call outcomes than others, which means CRM enrichment itself may contain useful signal.
The Call outcome variable is extremely imbalanced. CVM accounts for 51.52% of calls and GVM another 37.43%. Together they're about 89% of all 114,965 calls.
## Conclusion
Data preparation and quality assessment found that the CRM data is sufficiently complete and relationally consistent for modeling. The dominant preliminary sales finding is that approximately 89% of recorded calls fall into the two dominant CVM/GVM outcome categories, suggesting that voicemail/non-engagement represents the largest bottleneck in the current calling process. The next analysis should therefore identify which contact, company, timing, and outreach factors increase the likelihood of meaningful engagement.
## Exploratory Data Analysis & Business Findings

After validating and preprocessing the CRM data, exploratory analysis was performed to identify patterns associated with better sales-call outcomes.

For the initial analysis, calls with outcomes other than `CVM` and `GVM` were treated as calls that progressed beyond the two dominant voicemail-type outcomes. These internal outcome abbreviations should be confirmed with the business before using them as a final modeling target.

### Key  From Exploratory Data Analysis

#### 1. Repeated Calling Shows Diminishing Returns

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

This suggests that repeated calling produces diminishing returns. After approximately 3–5 unsuccessful attempts, switching communication channels or targeting another contact within the company may be more effective.

#### 2. Call Timing Appears to Influence Outcomes

Thursday produced the highest non-CVM/GVM rate at approximately **11.7%**, while Friday had the lowest at approximately **9.0%**.

Calls made later in the day also generally performed better than early-morning calls. Calls between approximately **12 PM and 6 PM** showed stronger outcomes, with the best observed rates occurring during the afternoon.

This suggests that call scheduling may be an actionable area for optimization.

#### 3. Contact Role Is Associated With Call Performance

Contacts identified as **Managers** had a non-CVM/GVM rate of approximately **20.2%**, compared with:

- Directors: **10.3%**
- C-Level: **10.2%**
- VP-Level: **8.3%**

Department and job-function analysis also showed stronger results for healthcare-related operational roles.

Examples include:

- Medical & Health department: **17.7%**
- Medical Administration job function: **18.9%**
- Clinical Director: **20.8%**
- Director – Revenue Cycle Management: **14.2%**
- Manager – Operations: **14.0%**

This suggests that targeting the appropriate operational decision-makers may be more effective than relying only on seniority.

#### 4. Mid-Sized Companies Appear More Reachable

Companies with approximately **51–250 employees** produced the highest observed non-CVM/GVM rate at **14.8%**.

Larger enterprises generally showed lower rates, including approximately **7.0%** for companies with 10,000–50,000 employees.

This suggests that SMB and mid-market organizations may be more responsive to outbound calling than very large enterprises.

#### 5. Industry Segmentation Matters

Industry showed substantial variation in call outcomes.

| Industry | Non-CVM/GVM Rate |
| --- | ---: |
| Hospital & Health Care | 12.2% |
| Oil & Energy | 13.1% |
| Retail | 8.6% |
| Financial Services | 8.8% |
| Manufacturing | 5.6% |

Healthcare calls were more than twice as likely as manufacturing calls to result in outcomes outside CVM/GVM.

This indicates that industry should be considered as an important prospect-selection feature.

#### 6. Existing Target Segments Show Useful Signal

Current CRM segmentation also showed differences in performance.

| Target Segment | Non-CVM/GVM Rate |
| --- | ---: |
| Practice Groups | 14.1% |
| RCM Services | 12.5% |
| Venture Capital Invested | 12.3% |
| Unsegmented prospects | 9.8% |

This suggests that existing target-segment definitions contain useful sales information and may be valuable model features.

#### 7. Sales Representative Results Vary Significantly

Large differences were observed between sales representatives' raw non-CVM/GVM rates.

However, these differences should **not yet be interpreted directly as salesperson performance**, since each representative may receive different industries, lead quality, company sizes, campaigns, or territories.

A multivariate analysis is required before separating salesperson effects from lead-assignment effects.

### Preliminary Business Recommendations

Based on the initial exploratory analysis:

- Prioritize healthcare, RCM, practice-group, and similar high-performing segments.
- Consider targeting operational decision-makers such as managers, clinical directors, and revenue-cycle personnel.
- Test shifting more calling activity toward Wednesday and Thursday afternoons.
- Reconsider repeatedly calling the same contact after approximately 3–5 unsuccessful attempts.
- Consider switching to email, LinkedIn, or another contact within the same organization after repeated unsuccessful calls.
- Investigate sales-representative performance while controlling for differences in lead quality and assigned prospect segments.

### Next Step

The relationships identified through exploratory analysis are correlations and should not yet be interpreted as causal effects.

The next stage is multivariate modeling to determine which variables remain predictive after controlling for other factors such as:

- Industry
- Company size
- Contact seniority
- Department
- Call timing
- Previous call attempts
- Sales representative
- Target segment

A baseline logistic classification model can then be used to estimate the probability that a call progresses beyond the dominant CVM/GVM outcomes.
