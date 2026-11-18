# How to start the project

This guide is for someone who has never run the project before. Follow the steps in order.

## What you need

- **Docker** and **Docker Compose** installed
- **Python 3.12**
- **About 25 GB of free disk space**. The scanner images are large.
- **At least 16 GB of RAM**. The scanner uses about 10 GB while it runs.
- **Only one scan at a time.** Running two at once will slow your computer a lot.

## Step 1: Create your settings file (first time only)

```
make env
```

This creates a file called `.env` with random passwords. Never share this file or commit it to git.

## Step 2: Start everything

```
make up
```

This starts nine services in Docker: the scanner, the database, the web app, the dashboards, the monitoring, and the three practice websites. The first start takes several minutes because Docker downloads the images.

When it finishes, these addresses work from your own computer:

| What | Address | Login |
|---|---|---|
| Web app | http://127.0.0.1:8080 | Username and password from `.env` (`WEB_USER`, `WEB_PASSWORD`) |
| Dashboards (Grafana) | http://127.0.0.1:3001 | Username `admin`, password from `.env` (`GRAFANA_ADMIN_PASSWORD`) |
| Scanner (ZAP) | http://127.0.0.1:8090 | Uses an API key from `.env` |

**Note:** `zap` and `webgoat` may show "unhealthy" in `docker compose ps`. That status comes from their health checks, not from the services. Both still answer requests.

## Step 3: Check that it works

```
make test
```

This runs the automatic checks. You should see something like `36 passed`. The browser tests are skipped unless you run them with the browser setting:

```
WASRA_E2E=1 .venv/bin/python -m pytest tests/e2e/test_ui_smoke.py tests/e2e/test_grafana_smoke.py
```

## Step 4: Scan something

The web app only scans the sites listed in [TARGETS.md](TARGETS.md).

1. Open http://127.0.0.1:8080 and log in.
2. Click the target you want to scan, for example DVWA.
3. Click **Start scan**, then wait. A scan can take a long time, especially the active scan.
4. When it says `done`, open the ranked findings.

To scan from the terminal instead, use `make scan-validation` (scans DVWA, WebGoat and bWAPP one after another).

## Step 5: Build the results tables

```
make experiments
```

This reads the saved scan results and writes the experiment tables to `results/experiments/`.

## Stopping and restarting

| Goal | Command |
|---|---|
| Stop everything (keeps your data) | `make down` |
| Start again later | `make up` |
| Delete containers and volumes (wipes the database) | `make clean` |

`make clean` deletes stored scan results in the database. Raw scan files in `results/raw/` are kept.

## When something goes wrong

- **Out of disk space.** Check with `df -h /`. Unused Docker images can be removed with `docker image prune`, but only remove images you do not need.
- **The computer freezes during a scan.** Stop the scanner with `docker compose stop zap`, then free memory by closing other programs.
- **A service will not start.** Run `docker compose logs <service-name>` to see the error. For example, `docker compose logs postgres`.
- **Port already in use.** Another program is using the same port. Find it with `ss -ltnp | grep <port>` and stop it.
