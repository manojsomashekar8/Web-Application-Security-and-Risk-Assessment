# Decisions

| # | Decision | Alternatives considered | Reason |
|---|----------|-------------------------|--------|
| D1 | Image pins: zaproxy/zap-stable:2.16.1, bkimminich/juice-shop:v19.0.0, postgres:16, prom/prometheus:v3.5.0, grafana/grafana:12.0.0 (tags verified with `docker manifest inspect`) | `latest` tags | Reproducibility; digests recorded in REPRODUCIBILITY.md |
| D2 | `prometheus` is not an image name; use `prom/prometheus` | - | Official image is under prom/ on Docker Hub |
| D3 | WebGoat: `webgoat/webgoat:v2026.5` (versioned tag, verified via Docker Hub tag list and manifest inspect). First attempts failed only because the `v` prefix was missing | `latest` (moves, breaks reproducibility); digest pinning is the fallback only if no versioned tag exists | Versioned tag preferred per user direction |
| D4 | DVWA: `vulnerables/web-dvwa`, bWAPP: `raesene/bwapp`, pinned by digest | - | Both resolve; used as unseen validation targets |
| D5 | Web UI: FastAPI + Jinja2 + vanilla JS (per addendum) | React/Node build | Fewer build steps, reproducible |
| D6 | PDF report: NOT implemented in phase 4. HTML + JSON only | WeasyPrint 70.0 (available on PyPI) | WeasyPrint needs system Pango/Cairo libs; adds host dependency. Revisit if required |
| D7 | Playwright pinned to 1.65.2 (PyPI) | - | Addendum requires pinned Playwright |
| D8 | Commit messages carry no AI attribution (user instruction overrides the default Co-Authored-By reminder) | Add Co-Authored-By line | User rule in prompt section 2 takes precedence |
| D9 | Host: Ubuntu 24.04.3, kernel 6.17, 12 CPU, 23 GiB RAM, Docker 29.1.3, Compose v5.0.0, Python 3.12.3 | - | Recorded from `make` target |
| D10 | ZAP web-app alerts carry no CVE IDs. CVSS/EPSS/KEV apply only where a CVE is mapped explicitly (configs/cve_map.json). All other findings use the ZAP-risk / ZAP-confidence / CWE fallbacks from SCORING.md | Pull CVEs from NVD by keyword for every finding | Keyword matching produces false CVE links; explicit mapping is auditable. Limitation must be reported in RESULTS.md |
| D11 | Feed snapshot: EPSS + KEV full files, NVD subset = CVEs listed in configs/cve_list.txt, fetched by ID. Manifest holds date and SHA-256 | Full NVD dump (large, slow) | Keeps the snapshot small and reproducible |
| D12 | Scoring config is JSON (configs/weights.json, configs/context_presets.json), not YAML | YAML | No extra dependency |
| D13 | Web UI login: HTTP Basic auth with WEB_USER / WEB_PASSWORD from .env, compared with hmac.compare_digest | Session login form | Simpler, same protection on loopback; the addendum's "simple login" is met |
| D14 | Scan allowlist is parsed from docs/TARGETS.md (`- <url> | note` lines). Server rejects any URL not listed | Separate allowlist file | Single source the user reviews |
| D15 | ZAP active scan uses default policy. Juice Shop active scan is slow (DomXss plugin ~345 s per host, full scan takes hours). Kept as is for fidelity; time is recorded in RESULTS.md | Reduced policy | Keeps scanner results comparable to the papers' setup |
| D16 | Read-only Grafana role is created by migration with a placeholder password; `make up` sets the real password from .env with ALTER ROLE | Put password in SQL file | Secrets stay out of committed files |
| D17 | Scan = new ZAP session, traditional spider, then AJAX spider (htmlunit, 10 min cap), then passive wait, then active scan. Reason: first Juice Shop run found 95 URLs and zero /rest/ or /api/ endpoints, so the active scan never tested the API (no SQLi or XSS found) | Traditional spider only; OpenAPI import (Juice Shop serves no OpenAPI document at /api-docs/swagger.json, verified) | AJAX spider is a built-in ZAP add-on present in the image; no per-target config |
| D18 | DVWA pinned to `vulnerables/web-dvwa:1.9` (versioned tag, found on Docker Hub) with digest | `latest` | Versioned tag preferred |
| D19 | bWAPP has only `latest` on Docker Hub. Pinned by digest (fallback): `raesene/bwapp:latest@sha256:2f41…600ee`, pulled 2026-11-17, no versioned tag exists | Other bWAPP images | Digest pin is the documented fallback per user direction |
| D20 | All compose images use `repo:tag@sha256:digest` form. Digests read from local pulls 2026-11-17 | tag-only | Digest makes the pin exact |
