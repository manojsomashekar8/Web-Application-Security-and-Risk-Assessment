# Literature and standards

These are the sources behind the choices in this project. The list was written from memory and has **not been checked online for this version**. Before citing any of it in a report, look up the current edition and add the DOI or URL.

## Standards and data sources used by the project

| Source | Used for | Where in the project |
|---|---|---|
| OWASP Top 10 (2021 edition) | Category labels for each finding | `src/normalize/normalize.py` (CWE to OWASP mapping) |
| MITRE CWE (Common Weakness Enumeration) | Weakness IDs that ZAP reports | `src/normalize/normalize.py` |
| FIRST, CVSS v3.1 specification | Severity score (S) when a CVE has a CVSS value | `src/enrich/enrich.py`, `src/scoring/score.py` |
| FIRST, EPSS (Exploit Prediction Scoring System) | Estimated chance of exploitation (E) | `data/feeds/epss.csv` |
| CISA Known Exploited Vulnerabilities (KEV) catalog | Exploited-in-the-wild flag (E = 1.0) | `data/feeds/kev.json` |
| NIST NVD | CVSS values for the CVEs in the subset | `data/feeds/nvd_subset.json` |
| OWASP ZAP (Zed Attack Proxy) | The scanner | `docker-compose.yml`, `src/collectors/` |

## Academic background

- Jacobs, J., Romanosky, S., Adjerid, I., Baker, W. (2020). *Improving vulnerability remediation through better exploit prediction.* Journal of Cybersecurity. Basis for using EPSS as an exploitation estimate.
- Allodi, L., Massacci, F. (2014). *Comparing vulnerability severity and exploits using case-control studies.* ACM Transactions on Information and System Security. Argues that CVSS severity alone is a weak predictor of exploitation.
- Kendall, M. G. (1938). *A new measure of rank correlation.* Biometrika. Basis for the tau comparison of rankings (`src/scoring/compare.py`).
- Järvelin, K., Kekäläinen, J. (2002). *Cumulated gain-based evaluation of IR techniques.* ACM Transactions on Information Systems. Background for NDCG@K, which the review lists as a metric; not implemented yet.

## Position of this project

Context-aware prioritization is not new by itself. The contribution here is a transparent, explained score, checked against simpler baselines (CVSS only, ZAP risk only, weighted sum), with its inputs and arithmetic shown to the user. The project does not claim novelty beyond that.
