# Allowed scan targets

## What this file is

The scanner only scans websites listed here. Anything else is refused by the server.

Each line is one website. The part after the `|` says why it is on the list.

## The list

- http://juice-shop:3000 | Development target (OWASP Juice Shop), project-internal Docker network.
- http://dvwa:80 | Validation target (DVWA), project-internal Docker network.
- http://webgoat:8080/WebGoat/ | Validation target (OWASP WebGoat), project-internal Docker network.
- http://bwapp:80 | Validation target (bWAPP), project-internal Docker network.

## Adding a site

Add a new line in the same format. Only add sites you own or have written permission to test.
