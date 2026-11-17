# Web Application Security and Risk Assessment

A reproducible pipeline that scans vulnerable web apps with OWASP ZAP, normalizes the alerts, enriches them with EPSS, KEV and CVSS data from a local snapshot, and ranks findings with an explainable risk score.

## Layout

- `src/collectors/`: ZAP client, scan runner and auth helper
- `src/normalize/`, `src/enrich/`, `src/scoring/`: pipeline stages
- `src/db.py`, `src/migrate.py`, `db/`: Postgres layer and migrations
- `src/api/`, `src/service.py`, `src/web/`, `src/cli.py`: API, service, UI and CLI
- `src/report/`, `src/metrics/`, `src/experiments/`: reports, metrics and experiments
- `configs/`: weights and ground truth
- `docs/`: architecture, scoring, plan and decisions
- `tests/`: unit, integration and e2e tests

## Quick start

```
docker compose up -d
make scan-validation
make experiments
```

Published ports are bound to 127.0.0.1. Run one scan at a time: ZAP uses about 10 GB of RAM.

## Docs

- [Architecture](docs/ARCHITECTURE.md)
- [Scoring](docs/SCORING.md)
- [Targets](docs/TARGETS.md)
- [Decisions](docs/DECISIONS.md)
- [Open questions](docs/OPEN_QUESTIONS.md)
