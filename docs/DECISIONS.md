# Decisions

Each row says what we picked, what else we could have picked, and why.

| # | What we picked | Other options | Why |
|---|---|---|---|
| D1 | Specific version tags for the main tools (ZAP 2.16.1, Juice Shop v19.0.0, Postgres 16, Prometheus v3.5.0, Grafana 12.0.0) | The `latest` tag | The same setup gives the same results later |
| D2 | `prom/prometheus` as the image name | `prometheus` | That is the official image's name on Docker Hub |
| D3 | WebGoat `v2026.5` | `latest` | `latest` changes over time, which would break reproducibility |
| D4 | DVWA and bWAPP pinned by digest (a fingerprint of the exact image) | Any other copy of these apps | Both are well-known practice apps |
| D5 | Original web pages built with FastAPI, Jinja2 and plain JavaScript | A React app with a build step | Fewer moving parts. Kept as a fallback next to the React app |
| D6 | HTML and JSON reports only, no PDF | PDF with WeasyPrint | WeasyPrint needs extra system libraries. Add later if needed |
| D7 | Playwright pinned to 1.65.2 | Unpinned | Keeps the browser tests repeatable |
| D8 | Commit messages contain no AI attribution lines | Adding an attribution line | The project owner asked for plain commit messages |
| D9 | Machine details recorded: Ubuntu 24.04.3, 12 CPUs, 23 GB RAM, Docker 29.1.3, Python 3.12.3 | Not recording them | Results can depend on the machine |
| D10 | CVE severity and exploit data only where a CVE is matched explicitly in `configs/cve_map.json` | Keyword search of public databases for every finding | Keyword searches give false matches. An explicit list is easy to check |
| D11 | Saved copies of public lists (EPSS, KEV, subset of NVD), each with a checksum | The full NVD database | The full database is large and slow to download |
| D12 | Settings files in JSON | YAML | No extra library needed |
| D13 | Web login with a username and password from `.env` | A full login form with sessions | Simpler. Still protected because services only listen on your own computer |
| D14 | Allowed targets read from `docs/TARGETS.md` | A separate allowlist file | One file the owner can review |
| D15 | ZAP's default scan settings | A reduced scan | Keeps results comparable to the research this project follows. The Juice Shop scan is slow; its time is not yet recorded |
| D16 | The Grafana read-only database account is set up from `.env` at startup | Putting the password in the SQL file | Keeps secrets out of committed files |
| D17 | Scan order: fresh session, normal spider, AJAX spider, passive checks, active scan | Normal spider only | The normal spider cannot see JavaScript-only pages, so the first Juice Shop run found no API endpoints |
| D18 | DVWA pinned to `vulnerables/web-dvwa:1.9` with its digest | `latest` | Versioned tag preferred |
| D19 | bWAPP pinned by digest only | Other bWAPP images | bWAPP has no versioned tag on Docker Hub |
| D20 | Every Docker image pinned as tag plus digest | Tag only | The digest makes the pin exact |
| D21 | Scanner URLs stored without the default port (`http://dvwa`, not `http://dvwa:80`). The alert lookup strips the port too | Looking up alerts with the port | Found in validation: the lookup returned almost nothing. Fixed in `src/collectors/run_scan.py` |
| D22 | New frontend: React 18 with Vite, served by nginx in its own container on port 80. nginx forwards `/api` to the backend and passes the login through | Server-rendered pages only; a Node server | Gives a real app UI, and the static build is small. The backend still checks the login, so nginx stays simple |
| D23 | Frontend versions pinned (React 18.3.1, React Router 6.28.0, Vite 5.4.11, plugin-react 4.3.4), with a lock file | Latest versions | Repeatable builds. All are well over two weeks old |
| D24 | Alert classification from ZAP risk and confidence: `vulnerability`, `potential`, `informational`, `excluded` | Calling every ZAP alert a vulnerability | ZAP does not prove exploitability. Informational notes must not look like vulnerabilities (review P1) |
| D25 | Repeated alerts merged when plugin ID, URL path (no query), parameter and attack match. Raw count kept | Merging by plugin ID alone | Different parameters are different problems. Merging by ID alone would hide them |
| D26 | Rankings: each method sorts by its own score. Exact ties are broken by plugin ID then URL | Breaking ties by input order | Input order is not a reason. The review allows deterministic tie-breaks only for exact ties |
| D27 | The explanation is built from the same numbers as the score and label, and names the main limiting factor | Listing the context values only | The old text listed High context values next to a Low label with no reason. The new text shows the arithmetic and the threshold |
| D28 | Old stored findings re-classified by a migration from their stored ZAP risk and confidence | Re-running every old scan | Classification depends only on those two fields, so no scan is needed. Repeats in old scans are not merged, because the raw alerts were not stored per finding |
| D29 | Dashboards provisioned from files in `grafana/provisioning/`, loaded at Grafana startup | Creating dashboards by hand in the UI | Repeatable and reviewable. Nothing needs clicking to set up |
| D30 | `AUTH_MODE` = `none` (default) or `basic`. In `none`, the app skips the login, and `make up` refuses to start if any published port is not bound to 127.0.0.1 (`scripts/check_bindings.py`, tested) | A login in every mode | The app cannot see host port bindings, so the check runs before the stack starts. Basic mode keeps the constant-time credential check |
| D31 | Feed snapshot is "fresh" for 30 days, then "stale" in the status panel | No threshold | A simple, visible rule. The number is a judgement call and can be changed in `src/health.py` |
| D32 | Feed files that are missing, unreadable or have a wrong header log a warning; their values become n/a and the scan continues. Each value stores its feed name, file, snapshot date and status | Stopping the scan on any feed error | A failed feed should not hide a whole scan. Provenance makes the gap visible |
| D33 | `enrichment_na` is true when the finding has no CVSS value. This drives the "findings with n/a enrichment" panel | Counting any missing field | CVSS is the field the severity term needs; one number keeps the panel readable |
| D34 | Stage timings (spider, AJAX spider, passive wait, active scan), raw alerts and top-10 overlap are stored per scan | Timing only in logs | Lets Grafana and the results page show durations, and lets a scan be re-scored without a new scan |
| D35 | Re-score recomputes findings from the stored raw alerts with the target's current context, in one transaction. Scans without stored raw alerts return 409 | Re-running ZAP | ZAP is slow and heavy. Scoring is pure and fast |
| D36 | Grafana overview has a `target` variable (multi-select, default all) and four new panels: framework band counts, stage durations, n/a enrichment count, and top-10 overlap | Separate dashboards per target | One overview with a filter keeps the set small. All panels are still provisioned from files |
| D37 | Every experiment writes a CSV beside its JSON. Nested values are stored as JSON text so each table is flat | Separate CSV scripts | One place generates the CSV, so the two files cannot disagree |
| D38 | Deduplication experiment (`exp6_dedup`) reports raw versus unique counts, the largest group, and distinct path and parameter pairs | Only the unit test | The review asked for a measured result on real scan data |
| D39 | The Juice Shop scan was run again with the current code. The old raw file was kept as `juiceshop_pre_grouping_alerts.json`, and the old scan 1 row was left in the database. Scan 2 is the replacement for analysis | Deleting the old scan | Keeps the earlier data for comparison; nothing was overwritten without a copy |
| D40 | Before `make reproduce`, the database was dumped to `~/backups/`. `make reproduce` runs `make clean`, which deletes the Postgres volume | Running it without a backup | `make clean` removes all stored targets and scans |
| D41 | The React app keeps the basic-auth credentials in memory only, never in localStorage | Browser storage | Memory is cleared on reload; nothing is left on disk in the browser |
