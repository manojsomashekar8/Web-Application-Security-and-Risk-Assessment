# Test plan (final state)

This page says what is tested, how, and what is not tested. It is for someone who wants to check that the project does what it claims.

## Layers

| Layer | Where | Needs | Command |
|---|---|---|---|
| Unit | `tests/*.py` (not the two folders below) | Python only | `make test` |
| Integration | `tests/integration/` | Running stack | `WASRA_INTEGRATION=1 make test` |
| Browser (React, original pages, Grafana) | `tests/e2e/` | Running stack, Chromium | `WASRA_E2E=1 make test` |

`make test` always runs the unit layer. The other two layers are skipped unless their environment variable is set, so the offline checks pass on any machine.

## What the unit tests check

| Area | File | Checks |
|---|---|---|
| Scoring | `test_scoring.py` | Worked example matches the spec; score stays in 0 to 100; deterministic; raising any input never lowers the score; band boundaries; the explanation label matches the score band (300 random cases) |
| Ranking | `test_ranking_methods.py` | Methods diverge when inputs differ; they agree when they should; equal inputs give a deterministic order; context changes move the framework score but not the CVSS-only score |
| Triage | `test_triage.py` | Classification rules; repeats merged; different parameters or paths kept apart |
| Normalization | `test_normalize.py` | ZAP alert fields map to the internal shape; CWE to OWASP mapping |
| Enrichment | `test_enrich.py`, `test_enrich_resilience.py` | Mapped CVEs get CVSS, EPSS and KEV; unmapped findings get n/a; a missing or corrupt feed file logs a warning and leaves n/a; provenance is recorded; a missing manifest leaves the snapshot date unknown |
| Allowlist and auth | `test_allowlist.py`, `test_auth_and_bindings.py` | Non-allowlisted URLs are rejected in both auth modes; basic mode requires a login; none mode refuses any public port binding; the repository compose file passes that check |
| Health | `test_health.py` | Feed freshness rule (fresh, stale after 30 days, missing); Postgres failure is reported, not raised |
| Experiments | `test_experiments_csv.py` | CSV export shape; deduplication counts |
| Pipeline | `test_compare_pipeline.py` | Same input gives the same ranked output |

## Browser tests (need the stack)

- `test_ui_smoke.py`: original pages load; auth is enforced; the new-target form has every field.
- `test_react_ui.py`: the React app renders the targets list, offers allowlisted sites, shows the results summary, and expands a row without console errors.
- `test_grafana_smoke.py`: Grafana is healthy; the Prometheus data source is OK; dashboards load; the overview has the `target` variable and the four new panels.
- `test_flow.py`: the full path (create target, scan Juice Shop, view findings, download the report). This runs a real scan and can take an hour.

## What is not tested

- Real production systems. Everything runs against three practice sites and one stored scan set.
- Scanner accuracy beyond the ground-truth mapping in `configs/ground_truth.json`.
- Repeated scans. Each target has one run, so run-to-run variation is unknown.
- Load and concurrency. Only one scan runs at a time by design.

## How to add a test

1. Put a unit test in `tests/` if it can run offline.
2. Use `WASRA_E2E=1` for anything that needs the browser or the running stack.
3. Keep each test about one rule, and name it after the rule.


## Final state (2026-11-22)

- Offline unit tests: 105 pass with the stack down. Browser and integration tests are skipped unless `WASRA_E2E=1` and `WASRA_INTEGRATION=1` are set.
- Last full `make reproduce` (attempt 10): 134 unit and browser tests passed, then 12 more in the e2e stage, then 17 integration tests passed. The flow test runs a real DVWA scan and takes about 10 to 13 minutes.
- New areas covered: scan profile validation (17 cases); API scan requests refused before anything starts; finding reports escape scanner text; CSV guards against spreadsheet formulas and keeps blank cells blank; import validation (format version, corrupt JSON, oversize file, malformed alerts, bad profile, bad rating, content hash); round trip and duplicate refusal (integration); results sorting (browser); DVWA flow (browser); Grafana validation panels and the one-row-per-target filter (browser).
- `install.sh` is linted by shellcheck when it is installed. It was not installed on the test host, so it was not linted there.
