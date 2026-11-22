# Open questions

What is still unresolved, and what is needed to settle each item.

## 1. WebGoat coverage

**Problem:** the scanner reached only 2 pages on WebGoat, so its results say nothing about detection.

**Why:** WebGoat is a single-page app. Its lessons load through JavaScript after the front page, and the scanner's spider cannot find them. The login cookie works.

**Options:** start the scan from WebGoat's API endpoints, or report WebGoat as "coverage too low to judge" and leave it out of comparisons.

**Needed:** a decision on which option to take.

## 2. Juice Shop scan time

**Problem:** the full Juice Shop scan has not been timed. The end-to-end test waits up to one hour.

**Needed:** one timed run, with the time for each stage recorded.

## 3. Enrichment provenance and failures (review P1)

**Problem:** the pipeline does not yet record where each CVSS, EPSS and KEV value came from (which feed file and date). If a feed file is missing, the whole scan fails instead of continuing without that enrichment.

**Needed:** record the feed name and snapshot date on each finding, and make a missing feed produce "n/a" values instead of stopping the scan.

## 4. Deduplication test (review recommendation)

**Problem:** grouping works and has unit tests, but there is no experiment that compares raw versus unique counts on a scan with known repeats.

**Needed:** add the deduplication experiment to `src/experiments/run.py`.

## 5. Older scan not regrouped

**Problem:** scan 1 (Juice Shop) was stored before grouping existed. Its 13 rows are classified correctly now, but its repeated alerts were not merged, so its "raw" and "unique" counts are equal.

**Needed:** re-run the scan with the current code, or accept scan 1 as the pre-grouping baseline and say so in the results.

## 6. Pushing commits to GitHub

**Problem:** the local commits have not all been pushed. The GitHub account on this machine cannot write to the project's repository.

**Needed:** push access for this account, or the owner pushing the commits.

## 7. Missing documents

`TEST_PLAN.md`, `UI.md`, `LITERATURE.md` and `REPRODUCIBILITY.md` have not been written.

## make reproduce attempt 5: Docker stopped during the final scan

- What happened: all tests passed (91 unit and browser, 8 integration). The last step, the Juice Shop scan through the CLI, failed because the Docker daemon stopped at 19:07:47 (systemd: docker.service deactivated, not started again). The CLI then received no JSON and exited with an error. The report and the reproducibility file were not written.
- Cause: not known from the logs. Nothing in this session stopped Docker. The daemon was stopped by systemd, so it may have been stopped by hand or by a system action.
- Default used: do not restart Docker or rerun the whole reproduce without your go-ahead, because a restart may be unwanted.
- Needed: confirm whether Docker should be running. If yes, the default next step is `sudo systemctl start docker`, then `make up`, then the final scan and report steps (`make scan-dvwa`, `make report`, `scripts/gen_reproducibility.py`).
- The database backup from before the reproduce runs is at ~/backups/wasra-before-rescan.sql.

## Unseen validation target (Task 3)

- Now that DVWA is the target we tune and develop on, no validation target stays unseen unless bWAPP is kept apart.
- Default used: bWAPP stays the unseen validation target. Nothing is tuned on it, and its scans are not used to choose settings.
- Needed: confirm this default, or name another unseen target.


## Final state (2026-11-22)

- Resolved since the earlier entries: scan coverage for DVWA and bWAPP (the port fix), the Juice Shop timing (measured), the backend crash during startup (restart policy, D59), and the frontend nginx startup race (per-request resolution, D60).
- CVE mapping: `configs/cve_map.json` is still empty, so CVSS, EPSS and KEV are n/a for every finding. Default used: show n/a with the reason, never invent values. Needed: a reviewed mapping.
- Client Spider: not active in the installed ZAP image. Default used: AJAX spider (D52). Needed: confirm the Client Side Integration add-on loads.
- Memory cap on ZAP: the 8 GB cap made a deep scan fail. Default used: no cap (D57). The measured peak is 12.8 GB; the free-memory check requires 14 GB (D58).
- Usage sampling runs only when `scripts/sample_usage.py` is started alongside a scan. A scan started from the web app is not sampled automatically. Default used: sample from the script. Needed: start the sampler from the backend, or accept unsampled UI scans.
- Scans 10 and 11 failed while ZAP was restarting, and scan 12 failed under the memory cap. They are kept as history.

## CVE values (CVSS, EPSS, KEV) are n/a for every finding

