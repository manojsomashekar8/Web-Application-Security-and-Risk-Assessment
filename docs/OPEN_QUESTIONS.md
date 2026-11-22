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
- Needed: confirm whether Docker should be running. If yes, the default next step is `sudo systemctl start docker`, then `make up`, then the final scan and report steps (`make scan-juiceshop`, `make report`, `scripts/gen_reproducibility.py`).
- The database backup from before the reproduce runs is at ~/backups/wasra-before-rescan.sql.

## Unseen validation target (Task 3)

- Now that DVWA is the target we tune and develop on, no validation target stays unseen unless bWAPP is kept apart.
- Default used: bWAPP stays the unseen validation target. Nothing is tuned on it, and its scans are not used to choose settings.
- Needed: confirm this default, or name another unseen target.
