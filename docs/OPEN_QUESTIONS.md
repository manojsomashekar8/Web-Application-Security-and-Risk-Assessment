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
