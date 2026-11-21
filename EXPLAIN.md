# EXPLAIN: how this project works

This document explains the whole project in plain language. It is written for someone who is new to web security and to this codebase. Each section says what a part does, why it exists, and where it lives.

---

## 1. The problem in one paragraph

A web scanner finds many warnings about a website. Most tools rank those warnings by a generic severity number. That number ignores where the site is, what data it holds, and who can reach it. A warning that is harmless on a test site can be urgent on a public payment site.

This project asks: **can we rank warnings by how risky they are for a specific business, and explain every ranking in words?** The answer is a transparent scoring model, checked against simpler baselines and tested with controlled experiments.

The project is a prototype. It has been checked on three deliberately vulnerable practice websites. It has not been validated on real production systems, and one scan is not enough to prove the model works.

---

## 2. The big picture

```
   You (browser)                                   Dashboards
       |                                               ^
       v                                               |
  [ React frontend ]  --/api-->  [ FastAPI backend ] --metrics--> [ Prometheus ] --> [ Grafana ]
   nginx, port 8081               port 8080 (host)        |                              ^
                                        |                  |                              |
                                        v                  v                              |
                                  [ ZAP scanner ]    [ PostgreSQL ] <--- read-only role -+
                                        |
                                        v
                              [ practice websites ]
                         Juice Shop, DVWA, WebGoat, bWAPP
```

Read it from top left to bottom right:

1. You use the **React frontend** to pick a website and start a scan.
2. The frontend talks to the **backend** through `/api`. The backend is the only part that starts scans.
3. The backend tells **ZAP** (an open-source scanner) to visit the website and collect warnings.
4. The backend cleans, enriches, scores and ranks the warnings, then saves them in **PostgreSQL**.
5. **Prometheus** reads numbers from the backend. **Grafana** draws charts from Prometheus and from the database. Grafana can only read.

Everything listens on `127.0.0.1` (your own computer). Nothing is exposed to the network.

---

## 3. Folder map

| Folder or file | What it is for |
|---|---|
| `frontend/` | The React web interface (built with Vite, served by nginx) |
| `src/api/` | The JSON API and login check |
| `src/web/` | The older server-rendered pages (still available on port 8080) |
| `src/collectors/` | Everything that talks to ZAP and logs into the practice sites |
| `src/normalize/` | Turns ZAP's raw alerts into one common shape |
| `src/triage.py` | Classifies alerts and merges repeated ones |
| `src/enrich/` | Adds CVE severity, EPSS and KEV data from saved copies of public lists |
| `src/scoring/` | The risk formula, the explanation text and the comparison scores |
| `src/pipeline.py` | Runs the steps above in order |
| `src/service.py` | Rules: allowlist check, saving targets, running scans |
| `src/metrics/` | Numbers that Prometheus reads |
| `src/experiments/` | Five experiments that compare the scoring methods |
| `src/report/` | Builds the JSON and HTML reports |
| `db/migrations/` | Database table definitions, applied in order at startup |
| `configs/` | Editable settings: score weights, context presets, CVE mapping |
| `data/feeds/` | Saved copies of public data (EPSS scores, KEV list, NVD subset) |
| `grafana/` | Dashboards and alert rules, loaded automatically |
| `prometheus/` | Prometheus configuration |
| `tests/` | Automatic checks |
| `results/` | Saved scan outputs and experiment results |
| `docs/` | Design documents (plan, scoring, decisions, results, targets) |

---

## 4. What happens during a scan (step by step)

```
you click "Start scan"
  -> the backend checks the website is on the allowlist (docs/TARGETS.md)
  -> for DVWA, WebGoat and bWAPP: log in with the practice-site account
  -> ZAP starts a fresh session and installs the session cookie
  -> ZAP spider: follows the links it can see
  -> ZAP AJAX spider: follows links that only appear after JavaScript runs
  -> ZAP passive scan: checks every page it saw (no attacks sent)
  -> ZAP active scan: sends test attacks to every URL it found
  -> the backend downloads the alerts (in pages of 500)
  -> normalize -> triage -> enrich -> score -> rank
  -> save the findings in PostgreSQL
  -> the scan is marked "done"
```

Only one scan runs at a time. A second request waits in a queue, because ZAP uses about 10 GB of memory and can only handle one scan well.

### Why the scan uses several spiders

The first run on Juice Shop found 95 pages but no API endpoints. The normal spider cannot see pages that load through JavaScript. The AJAX spider drives a headless browser to find those pages. Without it, the active scan never tests the API, so SQL injection and XSS in the API are missed.

### Why ports are stripped from URLs

ZAP stores `http://dvwa:80` as `http://dvwa`. For a long time the alert lookup used the port, so it only matched the front page. That is why early DVWA results showed 2 pages and 16 alerts instead of 71 pages and 775 alerts. The fix is in `src/collectors/run_scan.py`.

---

