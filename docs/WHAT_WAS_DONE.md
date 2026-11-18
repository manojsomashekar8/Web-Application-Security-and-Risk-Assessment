# What has been done

This is a short summary of the project so far, written for someone new to it.

## The goal

Scan websites that have known security holes, then rank the problems by how risky they are for a business. The ranking is explained in plain words so a person can understand why each problem is at the top or bottom.

## What works

1. **Scanning.** The OWASP ZAP scanner visits a website and runs attack checks. It logs in to the practice sites first, so it can see the pages behind the login.
2. **Cleaning up.** The scanner's output is put into one common format. Each problem is linked to a standard category (CWE and OWASP Top 10).
3. **Adding facts.** Problems with a known CVE number get severity and exploit data from saved copies of public lists.
4. **Scoring.** Each problem gets a risk score from 0 to 100. The score depends on severity, exploitability and how important the website is to the business. See [SCORING.md](SCORING.md).
5. **Web app.** You can add targets, start scans, and view ranked findings in a browser. A login protects it.
6. **Dashboards.** Grafana shows charts from the monitoring data and from the database.
7. **Tests.** Automatic tests check the clean-up and scoring code. Browser tests check the web app and Grafana.
8. **Experiments.** Five experiments compare the scoring methods, using saved scan results.

## Results so far

| Website | Pages reached | Alerts | Known problems found |
|---|---|---|---|
| DVWA | 71 | 775 | 2 out of 7 types |
| bWAPP | 94 | 609 | 1 out of 8 types |
| WebGoat | 2 | 26 | 0 out of 7 types (scan barely reached the site) |

Details and what the numbers mean are in [RESULTS.md](RESULTS.md).

## Known problems

- **WebGoat was barely scanned.** It is a single-page app, and the scanner could not find its lessons. See [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md).
- **Most alerts are minor.** Many findings are missing security headers, not serious problems, so precision is low.
- **One run per site.** We have not repeated scans, so we don't know how much results vary.
- **Juice Shop timing is not recorded.** The full scan is slow, and we haven't measured it yet.
- **Commits are not pushed to GitHub.** The account on this machine cannot write to the repository. The commits are saved locally.
- **Some docs are still missing.** `TEST_PLAN.md`, `UI.md`, `LITERATURE.md` and `REPRODUCIBILITY.md` have not been written.

## Where to go next

- To start the project, read [HOW_TO_START.md](HOW_TO_START.md).
- To see what is planned, read [PLAN.md](PLAN.md).
- To see the open decisions, read [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md).