- What is true: `configs/cve_map.json` is empty, and `data/feeds/nvd_subset.json` has 0 entries. No stored alert names a CVE. The only ZAP rule that normally carries CVEs is "Vulnerable JS Library (Powered by Retire.js)" (plugin 10003). It is loaded and enabled in the container. None of the stored scans (DVWA, Juice Shop, WebGoat, bWAPP) produced a 10003 alert, so there is no finding to map.
- Why this is not a display bug: CVSS, EPSS and KEV belong to CVEs. Most ZAP web findings (missing headers, CSP, server version leaks) have no CVE, so n/a is correct for them.
- What a real fix needs, in order: (1) a target whose pages load an old JavaScript library, so the Retire.js rule fires, and a stored sample of that alert to see its format; (2) a parser that reads the library name and version from that alert; (3) CVE lookup for that library version from a public source (OSV or NVD, fetched once, with the date and checksum recorded); (4) NVD subset filled with those CVEs, plus EPSS and KEV for them from the existing snapshots; (5) a per-finding mapping, because the CVE depends on the version, not just the plugin id (the current `cve_map.json` is keyed by plugin id only, so it cannot express this).
- Default used: keep n/a with the reason shown, and do not fill `cve_map.json` by hand. Needed: confirm that a vulnerable-library target may be added to the scan list (it would be a new target, so it needs your approval), or name a target you already have.

## CVE values: check result (2026-11-22)

- Ran the approved quick check on DVWA (scan 10, ZAP 2.16.1). Plugin 10003 did not fire. Result, raw alerts and settings are in `results/checks/dvwa-quick-10003/` and docs/RESULTS.md.
- The quick profile does not reach library-loading pages, so this does not show that DVWA is free of an old library.
- Default used: keep n/a with the reason (D61). No mapping was added.
- Needed: approval for a standard or deep scan of DVWA, which reaches more pages, to see whether 10003 fires. If it does, the parsing and CVE steps in the previous entry follow.
- Also needed: scans from before this change have no ZAP version and no settings (the re-imported raw scans are labelled "unrecorded"). Default used: keep them labelled that way.

## Earlier scans ran with a failing AJAX spider (found 2026-11-22)

- The AJAX browser (HtmlUnit) failed through ZAP's proxy (`HTTP/1.0 0`, root cause: ZAP's history database closed). In a failing scan the AJAX stage takes about 5 s instead of minutes. The fix is D67. Scan 15 is the first AJAX stage to run long with no proxy errors.
- **Scans that ran with a failing AJAX stage (about 5 s):** the DVWA deep scans 1 to 9 from the reproduce runs (all AJAX stages 5.0 s), scan 13 (AJAX 5.0 s), and scan 14 (AJAX 5.0 s). Any claim that these scans reached JavaScript-only pages is unsupported.
- **Scan that ran long (AJAX 135 s) and was not affected:** scan 6, the DVWA deep scan before profiles (135.2 s). Its AJAX stage worked as far as the time shows; its URL count was not stored.
- **Juice Shop timed run (scan 2, earlier):** the AJAX stage took 145.3 s, which suggests it worked, but no URL count was stored, so this is not verified.
- **Documents that describe AJAX results and need to be checked against this:**
  - `docs/RESULTS.md`: the timed Juice Shop run table (AJAX 145.3 s); the profile comparison (standard 10 of 10 overlap and deep reference, both DVWA runs with a failing AJAX stage); the passive scan 14 section (correctly marked as failed).
  - `docs/RESULTS.md` and `docs/WHAT_WAS_DONE.md`: WebGoat "2 pages" coverage result. Its AJAX stage is not recorded, so the cause of the 2 pages is unknown (the earlier explanation, that WebGoat is a single-page app, is not verified).
  - `EXPLAIN.md` section 4 ("Why several spiders?"): the statement that the AJAX spider finds the JavaScript pages describes the intended design. The example "first run on Juice Shop found 95 pages but no API endpoints" is from an earlier run with an unrecorded AJAX state.
  - `EXPLAIN.md` section 6 and `docs/RESULTS.md` Juice Shop numbers (raw alerts, unique findings, top-10 overlap): these come from the raw files, not from the AJAX stage, so they stand; the claims about what the scanner reached do not.
- **Needed:** decide whether to re-run the affected scans with the fixed browser (a large change, needs your approval). Default used: keep the numbers, mark them as produced with a failing AJAX stage, and do not re-run.
