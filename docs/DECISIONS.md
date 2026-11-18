# Decisions

This page lists the main choices we made and why. Each row says what we picked, what else we could have picked, and the reason.

| # | What we picked | Other options | Why |
|---|---|---|---|
| D1 | Specific version tags for the main tools (ZAP 2.16.1, Juice Shop v19.0.0, Postgres 16, Prometheus v3.5.0, Grafana 12.0.0) | The `latest` tag | The same setup gives the same results later |
| D2 | `prom/prometheus` as the image name | `prometheus` | That is the official image's name on Docker Hub |
| D3 | WebGoat `v2026.5` | `latest` | `latest` changes over time, which would break reproducibility |
| D4 | DVWA and bWAPP pinned by digest (a fingerprint of the exact image) | Any other copy of these apps | Both are well-known practice apps |
| D5 | Web app built with FastAPI, Jinja2 and plain JavaScript | A React app with a build step | Fewer moving parts to install and maintain |
| D6 | HTML and JSON reports only, no PDF | PDF with WeasyPrint | WeasyPrint needs extra system libraries. We can add PDF later if needed |
| D7 | Playwright pinned to 1.65.2 | Unpinned | Keeps the browser tests repeatable |
| D8 | Commit messages contain no AI attribution lines | Adding an attribution line | The project owner asked for plain commit messages |
| D9 | Recorded the machine details: Ubuntu 24.04.3, 12 CPUs, 23 GB RAM, Docker 29.1.3, Python 3.12.3 | Not recording them | Results can depend on the machine, so we note it |
| D10 | CVE severity and exploit data are only used where a CVE is matched explicitly, using `configs/cve_map.json` | Searching public databases by keyword for every finding | Keyword searches give false matches. An explicit list is easy to check |
| D11 | Saved copies of the public lists (EPSS, KEV, and a subset of NVD), with a checksum for each | The full NVD database | The full database is large and slow to download |
| D12 | Settings files in JSON | YAML | No extra library needed |
| D13 | Web app login with a username and password from `.env` | A full login page with sessions | Simpler, and still protected because the app only listens on your own computer |
| D14 | The list of allowed targets is read from `docs/TARGETS.md` | A separate allowlist file | One file for the owner to review |
| D15 | ZAP's default scan settings | A reduced scan | Keeps the results comparable to the research this project follows. The Juice Shop scan is slow with these settings, and we have not yet recorded how long it takes |
| D16 | The Grafana read-only database account is set up from `.env` when the stack starts | Putting the password in the SQL file | Keeps secrets out of committed files |
| D17 | Scan order: fresh session, normal spider, AJAX spider, passive checks, then active scan | Normal spider only | The first Juice Shop run found no API endpoints, because the normal spider can't see pages that load with JavaScript |
| D18 | DVWA pinned to `vulnerables/web-dvwa:1.9` with its digest | `latest` | Versioned tag preferred |
| D19 | bWAPP pinned by digest only | Other bWAPP images | bWAPP has no versioned tag on Docker Hub, so the digest is the only stable pin |
| D20 | Every Docker image is pinned as tag plus digest | Tag only | The digest makes the pin exact |
| D21 | Scanner URLs are stored without the default port (`http://dvwa`, not `http://dvwa:80`). The alert lookup now strips the port too | Looking up alerts with the port | Found during validation: the lookup with the port returned almost nothing. Fixed in `src/collectors/run_scan.py` |
