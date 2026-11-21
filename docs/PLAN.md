# Plan

A checked box means the work is done and committed. Phase 7 is optional.

## Phase 1: Set up the environment
- [x] Docker setup for all services
- [x] Every service only accepts connections from your own computer
- [x] The web app can talk to the scanner
- [x] Juice Shop scanned once, raw results saved

## Phase 2: Clean up, classify and group
- [x] One common format for findings, linked to CWE and OWASP categories
- [x] Saved copies of public severity and exploit lists, each with a checksum
- [x] Alerts classified as vulnerability, potential, informational or excluded
- [x] Repeated alerts merged by fingerprint; raw counts kept
- [x] Automatic tests for clean-up, classification and grouping
- [ ] Enrichment provenance recorded; missing feeds handled without failing the scan (see [Open questions](OPEN_QUESTIONS.md))

## Phase 3: Scoring
- [x] Risk score, three comparison scores, and explanations built from the actual numbers (see [Scoring](SCORING.md))
- [x] Explanation names the main limiting factor and the thresholds used
- [x] Rankings computed independently per method; exact ties broken deterministically
- [x] Automatic tests: score range, determinism, monotonicity, label-band consistency, ranking divergence, context sensitivity

## Phase 4: Web app, database and frontend
- [x] Database tables and migrations, including a read-only account for dashboards
- [x] API for targets, scans, findings, allowed targets and latest scan
- [x] Original server-rendered pages (port 8080)
- [x] React frontend in its own container (port 8081): targets, new target, target detail, results with summary, filters and explanations
- [x] HTML and JSON reports (PDF not built)

## Phase 5: Dashboards and monitoring
- [x] Metrics exporter for Prometheus, including classification and raw-vs-unique counts
- [x] Grafana dashboards and data sources, provisioned from files at startup
- [x] Overview dashboard includes classification and raw-vs-unique panels
- [x] Browser tests for the original pages, the React app and Grafana
- [ ] KEV alert rule covered by an automatic check

## Phase 6: Validation
- [x] DVWA scanned (71 pages, 775 alerts)
- [x] bWAPP scanned (94 pages, 609 alerts)
- [ ] WebGoat scanned with usable coverage (see [Open questions](OPEN_QUESTIONS.md))
- [x] Experiments 1 to 5 run and saved, after grouping and classification
- [ ] Deduplication experiment (review recommendation)
- [x] Results summary ([Results](RESULTS.md))
- [ ] Screenshots added to the results

## Phase 7: Optional extras
- [ ] Advisory watcher
- [ ] Nuclei scanner
- [ ] Local language model explanations (only after phases 1 to 6)
