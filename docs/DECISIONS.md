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
