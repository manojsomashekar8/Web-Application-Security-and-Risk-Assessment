# Install

This guide installs WASRA on a computer running **Ubuntu 22.04 or 24.04**. It takes about 30 to 60 minutes the first time, mostly downloading Docker images.

## What you need

| Item | Minimum | Recommended | Why |
|---|---|---|---|
| Operating system | Ubuntu 22.04 or 24.04 | same | `install.sh` refuses other systems |
| RAM | 16 GB | 24 GB | The ZAP scanner peaked at 12.8 GB during a deep scan |
| Free disk | 25 GB | 50 GB | Docker images and scan data |
| Network | needed once, to download | — | Images, Ubuntu packages and the Docker repository |

Only one scan runs at a time. Scans refuse to start if less than 14 GB of memory is free (`configs/resources.json`).

## Option A: the installer (recommended)

```
git clone <repository-url> wasra
cd wasra
./install.sh
```

`install.sh` does these things, in order:

1. Checks that the system is Ubuntu 22.04 or 24.04. Otherwise it stops with a message.
2. Reports RAM and free disk, and warns if they are below the recommended values.
3. Checks for `git`, `make`, `curl`, Python 3.12, Docker and the Docker Compose plugin. Installs whatever is missing, from Ubuntu's packages or Docker's official repository. It never runs a script downloaded from the internet.
4. Creates `.env` with random passwords, if it does not exist. An existing `.env` is never overwritten.
5. Creates the Python environment used by the tests (`.venv`).
6. Builds and starts the stack, and waits for the health endpoints.
7. Prints the addresses to open.

Other forms:

```
./install.sh --check     # report what is missing and the resource check; change nothing
./install.sh --no-start  # install and build, do not start
./install.sh             # running it again is safe: it skips what is already done
```

If Docker was just installed, log out and back in (or run `newgrp docker`) so your user can run Docker without `sudo`. The installer adds you to the `docker` group.

## Option B: by hand

```
sudo apt-get install -y git make curl python3.12 python3.12-venv
# Docker: follow https://docs.docker.com/engine/install/ubuntu/ (Docker Engine and the compose plugin)
git clone <repository-url> wasra && cd wasra
make env        # creates .env with random passwords (never overwrites it)
make venv       # Python environment for the tests
make up         # builds and starts the stack, then waits until it answers
```

## Check that it works

Open these in a browser on the same computer:

| Address | What you should see |
|---|---|
| http://127.0.0.1 | The WASRA app: the targets page, with a status panel showing Postgres, ZAP and the feed date |
| http://127.0.0.1:8080/healthz | `{"ok":true}` |
| http://127.0.0.1:3001 | The Grafana login (user `admin`, password `GRAFANA_ADMIN_PASSWORD` in `.env`) |

Then run the offline tests:

```
make test
```

Expect about 105 passed. The browser and integration tests need the stack running and are skipped by default. To run them:

```
WASRA_INTEGRATION=1 WASRA_E2E=1 make test
```

## Settings you may change at install time

All of these live in `.env` (copied from `.env.example`). Change them, then run `make up` again.

| Setting | Default | What it does |
|---|---|---|
| `AUTH_MODE` | `none` | `none`: no login (safe only because all ports are on 127.0.0.1). `basic`: the app asks for `WEB_USER` and `WEB_PASSWORD` |
| `WEB_USER`, `WEB_PASSWORD` | random | Login for the app when `AUTH_MODE=basic` |
| `GRAFANA_ADMIN_PASSWORD` | random | Login for Grafana (user `admin`) |
| `ZAP_API_KEY` | random | The key the backend uses to talk to ZAP. Only needed inside Docker and on 127.0.0.1 |
| `POSTGRES_PASSWORD`, `GRAFANA_DB_PASSWORD` | random | Database passwords. Grafana reads the database with its own read-only account |

If you set `AUTH_MODE=none`, `make up` refuses to start when any port in `docker-compose.yml` is not bound to `127.0.0.1`. That check is in `scripts/check_bindings.py`.

## If something goes wrong

| Symptom | What to do |
|---|---|
| `install.sh` says the system is unsupported | Use Ubuntu 22.04 or 24.04 |
| "permission denied" for Docker | Log out and back in, or run `newgrp docker` |
| `make up` times out waiting for the backend | Run `docker compose logs backend`. A short startup error is retried automatically (restart policy) |
| zap or webgoat shows "unhealthy" | Normal for a few minutes after start. Both still answer requests; check `docker compose ps` |
| Port 80 or 8080 already in use | Stop the other program (`ss -ltnp | grep :80`), then run `make up` again |
| Disk is full | Run `docker system df`; remove only images you do not need |

## Update to a newer version

```
git pull
make up          # rebuilds what changed and restarts it; database migrations run at startup
make test
```

Back up the database before any update that changes migrations:

```
docker compose exec -T postgres pg_dump -U wasra -d wasra > backup-$(date +%F).sql
```

## Remove it

```
make down        # stops everything, keeps data
make clean       # stops and deletes containers and volumes (all targets and scans are lost)
```
