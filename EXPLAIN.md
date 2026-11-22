# EXPLAIN: how this project works

This document explains the whole project in plain language, for someone new to web security and to this code. Each section says what a part does, why it exists, and where it lives. Numbers quoted here are from the stored results; docs/RESULTS.md has the full tables.

---

## 1. The problem

A web scanner finds many warnings about a website. Most tools rank them by a generic severity number that ignores where the site is, what data it holds, and who can reach it. A warning that is harmless on a test site can be urgent on a public payment site.

This project asks: **can we rank warnings by how risky they are for a specific business, and explain every ranking in words?** The answer is a transparent score, checked against simpler baselines and tested with controlled experiments.

It is a prototype. It has been checked on deliberately vulnerable practice websites (DVWA is the main one; Juice Shop, WebGoat and bWAPP were used for validation). It has not been tested on real production systems, and a few scans cannot prove the model works.

---

## 2. The big picture

```
   You (browser)                                   Dashboards
       |                                               ^
       v                                               |
  [ React app ]  --/api-->  [ FastAPI backend ] --metrics--> [ Prometheus ] --> [ Grafana ]
   nginx, port 80             port 8080 (host)        |                              ^
                                      |                  |                              |
                                      v                  v                              |
                                [ ZAP scanner ]    [ PostgreSQL ] <--- read-only role -+
                                      |
                                      v
                            [ practice websites ]
                      DVWA (default), Juice Shop, WebGoat, bWAPP
```

1. You use the **React app** to pick a website, choose a scan profile, and start a scan.
2. The app talks to the **backend** through `/api`. The backend is the only part that starts scans.
3. The backend tells **ZAP** (an open-source scanner) to visit the site and collect warnings.
4. The backend cleans, classifies, enriches, scores and ranks the warnings, and saves them in **PostgreSQL**.
5. **Prometheus** reads numbers from the backend, and **Grafana** draws charts from Prometheus and the database. Grafana can only read.

Every published port is bound to `127.0.0.1` (your own computer). The React app is on port 80, the original pages on 8080, Grafana on 3001, ZAP's API on 8090.

---

## 3. Folder map

| Folder or file | What it is for |
|---|---|
| `frontend/` | The React app (Vite build, served by nginx in its own container) |
| `src/api/` | The JSON API, login check, scan requests, downloads, import and export endpoints |
| `src/web/` | The original server-rendered pages (port 8080) |
| `src/collectors/` | Everything that talks to ZAP and logs into the practice sites |
| `src/scanprofile.py` | Scan profiles and custom settings, with server-side bounds |
| `src/normalize/` | Turns ZAP's raw alerts into one common shape |
| `src/triage.py` | Classifies alerts and merges repeated ones |
| `src/enrich/` | Adds CVE severity, EPSS and KEV data from saved public lists, with provenance |
| `src/scoring/` | The risk formula, the explanation text and the comparison scores |
| `src/pipeline.py` | Runs the steps above in order |
| `src/service.py` | Rules: allowlist check, targets, scans, re-score, export and import |
| `src/report/` | Per-finding reports (HTML and JSON) and the full-scan HTML page |
| `src/importexport.py` | The versioned export and import format (`wasra-scan`, version 1) |
| `src/health.py` | Health checks for Postgres, ZAP and feed freshness |
| `src/metrics/` | Numbers that Prometheus reads |
| `src/experiments/` | Experiments 1 to 7, each written as JSON and CSV |
| `db/migrations/` | Database tables, applied in order at startup (001 to 011) |
| `configs/` | Editable settings: score weights, scan profiles, validation threshold, resource limits, CVE mapping |
| `data/feeds/` | Saved copies of public data (EPSS, KEV, an NVD subset) and a manifest with the snapshot date |
| `grafana/` | Dashboards and alert rules, loaded automatically |
| `scripts/` | Export and import scripts, the usage sampler, the port check, the reproducibility report |
| `tests/` | Automatic checks (unit, integration, browser) |
| `results/` | Raw scan outputs, experiment results, ZAP reports and exports |
| `docs/` | Design documents |

