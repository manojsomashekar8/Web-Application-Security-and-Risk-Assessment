# Plan

A checked box is done and committed. An unchecked box is not done. Notes say what is partial.

## Phase 1: Environment
- [x] Docker stack for all services; every port bound to 127.0.0.1
- [x] `install.sh` for a fresh Ubuntu 22.04 or 24.04 host (idempotent; `--check` and `--no-start`)
- [x] `make up` refuses public ports in `AUTH_MODE=none`
- [x] Backend restarts on failure; frontend resolves the backend per request

## Phase 2: Scanning
- [x] ZAP settings checked against the installed version (docs/ZAP_NOTES.md)
- [x] Scan profiles quick, standard and deep, with stored settings and stage timings
- [x] Custom settings with server-side bounds (INSANE strength not offered)
- [x] DVWA is the default target; it is reset before every scan
- [x] Scans interrupted by a backend restart are marked failed at startup
- [x] ZAP's own HTML report generated at the end of each scan and offered for download
- [x] AJAX browser fixed: firefox-headless (D67)
- [ ] Client Spider (not active in the installed image; see docs/OPEN_QUESTIONS.md)
- [ ] Scans started from the web app are not sampled for CPU and memory (only `scripts/sample_usage.py` is)
- [x] Alert lookup bug fixed for every scan path (D71)

## Phase 3: Cleaning, classification, enrichment
- [x] One common finding format with CWE and OWASP mapping
- [x] Classification: vulnerability, potential, informational, excluded
- [x] Repeated alerts merged by fingerprint; raw counts kept
- [x] Enrichment provenance per value; missing or corrupt feeds give n/a and the scan continues
- [x] KEV is n/a without a CVE (D54, D56)
- [ ] CVE mapping for ZAP findings (`configs/cve_map.json` is empty)

## Phase 4: Scoring and ranking
- [x] Framework score, three comparison scores, explanations built from the stored numbers
- [x] Independent rankings; deterministic tie order; top-10 overlap per scan
- [x] Re-score from stored raw alerts (scans from before raw storage cannot be re-scored)

## Phase 5: Web app, downloads and import/export
- [x] React app: targets, new target, target detail with profiles and custom form, scan results
- [x] Results sortable by every column; default by framework risk
- [x] Per-finding downloads (HTML and JSON); full-scan HTML and JSON; findings CSV; ZAP HTML report
- [x] Scanner text escaped in HTML (tested)
- [x] Versioned export and import (`wasra-scan`, version 1), recomputed scores, duplicate refusal (tested)
- [ ] Export and import round trip and refusal tests run in the integration suite (written, run in reproduce)

## Phase 6: Dashboards and monitoring
- [x] Prometheus metrics: scans, findings, bands, stage durations, n/a enrichment, top-10 overlap, classification, raw vs unique, scan CPU and memory
- [x] Grafana overview with a `target` filter; validation dashboard with latest-run default, run-date selector and "Coverage too low"
- [x] Dashboards provisioned from files and checked by the Grafana test
- [x] Status panel: Postgres, ZAP, feed freshness

## Phase 7: Validation and experiments
- [x] Coverage threshold (10 pages); WebGoat shows "Coverage too low", never 0
- [x] Experiments 1 to 7, each as JSON and CSV
- [x] Timed runs and the profile comparison on DVWA (docs/RESULTS.md)
- [x] Validation matrix: WebGoat and bWAPP, every profile, one run each (docs/RESULTS.md)
- [ ] Repeated runs per target (each target was run once)

## Phase 8: Resources
- [x] Measured peak usage of a deep DVWA scan: ZAP 12.8 GB; free-memory check requires 14 GB
- [x] Container memory cap tried and removed after it caused failures (D57)
- [ ] Measured minimum and recommended RAM and disk for every profile (only deep was measured)

## Phase 9: Documentation and reproduction
- [x] EXPLAIN, README, HOW_TO_START, ARCHITECTURE, SCORING, RESULTS, ZAP_NOTES, UI, UI_REVIEW, TEST_PLAN, LITERATURE, DECISIONS, OPEN_QUESTIONS
- [x] `make reproduce` passed (attempt 10)
- [ ] Literature sources verified online (the list was written from memory)

## Phase 10: Optional extras
- [ ] Advisory watcher
- [ ] Nuclei scanner
- [ ] Local language model explanations (only after the phases above)
