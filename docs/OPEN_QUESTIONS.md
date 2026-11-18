# Open questions

1. PDF report: not built. Default used: HTML + JSON only (D6). Reply if you need PDF.
2. Grafana admin and web-UI login passwords: read from .env (not committed). Default used: .env.example holds placeholders; `make up` refuses to start if they are unset.
3. WebGoat tag: `latest` is the only resolving tag. Default used: pin by digest (D3).

## Validation scan coverage (blocker)

- Symptom: the DVWA, WebGoat and bWAPP scans reached only 1-2 URLs each. Alerts are almost all informational headers, so experiments 1-5 detect 0 known classes.
- Checked: the session cookies are seeded correctly. An authenticated spider with the same cookie still finds only the root URL, while the root page contains relative links.
- Not yet checked: whether ZAP's replacer rule is applied to spider requests, and whether the spider sees the logged-in page.
- Until fixed: experiment results are not valid and were not committed. Raw alerts in results/raw/ are partial.
