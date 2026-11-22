# How to start the project

This guide is for someone who has never run the project before. Follow the steps in order. For the full explanation of how everything works, read [EXPLAIN.md](../EXPLAIN.md).

## The short way (fresh Ubuntu 22.04 or 24.04)

```
./install.sh            # checks the system, installs what is missing, creates .env, builds and starts everything
./install.sh --check    # only report what is missing and the resource check (changes nothing)
./install.sh --no-start # install and build, but do not start
```

`install.sh` is safe to run twice. It never overwrites an existing `.env`. It installs Docker from Docker's official apt repository, and it warns if the machine has less RAM (16 GB) or less free disk (25 GB) than recommended.

## What you need (if you do not use install.sh)

- Docker and Docker Compose
- Python 3.12 and `make` and `git`
- About 25 GB of free disk space
- At least 16 GB of RAM. A deep scan of DVWA peaked at 12.8 GB of ZAP memory (see docs/RESULTS.md).
- One scan at a time. Running two at once slows the computer a lot.

## Step 1: Create your settings file (first time only)

```
make env
```

This creates `.env` with random passwords. Never share it or commit it to git. `AUTH_MODE=none` (no login) is the default; set `AUTH_MODE=basic` in `.env` to require a login.

## Step 2: Start everything

```
make up
```

`make up` first checks that every published port is bound to 127.0.0.1 when `AUTH_MODE=none`, and refuses to start otherwise. Database migrations are applied when the backend starts.

| What | Address | Login |
|---|---|---|
| **React web app (use this one)** | http://127.0.0.1 (port 80) | none, or `WEB_USER` and `WEB_PASSWORD` from `.env` when `AUTH_MODE=basic` |
| Original web pages | http://127.0.0.1:8080 | same as above |
| Dashboards (Grafana) | http://127.0.0.1:3001 | `admin`, password is `GRAFANA_ADMIN_PASSWORD` in `.env` |
| Scanner (ZAP) | http://127.0.0.1:8090 | API key in `.env` (`ZAP_API_KEY`) |

`zap` and `webgoat` can show "unhealthy" in `docker compose ps`. Their health checks are slow to pass; both still answer requests.

**After a reboot** Docker stops the containers. Run `make up` again. A scan that was running when the backend stopped is marked `failed` with "interrupted" at the next start.

## Step 3: Check that it works

```
make test
```

This runs the offline tests (about 100 pass; the browser and integration tests are skipped). The browser and integration tests need the stack running:

```
WASRA_INTEGRATION=1 WASRA_E2E=1 make test
```

## Step 4: Scan DVWA (the default target)

DVWA is the target used for development and demos. Only the websites in [TARGETS.md](TARGETS.md) can be scanned.

1. Open http://127.0.0.1 and open the DVWA target (add it first if it is not listed: name, website, four context ratings).
2. Choose a profile:
   - **quick**: a few seconds to a few minutes, passive checks only, no attacks.
   - **standard**: traditional and AJAX spider, active scan at Low strength, time limits. About 3 minutes on DVWA.
   - **deep**: the reference scan, no limits. About 8 minutes on DVWA.
   - **custom**: your own settings, checked by the server. INSANE strength is not offered.
3. Click **Start scan**. The page shows the settings that were used and how long each stage took.
4. When it says `done`, open the ranked findings. Sort any column by clicking its header. Download a finding (HTML or JSON), the full report, or the table as CSV.

From the terminal, the same default scan is:

```
make scan-dvwa
```

DVWA's database is reset and its security level set to low before every scan, so one scan never changes the next.

## Export and import a scan

```
python scripts/export_scan.py SCAN_ID          # writes results/exports/wasra-scan-SCAN_ID.json
python scripts/import_scan.py FILE.json        # creates a new scan from the file; nothing is scanned
```

The file has `format` `wasra-scan` and `format_version` 1. Imports reject other versions, files over 25 MB, and malformed data with a message. Scores are recomputed on import, never trusted from the file. Importing the same file twice is refused.

## Step 5: Load the validation matrix

```
make load-validation
```

This imports the saved WebGoat and bWAPP runs (every profile) into the scan list, and refreshes the validation dashboard. It scans nothing, and it recomputes every score. Running it twice is safe: duplicates are refused.

## Step 6: Build the results tables

```
make experiments
```

This reads the saved scan results and writes the experiment tables (JSON and CSV) to `results/experiments/`.

## Changing the frontend

```
docker compose build frontend
docker compose up -d --no-deps frontend
```

`--no-deps` restarts only the frontend. Without it, Docker also restarts Postgres (through the dependency chain), which is harmless when no scan runs but interrupts one that does.

## Stopping and restarting

`make down` stops and removes the containers and keeps the database volume. Starting again with `make up` brings the data back.

| Goal | Command |
|---|---|
| Stop everything (keeps your data) | `make down` |
| Start again | `make up` |
| Delete containers and volumes (wipes the database) | `make clean` |

`make clean` deletes all stored targets and scans. Raw files in `results/raw/` are kept. Take a backup first:
`docker compose exec -T postgres pg_dump -U wasra -d wasra > backup.sql`.

## When something goes wrong

- **A scan fails with "Read timed out" to zap.** ZAP may be busy or still starting. Wait for `docker compose ps` to show zap, then retry.
- **"only N MB of memory is free"** (HTTP 507). Free memory is below the threshold in `configs/resources.json`. Close other programs, then retry.
- **Out of disk space.** Check with `df -h /`. Remove only images you do not need.
- **A service will not start.** Read its log: `docker compose logs <service>`.
- **Port already in use.** Find what is using it with `ss -ltnp | grep <port>`.
- **The web page asks for a login again and again.** Check `AUTH_MODE` and the username and password in `.env`.