---

## 4. Scan profiles and what happens during a scan

You choose a profile on the target page:

| Profile | What it does | DVWA time (measured) |
|---|---|---|
| **quick** | Traditional spider with a 2-minute cap, passive checks only, no attacks | 7 s |
| **standard** | Traditional and AJAX spider, active scan at Low strength, time limits | 3 min 18 s |
| **deep** | The reference scan: both spiders, active scan at ZAP's default strength, no limits | 8 min 21 s (12 min 12 s in the final reproduce run) |
| **custom** | Your own settings, checked by the server (INSANE strength is not offered) | depends on settings |

Each scan stores the exact settings it used, and the scan page shows them with the time each stage took.

```
you click "Start scan"
  -> the backend checks the site is on the allowlist (docs/TARGETS.md)
  -> checks free memory: refuses below 14 GB (ZAP needs about 12.8 GB at peak)
  -> for DVWA, WebGoat and bWAPP: log in; for DVWA, first reset its database and set security low
  -> ZAP starts a fresh session and installs the session cookie
  -> applies the profile's settings to ZAP (time limits, strength, threads, delay, excluded URLs)
  -> spider and AJAX spider (as the profile says)
  -> passive checks finish
  -> active scan (if the profile has one)
  -> the backend downloads the alerts and stores them
  -> normalize -> triage -> enrich -> score -> rank
  -> save the findings, the settings, the timings and the ZAP HTML report
  -> the scan is marked "done"
```

Only one scan runs at a time. A second request waits in a queue. A scan that was running when the backend stopped is marked `failed` ("interrupted") at the next startup.

**Why several spiders?** The normal spider cannot see pages that load through JavaScript. The AJAX spider drives a browser to find those pages, so the active scan can test them too. The Client Spider, which ZAP now recommends, is not active in the installed ZAP image, so we use the AJAX spider (decision D52).

**Why ports are stripped from URLs?** ZAP stores `http://dvwa:80` as `http://dvwa`. The alert lookup used the port, so it found only the front page until this was fixed (decision D21).

**DVWA is reset before every scan** (`src/collectors/auth.py`). DVWA's own "Create / Reset Database" runs, the security cookie is set to low, and so the next scan never starts from a state an earlier scan changed.

---

## 5. From raw alerts to a ranked list

### Step A: Normalize (`src/normalize/normalize.py`)

ZAP reports each alert with a name, a risk level (High, Medium, Low, Informational), a confidence (High, Medium, Low, False Positive), and sometimes a CWE number. The normalizer converts these to one shape and maps each CWE to an OWASP Top 10 category.

| ZAP risk | Number used by the score |
|---|---|
| High | 0.8 |
| Medium | 0.5 |
| Low | 0.2 |
| Informational | 0.1 |

Confidence becomes a number too: High 0.9, Medium 0.6, Low 0.3, False Positive 0.0.

### Step B: Triage (`src/triage.py`)

**Classification.** ZAP does not prove that an issue can be exploited, so each alert gets a label:

| Label | Rule | Meaning |
|---|---|---|
| `vulnerability` | Everything else | The scanner reports it. Not proven exploitable. |
| `potential` | Confidence Low | Might be real. Needs a manual check. |
| `informational` | ZAP risk Informational | A note, such as a missing header. Not a vulnerability. |
| `excluded` | Confidence False Positive | ZAP thinks it is wrong. |

**Grouping.** The same check can fire many times on one page with different test values. A fingerprint is the plugin ID, the URL path (without the query), the parameter and the attack string. Alerts with the same fingerprint become one finding, and the raw count is kept. On Juice Shop 1,103 raw alerts became 493 unique findings; on DVWA 775 became 544 (docs/RESULTS.md).

### Step C: Enrich (`src/enrich/enrich.py`)

Findings with a CVE number (a public ID for a known problem) can get three values from saved public lists:

