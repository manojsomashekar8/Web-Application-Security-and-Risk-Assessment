# Web Application Security and Risk Assessment

## What is this?

This project scans deliberately vulnerable websites with the OWASP ZAP scanner, then ranks the problems it finds by how risky they are for a specific business, and explains each ranking in plain words.

It runs entirely on your own computer. Nothing is sent to outside services.

## Start here

- **New to the project?** Read [EXPLAIN.md](EXPLAIN.md). It walks through the whole thing step by step.
- **Want to run it?** Read [docs/HOW_TO_START.md](docs/HOW_TO_START.md), or on a fresh Ubuntu machine run `./install.sh`.
- **Want the results?** Read [docs/RESULTS.md](docs/RESULTS.md).

## Quick start

```
./install.sh            # fresh Ubuntu 22.04 or 24.04: installs what is missing and starts everything
make up                 # start the stack, if it is already installed
make scan-dvwa          # the default demo scan of DVWA (about 8 minutes)
```

Then open http://127.0.0.1 (the app). Dashboards are at http://127.0.0.1:3001.

## Commands

| Command | What it does |
|---|---|
| `make env` | create `.env` with random passwords (first time only) |
| `make up` | start all services (refuses to start with public ports in `AUTH_MODE=none`) |
| `make down` | stop everything (keeps data) |
| `make scan-dvwa` | scan DVWA through the API (the default target) |
| `make experiments` | rebuild the experiment tables (JSON and CSV) |
| `make load-validation` | load the saved WebGoat and bWAPP validation matrix (scans, summary and dashboard rows) into a fresh database |
| `make test` | offline tests; with the stack up, `WASRA_INTEGRATION=1 WASRA_E2E=1 make test` runs the rest |
| `make reproduce` | full clean run. Deletes the database first, so back it up |
| `./install.sh --check` | report what is missing on a host, change nothing |

## Validation matrix

The matrix (WebGoat and bWAPP, each with quick, standard and deep) is saved in the repository: raw alerts, settings, ZAP version and image digest, and the summary in `results/validation/summary.json`. After `make up`, run `make load-validation` to see the matrix in the scan list and on the validation dashboard. Details and the table: [docs/RESULTS.md](docs/RESULTS.md).

## Scripts

| Script | What it does |
|---|---|
| `python scripts/export_scan.py SCAN_ID` | write a finished scan to a versioned JSON file |
| `python scripts/import_scan.py FILE` | import an exported scan (scores are recomputed; nothing is scanned) |
| `python scripts/sample_usage.py SCAN_ID` | record CPU and memory of ZAP and the backend during a scan |
| `python scripts/validation_matrix.py --target ID --name NAME` | run each profile once for a target and save the files under `results/validation/` |
| `python scripts/validation_summary.py [--store]` | summarise the matrix and (with `--store`) refresh the dashboard rows |
| `python scripts/validation_exports.py` | write the matrix as importable exports |

## Where things are

| Folder or file | What is in it |
|---|---|
| `frontend/` | The React app (port 80) |
| `src/` | Python: scanning, scoring, the API, reports, import and export |
| `db/migrations/` | Database tables, applied in order at startup |
| `configs/` | Scan profiles, score weights, validation threshold, resource limits, CVE mapping |
| `grafana/`, `prometheus/` | Dashboards and monitoring settings |
| `tests/` | Automatic checks |
| `results/` | Raw scan outputs, experiment results, ZAP reports and exports |
| `docs/` | Design documents and results |

## Safety

- Only the websites in [docs/TARGETS.md](docs/TARGETS.md) can be scanned. The server checks this in every mode.
- Every service listens only on your own computer (`127.0.0.1`).
- `AUTH_MODE=none` (the default) has no login, which is safe only because of the rule above. Set `AUTH_MODE=basic` in `.env` to require one.
- Passwords live in `.env`, which is never committed.

## Documentation

- [EXPLAIN](EXPLAIN.md): the whole project, step by step
- [How to start](docs/HOW_TO_START.md)
- [Plan](docs/PLAN.md): what is built and what is left
- [Architecture](docs/ARCHITECTURE.md)
- [Scoring](docs/SCORING.md): how the risk score is worked out
- [Results](docs/RESULTS.md): what the scans found, and the profile comparison
- [ZAP notes](docs/ZAP_NOTES.md): the scanner settings we use, checked against the installed version
- [UI guide](docs/UI.md) and [UI review](docs/UI_REVIEW.md)
- [Test plan](docs/TEST_PLAN.md)
- [Reproducibility](docs/REPRODUCIBILITY.md)
- [Targets](docs/TARGETS.md)
- [Decisions](docs/DECISIONS.md): why things were built the way they were
- [Open questions](docs/OPEN_QUESTIONS.md): what is still unresolved, with the default used for each
- [Literature](docs/LITERATURE.md)
