# How to start the project

This guide is for someone who has never run the project before. Follow the steps in order. For the full explanation of how everything works, read [EXPLAIN.md](../EXPLAIN.md).

## What you need

- **Docker** and **Docker Compose**
- **Python 3.12** and **Node.js 20** (only if you want to change the frontend outside Docker)
- **About 25 GB of free disk space.** The scanner images are large.
- **At least 16 GB of RAM.** The scanner uses about 10 GB while it runs.
- **One scan at a time.** Running two at once slows your computer a lot.

## Step 1: Create your settings file (first time only)

```
make env
```

This creates `.env` with random passwords. Never share it or commit it to git.

## Step 2: Start everything

```
make up
```

This starts the services in Docker. Database changes (migrations) are applied automatically when the backend starts. The first start takes several minutes because Docker downloads and builds the images.

After it finishes, these addresses work from your own computer:

| What | Address | Login |
|---|---|---|
| **React web app (use this one)** | http://127.0.0.1:80 | `WEB_USER` and `WEB_PASSWORD` from `.env` |
| Original web pages | http://127.0.0.1:8080 | Same as above |
| Dashboards (Grafana) | http://127.0.0.1:3001 | `admin` and `GRAFANA_ADMIN_PASSWORD` from `.env` |
| Scanner (ZAP) | http://127.0.0.1:8090 | API key in `.env` |

**Note:** `zap` and `webgoat` may show "unhealthy" in `docker compose ps`. That comes from their health checks. Both still answer requests.

**After a reboot** Docker stops the containers. Run `make up` again.

## Step 3: Check that it works

```
make test
```

You should see `44 passed` or similar. The browser tests are skipped unless you turn them on:

```
WASRA_E2E=1 .venv/bin/python -m pytest tests/e2e
```

## Step 4: Scan something

Only the websites listed in [TARGETS.md](TARGETS.md) can be scanned.

1. Open http://127.0.0.1:80 and log in.
2. Click **Add target** if the site is not listed yet. Pick a website and rate the business context (criticality, data sensitivity, exposure, impact).
3. Open the target and click **Start scan**. The page updates by itself. A scan can take a long time.
4. When it says `done`, you see the ranked findings. Click a row to read why it got its score.

To scan the three practice sites from the terminal instead:

```
make scan-validation
```

## Step 5: Rebuild the results tables

```
make experiments
```

This reads the saved scan results and writes the experiment tables to `results/experiments/`.

## Changing the frontend

After editing files in `frontend/`:

```
docker compose build frontend
docker compose up -d frontend
```

To check the frontend builds without Docker:

```
cd frontend
npm install
npm run build
```

## Stopping and restarting

| Goal | Command |
|---|---|
| Stop everything (keeps your data) | `make down` |
| Start again | `make up` |
| Delete containers and volumes (wipes the database) | `make clean` |

`make clean` deletes stored scan results in the database. Raw files in `results/raw/` are kept.

## When something goes wrong

- **Out of disk space.** Check with `df -h /`. Remove only images you do not need.
- **The computer freezes during a scan.** Stop the scanner with `docker compose stop zap` and close other programs.
- **A service will not start.** Read its log: `docker compose logs <service>`, for example `docker compose logs backend`.
- **Port already in use.** Find what is using it with `ss -ltnp | grep <port>`.
- **The web page asks for a login again and again.** Check the username and password in `.env` match what you type.
