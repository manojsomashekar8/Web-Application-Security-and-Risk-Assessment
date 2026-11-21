# User interface guide

The main interface is the React app at http://127.0.0.1 (port 80). The original server-rendered pages are on port 8080 and are kept as a fallback.

## Login

The server sets the mode with `AUTH_MODE` in `.env`:

- `none` (default): no login. This is safe only because every port is bound to 127.0.0.1. The stack refuses to start if any port is bound elsewhere.
- `basic`: the app shows a login form. Your username and password are kept in memory only and sent as an `Authorization` header with each request. They are not stored in the browser. Reloading the page asks you to log in again.

## Screens

| Screen | Route | What you do |
|---|---|---|
| Targets | `/` | See every target and its latest scan status. The system status panel shows whether Postgres, ZAP and the feed snapshot are healthy |
| Add target | `/targets/new` | Pick a website from the allowlist and rate the four business-context factors |
| Target | `/targets/:id` | See the context, start a scan, open the latest results |
| Scan results | `/scans/:id` | Read the summary, filter the findings, expand a row for the explanation, re-score, or download the JSON report |

## Scan results, in order

1. **Summary cards.** Raw alerts (what the scanner reported) and unique findings (after merging repeats), plus High, Medium and Low counts from the framework score.
2. **Classification.** Vulnerability, potential, informational and excluded counts. Click one to filter the table.
3. **Filters.** Class and risk band.
4. **Table.** Rank, finding, class, risk score, band, ZAP risk, confidence, CVSS, EPSS, KEV and count. A missing value shows as "n/a", never 0.
5. **Expanded row.** The explanation built from the score's own numbers, the severity and exploitability inputs, the internet exposure, and the rank under each of the four methods.

## Re-score

The **Re-score** button recomputes the findings from the scan's stored raw alerts, using the target's current context. No new scan starts. This is useful after you change a business-context rating. It works only for scans that stored their raw alerts, which is every scan run after that storage was added. Older scans show a clear message to run a new scan.

## Accessibility and layout

- Works at phone width (390 px): the page has no horizontal scroll, and tables scroll inside their own box.
- Light and dark colours follow the system setting.
- Missing values are written as text ("n/a"), not shown by colour alone.
- Status badges combine a word and a colour.

## Errors you may see

| Message | Meaning | What to do |
|---|---|---|
| "Wrong username or password, or login required." | Basic mode and the credentials are wrong or missing | Log in again |
| "422" with "allowlist" | The website is not on `docs/TARGETS.md` | Use an allowed site |
| "409: this scan has no stored raw alerts" | Re-score on an old scan | Run a new scan |
| Status panel shows ZAP or Postgres as failed | The service is down or not ready | Run `docker compose ps`, then `make up` |
