# Using WASRA

This guide covers the daily workflow and every setting you can choose. For how the score works, read [EXPLAIN.md](../EXPLAIN.md).

Open the app at **http://127.0.0.1** (port 80).

## 1. Add a target

Only sites on the allowlist can be scanned.

1. Open **Add target**.
2. Choose the website from the list. The list comes from `docs/TARGETS.md`.
3. Give it a name and rate the four business ratings (see the table below).
4. Click **Save target**. You land on the target page.

To allow a new site, add a line to `docs/TARGETS.md` in the format `- http://host:port | note`. The list is read on every request, so no restart is needed. Only add sites you are allowed to test.

### The four business ratings

| Rating | Question it answers | Low / Medium / High counts as |
|---|---|---|
| Criticality | How important is the app to the business? | Low 0.33, Medium 0.66, High 1.0 |
| Data sensitivity | What data does it hold? | same |
| Internet exposure | Can anyone on the internet reach it? | same |
| Business impact | What happens if it is compromised? | same |

These ratings change the score. Re-score a finished scan after changing them (see section 4).

## 2. Choose a scan profile

On the target page, pick a profile and click **Start scan**.

| Profile | What it does | Attacks? | DVWA time measured | Use it for |
|---|---|---|---|---|
| **quick** | Traditional spider, 2-minute cap, passive checks only | No | 7 s | A first look, or a smoke test |
| **standard** | Traditional spider, AJAX spider (5 min), active scan at Low strength, MEDIUM alert threshold, 60-minute cap, 5-minute cap per rule, 8 threads per host | Yes | 3 min 18 s | Regular scans where time matters |
| **deep** | Traditional spider and AJAX spider (10 min), active scan at ZAP's default strength and threshold, no limits, 24 threads | Yes | 8 min 21 s | The reference scan |
| **custom** | Your own values, from the form below | Depends | — | Experiments |

Times are from DVWA on the development machine; yours will differ.

## 3. Custom settings

Choose **custom** to show the form. Every field is checked by the server. A value outside its range is refused with a message naming the field, and no scan starts.

| Field | Choices or range | Default in the form | What it changes |
|---|---|---|---|
| Spider | traditional, AJAX, none | traditional | Which spider runs first. "none" skips spidering (the scan only sees what the active scan finds from the start page) |
| Active scan | on, off | on | Whether attack checks run. Off gives a passive-only scan |
| Attack strength | LOW, MEDIUM, HIGH, DEFAULT | DEFAULT | How hard each attack check tries. LOW sends the fewest attacks. INSANE is not offered |
| Alert threshold | OFF, LOW, MEDIUM, HIGH, DEFAULT | DEFAULT | Minimum confidence of an alert ZAP reports. HIGH keeps only the most certain alerts |
| Threads per host | 1 to 24 | 24 | Parallel requests to the site. Fewer is gentler on the site and on your computer |
| Delay between requests | 0 to 2000 ms | 0 | Pause between requests. Use it for fragile sites |
| Max scan minutes | 1 to 240 | 60 | Stops the active scan after this long |
| Max rule minutes | 1 to 60 | 5 | Stops any single check after this long |
| Excluded URL patterns | up to 20 patterns, each up to 200 characters, one per line | none | Regular expressions. Matching URLs are skipped by the spider and the active scan. Example: `.*logout.*` |
| Rule ids to disable | up to 100 numeric ZAP plugin ids, comma-separated | none | Turns off specific checks. Find ids in the alert list of a scan |

**Settings that are not offered, on purpose:** INSANE attack strength, and "no limit" for the active scan duration. Both can run for many hours.

**Settings that are fixed and cannot be changed from the app:** the DVWA reset and its low security level (see docs/TARGETS.md), the request for the ZAP report, and the free-memory check.

### Presets for common cases

| Goal | Settings |
|---|---|
| Quick check of a new site, no attacks | profile **quick** |
| Attacks but gentle on a fragile site | custom: spider traditional, active on, strength LOW, threads 2, delay 500 ms, max scan minutes 30 |
| Skip logout pages and static files | custom: excluded URLs `.*logout.*` and `.*\.(png|jpg|css|js)$` |
| Ignore one known-noisy check | custom: rule ids to disable (for example `10038`) |

## 4. Read the results

The results page starts with the settings used and the time each stage took, then the summary. Read it top to bottom:

