# Allowed scan targets

## What this file is

The scanner only scans websites listed here. The server checks every scan against this list, whatever scan profile is chosen.

Each line is one website, in the format `- <url> | <note>`. The app reads this file directly, so keep the format.

## The list

- http://dvwa:80 | **Default demo target.** DVWA (Damn Vulnerable Web Application), project-internal Docker network. Security level: **low** (set by the login helper on every scan; see below).
- http://juice-shop:3000 | Development target (OWASP Juice Shop), project-internal Docker network. Kept for history. No new Juice Shop scans are planned.
- http://webgoat:8080/WebGoat/ | Validation target (OWASP WebGoat), project-internal Docker network. Its single-page app is barely reachable by the scanner (see docs/OPEN_QUESTIONS.md).
- http://bwapp:80 | Validation target (bWAPP), project-internal Docker network. Kept as the unseen validation target: tuning is done on DVWA, not on bWAPP.

## DVWA: database reset and security level

- Before each scan of DVWA, the login helper (`src/collectors/auth.py`, `dvwa`) runs DVWA's own "Create / Reset Database" from `/setup.php`, then logs in as the public default account (`admin`) and sets the cookie `security=low`. A scan therefore starts from a clean database and the low security level, and an earlier scan does not change the next one.
- The security level is set through the cookie on every request, so it is not left at whatever a previous run chose.
- The DVWA login and reset run inside the Docker network only.

## Adding a site

Add a line in the same format. Only add sites you own or have written permission to test.

## Validation target settings (2026-11-22)

- **WebGoat** (`http://webgoat:8080/WebGoat/`, image `webgoat/webgoat:v2026.5`): the login helper registers the account `wasrascan` (password set in code, public lab value) and logs in before each scan. Login is confirmed by the logout link on `/WebGoat/start.mvc`. Lessons are a single-page app. Business ratings used for scans: High for all four.
- **bWAPP** (`http://bwapp:80`, image `raesene/bwapp:latest` pinned by digest): the database is installed. The login helper logs in as the public lab user `bee` with `security_level=0` (low). Login is confirmed by the logout link on `/portal.php`. Business ratings: High for all four.
- Both are validation targets. Nothing is tuned on their results.

## Matrix results

- WebGoat and bWAPP: every profile was run once. Files: `results/validation/webgoat/` and `results/validation/bwapp/`. Table and notes: docs/RESULTS.md.
- DVWA: not part of the matrix. Its earlier API scans have start-page-only alert lists (see docs/OPEN_QUESTIONS.md).
