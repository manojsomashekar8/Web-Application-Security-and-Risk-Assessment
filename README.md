# Web Application Security and Risk Assessment

## What is this?

This project scans deliberately vulnerable websites for security problems, then ranks the problems by how risky they are for a specific business.

Think of it in three steps:

1. **Scan**: a free tool called OWASP ZAP visits a website and tries common attacks.
2. **Clean up and add facts**: the results are sorted into one format, then matched with public data about how severe each problem is.
3. **Rank**: each problem gets a risk score from 0 to 100, based on how severe it is, how easy it is to exploit, and how important the website is to the business.

Everything runs on your own computer. Nothing is sent to outside services.

## Before you start

You need:
- Docker and Docker Compose
- Python 3.12
- Around 25 GB of free disk space (the scanner images are large)
- At least 16 GB of RAM (the scanner uses about 10 GB while it runs)

## How to run it

```
make up                # starts all the services
make test              # runs the offline tests
make scan-validation   # scans the three practice websites (takes about 30 minutes)
make experiments       # builds the results tables from the scans
make down              # stops everything
```

Then open the web app at http://127.0.0.1:80 (log in with the username and password from your `.env` file). The dashboards are at http://127.0.0.1:3001.

New to the project? Read [EXPLAIN.md](EXPLAIN.md) for a full, plain-language walkthrough of how it works.

## Where things are

| Folder or file | What is in it |
|---|---|
| `src/` | The Python code: scanning, scoring, the web app and the command line tool |
| `db/` | The database setup scripts |
| `configs/` | Settings you can change, such as score weights and the list of CVEs |
| `grafana/`, `prometheus/` | Dashboard and monitoring settings |
| `tests/` | Automatic checks of the code |
| `results/` | Scan outputs and experiment results |
| `docs/` | Written documentation (start with [docs/PLAN.md](docs/PLAN.md)) |

## Documentation

- [EXPLAIN](EXPLAIN.md): the whole project, step by step
- [Plan](docs/PLAN.md): what is built and what is left
- [Architecture](docs/ARCHITECTURE.md): how the parts fit together
- [Scoring](docs/SCORING.md): how the risk score is worked out
- [Results](docs/RESULTS.md): what the scans found
- [Targets](docs/TARGETS.md): the websites we are allowed to scan
- [Decisions](docs/DECISIONS.md): why things were built the way they were
- [Open questions](docs/OPEN_QUESTIONS.md): what is still unresolved

## Safety

- Only the websites listed in [docs/TARGETS.md](docs/TARGETS.md) can be scanned. The server rejects anything else.
- All services are only reachable from your own computer (they listen on 127.0.0.1).
- Passwords live in `.env`, which is not committed to git.
