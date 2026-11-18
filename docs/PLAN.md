# Plan

This page tracks the project in seven phases. A checked box means the work is done and committed to the local repository. Phase 7 is optional.

## Phase 1: Set up the environment
- [x] Docker setup for all services (scanner, database, web app, dashboards, practice websites)
- [x] Every service only accepts connections from your own computer
- [x] The web app can talk to the scanner
- [x] Juice Shop scanned once, raw results saved

## Phase 2: Clean up and add facts
- [x] One common format for findings, with links to CWE and OWASP categories
- [x] Saved copies of public severity and exploit lists, each with a checksum
- [x] Automatic tests for the clean-up and adding-facts steps

## Phase 3: Scoring
- [x] Risk score, three simpler comparison scores, and plain-language explanations (see [Scoring](SCORING.md))
- [x] Settings in `configs/weights.json` and `configs/context_presets.json`
- [x] Automatic tests, including checks that the score always stays between 0 and 100

## Phase 4: Web app, database and reports
- [x] Database tables and setup scripts, including a read-only account for the dashboards
- [x] Web app and API for targets, scans and findings
- [x] Web app pages with login
- [x] HTML and JSON reports (PDF not built, see [Open questions](OPEN_QUESTIONS.md))

## Phase 5: Dashboards and monitoring
- [x] Metrics exporter for Prometheus
- [x] Grafana dashboards and data sources, set up from files
- [ ] KEV alert rule, checked by `make test`
- [x] Browser tests for the web app and Grafana (see `tests/e2e/`)

## Phase 6: Validation
- [x] DVWA scanned
- [x] bWAPP scanned
- [ ] WebGoat scanned with usable coverage (see [Open questions](OPEN_QUESTIONS.md))
- [x] Experiments 1 to 5 run and saved
- [x] Results summary written ([Results](RESULTS.md))
- [ ] Screenshots of the web app and dashboards added to the results

## Phase 7: Optional extras
- [ ] Advisory watcher
- [ ] Nuclei scanner
- [ ] Local language model explanations (only after phases 1 to 6)
