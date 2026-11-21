# What has been done

A plain-language summary of the project so far. For the full walkthrough, read [EXPLAIN.md](../EXPLAIN.md).

## The goal

Scan websites that have known security holes, then rank the problems by how risky they are for a business. Every ranking comes with a plain-language explanation.

## What works

1. **Scanning.** The OWASP ZAP scanner visits a website and runs attack checks. It logs in to the practice sites first.
2. **Clean-up.** Each scanner alert becomes one common format, linked to a standard category (CWE and OWASP Top 10).
3. **Classification.** Each alert is labelled as a vulnerability, a potential issue, an informational note, or excluded. Scanner alerts are not treated as proven exploits.
4. **Grouping.** Repeated alerts on the same page and parameter become one finding. The raw count is kept.
5. **Enrichment.** Findings with a CVE number get severity and exploit data from saved public lists. Missing data shows as "n/a".
6. **Scoring.** Each finding gets a risk score from 0 to 100 and a High, Medium or Low label. The explanation shows the arithmetic and the main limiting factor. See [SCORING.md](SCORING.md).
7. **Rankings.** Four methods rank the findings, each from its own score. Ties share a deterministic order.
8. **React web app** on port 8081. Add targets, start scans, see results with summary cards, filters and explanations.
9. **Dashboards.** Grafana dashboards are loaded automatically at startup. They show scan status, risk, classification and raw versus unique counts.
10. **Tests.** Automatic tests cover the clean-up, scoring, rankings, grouping and context sensitivity. Browser tests cover the React app, the original pages and Grafana.
11. **Experiments.** Five experiments compare the scoring methods on saved scan results.

## Results so far

| Website | Pages reached | Alerts | Known problem types found |
|---|---|---|---|
| DVWA | 71 | 775 | 2 out of 7 |
| bWAPP | 94 | 609 | 1 out of 8 |
| Juice Shop | see results | 731 | 2 out of 6 |
| WebGoat | 2 | 26 | 0 out of 7 (scan barely reached the site) |

These counts are alerts from the scanner. Detection numbers are low because most alerts are minor (missing headers, for example). Details are in [RESULTS.md](RESULTS.md).

## Known problems

- **WebGoat was barely scanned.** It is a single-page app and the scanner could not reach its lessons.
- **Most alerts are minor.** Precision is low, as expected for a web scanner.
- **One run per site.** Results have not been repeated, so we don't know how much they vary.
- **Juice Shop scan time is not recorded.**
- **Scan 1 predates grouping.** Its repeated alerts were not merged.
- **Enrichment provenance is not recorded yet.** A missing feed file would fail the scan rather than leave values as "n/a".
- **Commits are not all pushed to GitHub.** The account on this machine cannot write to the repository.
- **Some docs are still missing:** `TEST_PLAN.md`, `UI.md`, `LITERATURE.md` and `REPRODUCIBILITY.md`.

## Where to go next

- To understand how everything works: [EXPLAIN.md](../EXPLAIN.md)
- To start the project: [HOW_TO_START.md](HOW_TO_START.md)
- To see what is planned: [PLAN.md](PLAN.md)
- To see the open decisions: [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md)
