# Allowed scan targets

Only the targets below may be scanned. Each line is read by the app (src/service.py). Format: `- <url>` followed by ` | <authorization note>`.

- http://juice-shop:3000 | Development target (OWASP Juice Shop), project-internal Docker network.
- http://dvwa:80 | Validation target (DVWA), project-internal Docker network.
- http://webgoat:8080/WebGoat/ | Validation target (OWASP WebGoat), project-internal Docker network.
- http://bwapp:80 | Validation target (bWAPP), project-internal Docker network.