## 5. From raw alerts to a ranked list

### Step A: Normalize (`src/normalize/normalize.py`)

ZAP reports each alert with a name, a risk level (High, Medium, Low, Informational), a confidence (High, Medium, Low, False Positive), and sometimes a CWE number. The normalizer converts these into one shape and maps each CWE to an OWASP Top 10 category.

Risk levels become numbers used by the score:

| ZAP risk | Number |
|---|---|
| High | 0.8 |
| Medium | 0.5 |
| Low | 0.2 |
| Informational | 0.1 |

Confidence becomes a number too: High 0.9, Medium 0.6, Low 0.3, False Positive 0.0.

### Step B: Triage (`src/triage.py`)

Two rules, both explained in the code:

**Classification.** ZAP does not prove that an issue can be exploited. So each alert gets a label:

| Label | Rule | Meaning |
|---|---|---|
| `vulnerability` | Everything else | The scanner reports it. Not proven exploitable. |
| `potential` | Confidence Low | Might be a real issue. Needs a manual check. |
| `informational` | ZAP risk Informational | A note, such as a missing header. Not a vulnerability. |
| `excluded` | Confidence False Positive | ZAP thinks it is wrong. |

**Grouping.** The same ZAP check can fire many times on one page with different test values. An alert's fingerprint is its plugin ID, URL path (without the query string), parameter and attack string. Alerts with the same fingerprint become one finding, and the count of raw alerts is kept. Different parameters or paths stay separate.

### Step C: Enrich (`src/enrich/enrich.py`)

Some findings have a CVE number (a public ID for a known problem). For those, we look up:

- **CVSS**: a severity score from 0 to 10, from the NVD subset saved in `data/feeds/`.
- **EPSS**: the estimated chance the problem is exploited within 30 days, from `data/feeds/epss.csv`.
- **KEV**: whether CISA lists the problem as actively exploited, from `data/feeds/kev.json`.

Only findings with an explicit CVE mapping in `configs/cve_map.json` get these values. ZAP's web findings usually have no CVE, so most findings have empty CVSS, EPSS and KEV fields. **Missing data is shown as "n/a", never as 0.** We do not guess CVE numbers.

### Step D: Score (`src/scoring/score.py`)

Each finding gets three numbers:

- **S, severity (0 to 1):** CVSS divided by 10 if there is a CVE. Otherwise the ZAP risk number.
- **E, exploitability (0 to 1):** 1.0 if on the KEV list. Otherwise EPSS if available. Otherwise the ZAP confidence number.
- **Context:** four answers about the business, each turned into a number (Low 0.33, Medium 0.66, High 1.0): criticality, data sensitivity, business impact, and internet exposure.

Then the formulas:

```
Impact     I = S x average(criticality, data sensitivity, business impact)
Likelihood L = E x internet exposure
Risk score   = 100 x L x I          (always between 0 and 100)
```

**Why multiply?** A problem needs both a serious flaw (S) and a realistic way in (E x exposure) to matter. If either is near zero, the risk is near zero. Adding them would let a harmless flaw score high just because the site is important.

### Step E: Label

The label comes from the same score:

| Score | Label |
|---|---|
| 60 and above | High |
| 30 to 59.9 | Medium |
| below 30 | Low |

### Step F: Explain (`src/scoring/score.py`, function `explain`)

Every explanation is built from the numbers that produced the score. For example:

> Risk 6.0 (Low). Thresholds: High 60+, Medium 30 to 59.9, Low below 30. Likelihood 0.60 = exploitability 0.60 (ZAP confidence Medium) x internet exposure 1.00 (High). Impact 0.10 = severity 0.10 (ZAP risk Informational) x mean of criticality High, data sensitivity High, business impact High. Main limit: severity 0.10.

This answers the question a reviewer will ask: "the context is High, so why is the score low?" The answer is the **main limit**. Here the flaw itself is informational, so it cannot be urgent no matter how important the site is.

A test checks that the label in the text always matches the number printed with it.

### Step G: Rank (`src/pipeline.py`)

Findings are ranked by four methods, each from its own score:

| Method | Score |
|---|---|
| `risk` | The framework score above (the main result) |
| `weighted_sum` | A simple weighted average, used as a comparison |
| `cvss_only` | 100 x severity (ignores context and exploitability) |
| `zap_risk_only` | 100 x ZAP risk level (ignores context) |

Ties are broken by plugin ID and then URL, so repeated runs give the same order. A test checks that changing the input order does not change the result.

**Why are the rankings often the same?** In one scan, most findings have the same ZAP risk and confidence. When the inputs are equal, every method gives an equal score, so they produce the same order. The methods only differ when the findings differ in CVE data, KEV status or ZAP risk. Tests in `tests/test_ranking_methods.py` show both cases.

---

## 6. Evaluation: how we know it works

A score that looks sensible is not evidence. The project runs five experiments (`make experiments`):