- **CVSS**: severity from 0 to 10 (NVD subset in `data/feeds/`).
- **EPSS**: estimated chance of exploitation in the next 30 days (`epss.csv`).
- **KEV**: whether CISA lists it as actively exploited (`kev.json`).

Only findings with an explicit CVE mapping in `configs/cve_map.json` get them. **That file is currently empty**, so no ZAP finding gets a CVE, and CVSS, EPSS and KEV show as **n/a** for every finding. We do not invent values. The reason is shown as a tooltip on each n/a.

**Provenance.** Each value records its feed name, file, snapshot date (from `data/feeds/manifest.json`) and status (`ok`, `no_cve`, `not_in_feed` or `unavailable`).

**Resilience.** A missing, unreadable or wrong-format feed file logs a warning, sets its values to n/a, and the scan continues.

### Step D: Score (`src/scoring/score.py`)

- **S, severity (0 to 1):** CVSS / 10 if there is a CVE, otherwise the ZAP risk number.
- **E, exploitability (0 to 1):** 1.0 if on the KEV list, otherwise EPSS if known, otherwise the ZAP confidence number.
- **Context:** the four business ratings, Low 0.33, Medium 0.66, High 1.0: criticality, data sensitivity, business impact, internet exposure.

```
Impact     I = S x average(criticality, data sensitivity, business impact)
Likelihood L = E x internet exposure
Risk score   = 100 x L x I          (always between 0 and 100)
```

**Why multiply?** A problem needs both a serious flaw and a realistic way in to matter. If either is near zero, the risk is near zero.

### Step E: Label

| Score | Label |
|---|---|
| 60 and above | High |
| 30 to 59.9 | Medium |
| below 30 | Low |

### Step F: Explain (`src/scoring/score.py`, `explain`)

The explanation is built from the same numbers as the score:

> Risk 45.0 (Medium). Thresholds: High 60+, Medium 30 to 59.9, Low below 30. Likelihood 0.90 = exploitability 0.90 (ZAP confidence High) x internet exposure 1.00 (High). Impact 0.50 = severity 0.50 (ZAP risk Medium) x mean of criticality High, data sensitivity High, business impact High. Main limit: severity 0.50.

It answers the question a reviewer asks: "the context is High, so why is the score low?" The answer is the main limit. A test checks that the label always matches the number printed with it.

### Step G: Rank (`src/pipeline.py`)

Four methods rank the findings, each from its own score: `risk` (the framework score, the main result), `weighted_sum` (a simple weighted average), `cvss_only` and `zap_risk_only`. Ties are broken by plugin ID and URL, so repeated runs give the same order. Each scan also stores its **top-10 overlap** between the framework ranking and the CVSS-only ranking.

**Why are the rankings often the same?** In one scan most findings share the same ZAP risk and confidence, so the methods agree. They differ only when findings differ in CVE data, KEV status or ZAP risk. Tests in `tests/test_ranking_methods.py` show both cases.

---

## 6. Re-score, export and import

- **Re-score** recomputes every finding of a scan from its stored raw alerts, using the target's current business ratings. No new scan starts. Scans from before raw alerts were stored cannot be re-scored; the page says so.
- **Export** writes one finished scan as a versioned JSON file (`format` `wasra-scan`, `format_version` 1), with the target, the settings, the stage timings and the raw alerts. `scripts/export_scan.py SCAN_ID` writes it to `results/exports/`.
- **Import** (`scripts/import_scan.py FILE` or the API) checks the format version, the size (25 MB), and every field. Unknown versions, corrupt files and malformed alerts are refused with a message. Scores are **recomputed** from the raw alerts, never trusted from the file. The imported target must still be on the allowlist, and importing never starts a scan. Importing the same file twice is refused as a duplicate.

---

## 7. Downloads and reports

