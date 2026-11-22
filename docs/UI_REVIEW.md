# UI review (2026-11-22)

Screenshots are in `docs/screenshots/`. They were taken with Playwright at 1280 px wide against DVWA scan 6 (16 findings, deep profile, ZAP 2.16.1).

## What each screen shows

**Targets** (`targets.png`): one card per target with its name, URL, criticality and exposure, and a status badge. A system-status panel sits above the cards (Postgres, ZAP version, feed snapshot age).

**DVWA target** (`target_dvwa.png`): the four business-context ratings (all High), the latest scan status (done), and two buttons: Start scan and Open latest results. There is no profile selector yet, so every scan is the deep profile.

**Scan 6 results, collapsed** (`scan6_collapsed.png`): summary cards (16 raw alerts, 16 unique findings, 0 High, 2 Medium, 14 Low), classification counts (4 vulnerability, 0 potential, 12 informational, 0 excluded), class and band filters, and a 16-row table.

**Scan 6 results, first row expanded** (`scan6_expanded.png`): the explanation text, then Severity (S), Exploitability (E), Internet exposure, Impact (I), Likelihood (L), Severity used (S) with its source, CVE, CWE, OWASP category, and the rank under each of the three comparison methods.

## Why CVSS shows "n/a"

It is missing in the data, not in the display.

1. `configs/cve_map.json` has **no entries**. It maps ZAP plugin ids to CVE ids, and it is empty.
2. Without a CVE, `enrich()` sets CVSS, EPSS and KEV to None. Provenance records the status `no_cve`.
3. Scan 6 has 16 findings and none has a CVE. Scan 2 (Juice Shop) has 439 findings and none has a CVE either (checked in Postgres).
4. The frontend prints "n/a" for any null value (`frontend/src/components.jsx`, `Value`). So the "n/a" is correct for the data we hold.

We do not invent CVSS values. CVSS belongs to a CVE, and most ZAP web findings (missing headers, for example) have none.

## Problems found and what was done

| # | Problem | Status |
|---|---|---|
| 1 | Column says "CVSS", which suggests the scanner measured it | Fixed: columns are "CVSS (from CVE)", "EPSS (from CVE)", "KEV (from CVE)". Each n/a has a tooltip with the reason (`naTitle`) |
| 2 | The score's severity source is not visible in the table | Fixed in the expanded row: "Severity used (S)" shows `0.50 (ZAP risk Medium)` or `(CVSS x.x)`. CWE and OWASP are shown there too. The table itself still omits CWE and OWASP (not done) |
| 3 | KEV printed "no" for findings with no CVE, which implies the KEV list was checked | Fixed: KEV is n/a when no CVE is mapped (decision D54). The test was updated |
| 4 | Twelve "User Agent Fuzzer" rows look identical in the table | Not changed. They are separate alerts with different parameters or attacks, so grouping keeps them apart by design (D25). The table should show the parameter column; not done yet |
| 5 | Every scan uses the same settings; the user cannot choose a profile | Planned (Task 1). Profile validation is written and tested; the UI is not |
| 6 | The Juice Shop and DVWA results pages show no scan settings or timings | Planned (Tasks 1 and 7) |
| 7 | The table sorts only by rank; other columns are not sortable | Planned (Task 2) |
| 8 | There is no per-finding download | Planned (Task 2) |
| 9 | The results page reads "Re-score" and "Download JSON report", but there is no HTML download | Planned (Task 2) |
| 10 | The target page does not show DVWA's security level | Planned (Task 3) |

## Layout notes

- The results table is wide (11 columns). It scrolls sideways inside its box on a phone (checked earlier, no page-level scroll).
- Headers for the three CVE columns wrap onto three lines. Acceptable, but a shorter label ("CVE data") would read faster.
- The class and band filters are above the table, and the counts they show match the table.