| Experiment | Question it answers |
|---|---|
| 1. Detection | How many known vulnerability types does each target's scan find? |
| 2. Ranking | How much do the four rankings agree (Kendall tau, top-k overlap)? |
| 3. Context sensitivity | Does changing only the business context change the context-aware score, while the CVSS-only ranking stays the same? |
| 4. Weights | Does the weighted-sum ranking stay stable when weights change inside documented ranges? |
| 5. Ablation | What happens when each factor is removed in turn? |

Results are summarised in [docs/RESULTS.md](docs/RESULTS.md). Current limits:

- One run per target. No repeat runs, so no variance estimate.
- WebGoat is a single-page app. The scanner reached only 2 of its pages, so its numbers say nothing about detection.
- Most ZAP web findings have no CVE, so the framework's advantage over the baselines comes mostly from context, not from CVE data.
- Precision is low because most alerts are minor (missing headers and similar). That is expected for a web scanner.

---

## 7. The web interface (React)

The frontend is in `frontend/`. It is a single-page app with four screens:

| Screen | Route | What you do |
|---|---|---|
| Targets | `/` | See every target and its latest scan status |
| Add target | `/targets/new` | Pick a website from the allowlist and rate its business context |
| Target | `/targets/:id` | See the context, start a scan, open the latest results |
| Scan results | `/scans/:id` | See summary cards, filter findings, expand a row to read why it scored that way |

The results screen shows:

- **Raw alerts** (every alert the scanner raised) and **unique findings** (after merging repeats). The gap between them is the noise removed by grouping.
- **High, Medium and Low counts** from the framework score.
- **Classification** counts, with a click to filter.
- A table with the rank, class, score, band, ZAP risk, confidence, CVSS, EPSS, KEV and count. Missing values show as "n/a".
- An expandable explanation with each factor and the rank under every method.

Scan progress updates automatically while the scan runs.

The frontend is built into a small nginx container. nginx serves the app and forwards `/api` to the backend. The backend still checks the login, so the browser asks for the WASRA username and password once.

---

## 8. Dashboards (Grafana)

Dashboards are **automatic**. Grafana loads them from `grafana/provisioning/` on startup, so you never create them by hand. The same goes for the data source and the alert rule.

| Dashboard | Panels |
|---|---|
| WASRA overview | Scans by status, findings by ZAP risk, average framework risk per target, scans over time (table), findings by classification, raw alerts vs unique findings |
| WASRA ranking stability | Top 10 findings by framework risk for a chosen scan, with all four rankings side by side, and the risk of top findings across scans |
| WASRA validation | Detection precision, recall and detected-type counts per target (from the validation results table) |

The alert rule `kev-finding` fires when a KEV-listed finding appears on a monitored target.

Prometheus reads `/metrics` from the backend. The metrics are computed from the database on every scrape, so they are never out of date and nothing is stored in memory.

Grafana connects to PostgreSQL with a **read-only role** (`grafana_ro`). It cannot change data or start scans.

---

## 9. Safety rules

- **Allowlist.** A scan only starts for a URL listed in `docs/TARGETS.md`. The server checks this, not the browser.
- **Local only.** Every port is bound to `127.0.0.1`.
- **Login.** The web app and API use HTTP Basic auth with credentials from `.env`. The comparison uses a constant-time check.
- **Secrets.** `.env` is not committed to git. `make env` generates random passwords.
- **Practice-site logins.** The default accounts of the practice apps are only used inside the Docker network.
- **Read-only dashboards.** Grafana cannot write.

---

## 10. Running it

See [docs/HOW_TO_START.md](docs/HOW_TO_START.md) for the full guide. In short:

```
make env                 # first time only: create .env with random passwords
make up                  # start all services (migrations run automatically)
make test                # offline unit tests
make scan-validation     # scan the three practice sites (slow, one at a time)
make experiments         # rebuild the experiment tables
make down                # stop everything
```

Then open:

- http://127.0.0.1:8081 for the new React interface
- http://127.0.0.1:8080 for the original server-rendered pages
- http://127.0.0.1:3001 for Grafana

---

## 11. Known limits and what is next

| Limit | What would fix it |
|---|---|
| WebGoat barely scanned (single-page app) | Seed the scanner from API endpoints, or report WebGoat as a coverage limit |
| Juice Shop scan time not measured | One timed run with each stage recorded |
| One run per target | Repeated runs with variance reported |
| Most findings lack CVEs | A reviewed CVE mapping for more finding types |
| Commits not pushed from this machine | Push with an account that has write access |
| Missing docs: `TEST_PLAN.md`, `UI.md`, `LITERATURE.md`, `REPRODUCIBILITY.md` | Write them |

For the reasoning behind each choice, see [docs/DECISIONS.md](docs/DECISIONS.md). For what is still open, see [docs/OPEN_QUESTIONS.md](docs/OPEN_QUESTIONS.md).