| What | Made by | Where |
|---|---|---|
| **ZAP report (HTML)** | ZAP itself (its `traditional-html` template), when the scan finishes | Scan page header. Covers the whole scan |
| Full report (HTML and JSON) | Our backend | Scan page header |
| Findings table (CSV) | Our backend. Cells starting with `= + - @` are quoted so spreadsheets do not run them | Scan page header |
| Per-finding report (HTML and JSON) | Our backend: name, description, solution, references, URL, parameter, attack, evidence, CWE, OWASP, ZAP risk and confidence, the grouped count, CVSS/EPSS/KEV or n/a with the reason, every score factor, the explanation, the context ratings, and the rank under each method | "Report" column of each finding row |

ZAP's report is generated for the scan's session, so it cannot be made for one finding; that is why per-finding reports come from our backend. All scanner text is escaped in HTML, and a test checks that `<script>` in the evidence comes out escaped.

---

## 8. The web app (React)

Four screens at `frontend/`:

| Screen | Route | What you do |
|---|---|---|
| Targets | `/` | See each target and its latest scan, and the system status (Postgres, ZAP, feed age; older than 30 days is stale) |
| Add target | `/targets/new` | Pick a site from the allowlist and rate its business context |
| Target | `/targets/:id` | Choose a profile (or custom settings), start a scan, open the latest results |
| Scan results | `/scans/:id` | Settings and stage timings, summary, classification, filters, sortable table, downloads, and an expandable explanation per finding |

The results table sorts by any column (default: framework risk, highest first; ties keep the stored order). Missing values show as "n/a" with a tooltip giving the reason. Scanner text is never shown as HTML.

If the app runs in `AUTH_MODE=basic`, it shows a login form and keeps the credentials in memory only.

---

## 9. Dashboards (Grafana)

Dashboards load from `grafana/provisioning/` at startup, so nothing is set up by hand.

- **WASRA overview**: a `target` filter; scans by status; findings by ZAP risk; average framework risk per target; findings by classification; raw alerts vs unique findings; findings by framework band; scan duration per stage; findings with n/a enrichment; top-10 overlap; and CPU and memory of ZAP and the backend during the latest scan.
- **WASRA validation**: the latest run per target by default, with a run-date selector. The results table shows known types, detected types, matching alerts, total alerts, precision, recall and run time. Where a run reached fewer than 10 pages, precision and recall say **"Coverage too low"** instead of a number, never 0. A note explains that most ZAP alerts are informational, so alert-level precision is low. Recall by category is shown too.
- **WASRA ranking stability**: top 10 by framework risk, with the four rankings side by side.

Prometheus reads `/metrics` from the backend on every scrape, computed from the database. Grafana reads through a **read-only** role.

---

## 10. Validation and experiments

Seven experiments (`make experiments`), each written as JSON and CSV in `results/experiments/`:

1. **Detection**: known vulnerability types found per target, precision and recall.
2. **Ranking**: agreement between rankings (Kendall tau, top-k overlap).
3. **Context sensitivity**: changing one business factor moves the framework score, not the CVSS-only ranking.
4. **Weights**: how stable the weighted-sum ranking is when weights change.
5. **Ablation**: what happens when one factor is removed.
6. **Deduplication**: raw alerts against unique findings, per target.
7. **Categories**: detection per vulnerability category.