1. **Summary.** Raw alerts (every alert ZAP raised) and unique findings (repeats merged). High, Medium and Low counts come from the risk score.
2. **Classification.** Vulnerability, potential, informational, excluded. Click one to filter the table.
3. **Table.** Sort by any column by clicking its header; click again to reverse. Default is framework risk, highest first.
4. **Expand a row** to see why it got its score.
5. **n/a** means the value does not exist for that finding. Hover over it for the reason. It is never 0.

## 5. Download reports

| Button | What you get | Made by |
|---|---|---|
| ZAP report (HTML) | ZAP's own report for the whole scan | ZAP (shown only when one was stored) |
| Full report (HTML) | All findings, with links to each finding's report | WASRA |
| Full report (JSON) | The same data as JSON | WASRA |
| Findings (CSV) | The table for a spreadsheet | WASRA |
| HTML and JSON (in a finding row) | One finding: description, solution, references, evidence, scores, ranks | WASRA |

Downloads work in both login modes.

## 6. Re-score

Click **Re-score** to recompute every finding of a scan from its stored raw alerts, using the target's current ratings. No new scan starts. It works only for scans that stored their raw alerts (scans from after that change). Older scans show a message saying so.

## 7. Export and import

Share a finished scan with another copy of WASRA:

```
python scripts/export_scan.py SCAN_ID                # writes results/exports/wasra-scan-SCAN_ID.json
python scripts/import_scan.py path/to/file.json      # creates a new scan; nothing is scanned
```

- The file format is `wasra-scan`, version 1. Other versions are refused.
- Files over 25 MB are refused.
- Imported scores are recomputed. Scores in the file are not trusted.
- The imported target must be on the allowlist.
- Importing the same file twice is refused.

## 8. Settings in the configuration files

Most users never need to touch these. Edit them, then run `make up` (or restart the backend).

| File | What it sets | Default |
|---|---|---|
| `configs/scan_profiles.json` | The four profiles above | as shown in section 2 |
| `configs/resources.json` | `min_mem_available_mb`: scans refuse to start below this free memory | 14000 (MB) |
| `configs/validation.json` | `min_pages`: a validation run below this many pages shows "Coverage too low" | 10 |
| `configs/weights.json` | Weights of the weighted-sum comparison score (not the main score) | severity 0.4, exploitability 0.3, context 0.3 |
| `configs/context_presets.json` | Default ratings used by the experiments | all Medium |
| `configs/cve_map.json` | ZAP plugin id to CVE mapping, for CVSS, EPSS and KEV | empty (no CVEs yet) |
| `docs/TARGETS.md` | Which sites may be scanned | DVWA, Juice Shop, WebGoat, bWAPP |

## 9. Grafana time range

The overview's time-series panels use the dashboard time range, which opens at the last 6 hours. Widen it (top right) to see older scans.

## 9b. Login modes

| Mode | Set `AUTH_MODE` to | What happens |
|---|---|---|
| No login | `none` (default) | Anyone who can reach 127.0.0.1 on your computer can use the app. Ports are checked to be local-only |
| Login | `basic` | The app shows a login form. Use `WEB_USER` and `WEB_PASSWORD` from `.env`. Credentials stay in memory in the browser |

After changing `AUTH_MODE`, run `make up`.

## 10. Commands you will use

| Command | What it does |
|---|---|
| `make scan-dvwa` | The default demo scan, from the terminal |
| `make experiments` | Rebuild the experiment tables |
| `make report` | Write JSON and HTML reports for finished scans into `results/reports/` |
| `make down` / `make up` | Stop and start the stack (data is kept) |
| `make test` | Offline tests |
| `docker compose logs backend` | See backend errors |

## 11. Things that can go wrong while using it

| Message or symptom | Meaning | What to do |
|---|---|---|
| 422, "unknown profile" or a field name | A scan or import request has a bad value | Fix the value shown in the message |
| 507, "only N MB of memory is free" | Free memory is below the limit in `configs/resources.json` | Close other programs and retry |
| 409, "already exists" | A target with that website exists, or the file was imported before | Open the existing target |
| 409, "no stored raw alerts" | Re-score or export of an older scan | Run a new scan |
| A scan shows "failed" with "interrupted" | The backend stopped during the scan | Start the scan again |
| A scan shows "Read timed out" to zap | ZAP was busy or still starting | Wait for ZAP to be healthy, then start again |
| The results table is empty | The scan had no findings, or it is still running | Wait, or check the scan status |
| A download says the file is missing | The ZAP report file was removed from `results/zap-reports/` | Re-run the scan |
