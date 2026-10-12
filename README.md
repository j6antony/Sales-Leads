# Sales Data Initial Analysis Findings
The three datasets join cleanly after ID normalization: 0 invalid Call→Contact, Call→Company, or Contact→Company relationships after cleaning.
The raw HubSpot export is very bloated: Companies, Contacts, and Calls contain many fields that are 90–100% empty, so a large amount of CRM metadata can be discarded.
The important call variables are actually well populated. Call direction, Call duration, Call status, Activity date, and several others have essentially no missing data; Call outcome is missing in only about 0.73% of records.
Missingness is not random. Contact and company information is more complete for some call outcomes than others, which means CRM enrichment itself may contain useful signal.
The Call outcome variable is extremely imbalanced. CVM accounts for 51.52% of calls and GVM another 37.43%. Together they're about 89% of all 114,965 calls.
## Conclusion
Data preparation and quality assessment found that the CRM data is sufficiently complete and relationally consistent for modeling. The dominant preliminary sales finding is that approximately 89% of recorded calls fall into the two dominant CVM/GVM outcome categories, suggesting that voicemail/non-engagement represents the largest bottleneck in the current calling process. The next analysis should therefore identify which contact, company, timing, and outreach factors increase the likelihood of meaningful engagement.
#