Precision = matching alerts / total alerts. Recall = known types detected / known types. A run that reaches fewer than 10 pages (ZAP's site tree after the spiders) shows **"Coverage too low"**, never 0.

**The validation matrix** (WebGoat and bWAPP, each with quick, standard and deep, one run each) is saved in the repository: `results/validation/`, with the table in [docs/RESULTS.md](docs/RESULTS.md). The main points:

- bWAPP: quick takes 17 s, standard 5 min 48 s, deep 14 min 9 s. Quick finds 170 unique findings, standard and deep about 380. All three detect 1 of 8 known types. Standard's top 10 matches deep's (10 of 10).
- WebGoat: all three profiles finish in under 5 minutes and reach 1 URL, so its results show "Coverage too low". The fixed AJAX browser runs but adds no pages.
- Plugin 10003 (the Retire.js library check) did not fire in any of the six runs, so no CVSS, EPSS or KEV value is available for these targets. That is correct for them, not missing data.

**A bug found during the matrix.** The alert lookup asked ZAP for alerts with the default port (`http://bwapp:80`). ZAP stores that host without the port, so only start-page alerts came back. The fix is in the shared client (decision D71). Earlier bWAPP and DVWA runs made through the API are superseded where listed in docs/OPEN_QUESTIONS.md.

**Load the matrix into a fresh install:** `make load-validation` (see docs/HOW_TO_START.md).

Results are summarised in [docs/RESULTS.md](docs/RESULTS.md). Current limits:

- One run per profile and target. No variance.
- Local lab applications only (WebGoat and bWAPP, inside the Docker network).
- Most ZAP web findings have no CVE, so the framework's advantage over the baselines comes mostly from context.
- Precision is low because most alerts are informational (missing headers and similar).

## 11. Safety rules

- **Allowlist in both auth modes.** A URL not in `docs/TARGETS.md` is refused by the server.
- **Local only.** Every published port is bound to `127.0.0.1`. `make up` refuses to start in `AUTH_MODE=none` if any port is bound elsewhere (`scripts/check_bindings.py`, tested).
- **AUTH_MODE.** `none` (the default) skips the login. `basic` adds one: a constant-time credential check, and the app keeps the credentials in memory only.
- **Scan requests are validated** against fixed bounds (`src/scanprofile.py`). Unknown fields are refused. The frontend never sends raw ZAP calls.
- **Memory check** before a scan: refused below 14 GB free.
- **Secrets.** `.env` is never committed. `make env` generates random passwords.
- **Practice-site logins** are the apps' public defaults, used only inside the Docker network.
- **Read-only dashboards.** Grafana cannot write.

---

## 12. Running it

```
./install.sh             # fresh Ubuntu 22.04 or 24.04: installs what is missing, creates .env, starts everything
make up                  # start the stack (if it is installed already)
make scan-dvwa           # the default demo scan (about 8 minutes, deep)
make test                # offline tests; with the stack up: WASRA_INTEGRATION=1 WASRA_E2E=1 make test
make experiments         # rebuild the experiment tables
make reproduce           # full clean run (deletes the database; back it up first)
make down                # stop everything
```

Then open http://127.0.0.1 (the app), http://127.0.0.1:3001 (Grafana), or http://127.0.0.1:8080 (the original pages).

---

## 13. Known limits and what is next

| Limit | What would fix it |
|---|---|
| `configs/cve_map.json` is empty, so CVSS, EPSS and KEV are n/a for every finding | Build a reviewed mapping from ZAP plugin IDs to CVEs |
| The Client Spider is not active in the installed ZAP image | Confirm the Client Side Integration add-on loads, then compare it with the AJAX spider |
| ZAP's report is per scan, not per finding | A per-finding ZAP report is not possible with this ZAP design |
| Each validation target scanned once | Repeated runs, with variation reported |
| WebGoat reaches 1 URL in every profile, even with the fixed AJAX browser | Read ZAP's AJAX result list directly, or seed WebGoat's lesson routes; until then WebGoat is reported as "Coverage too low" |
| Scans made before raw-alert storage cannot be re-scored or exported | Re-run them |
| Earlier DVWA and bWAPP API scans returned start-page alerts only (alert lookup bug, fixed in D71) | Re-run the affected DVWA scans with approval; their plugin 10003 conclusions are unverified |
| Memory: ZAP needs about 12.8 GB at peak; a container cap of 8 GB made scans fail | Measured limits are recorded in docs/REPRODUCIBILITY.md; no cap is set |
| The browser test for downloads and the export/import round trip depend on a finished scan existing | Keep one scan in the reproduce run |
| Literature list was written from memory | Verify each source and add DOIs before citing it (docs/LITERATURE.md) |

Decisions are in [docs/DECISIONS.md](docs/DECISIONS.md). Open questions, with the default used for each, are in [docs/OPEN_QUESTIONS.md](docs/OPEN_QUESTIONS.md).
