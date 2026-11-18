# Open questions

This page lists what is still unresolved. Each item says what we know and what is needed.

## 1. PDF reports

Not built. We only make HTML and JSON reports. If you need PDF, tell us and we will add it (see [Decisions](DECISIONS.md), D6).

## 2. WebGoat coverage

**Problem:** the scanner only reached 2 pages on WebGoat, so its results show nothing useful yet.

**Why:** WebGoat is a single-page app. Its lessons load through JavaScript after the front page, and the scanner's spider cannot find them. The login cookie works, so the login itself is fine.

**Options:**
- Start the scan from the API endpoints that WebGoat uses, if we can list them.
- Or report WebGoat as "coverage too low to judge" and leave it out of the comparison.

**Decision needed:** which option to take.

## 3. Juice Shop scan time

**Problem:** we have not measured how long the full Juice Shop scan takes. The test that runs it waits up to one hour before it gives up.

**Needed:** one timed run, with the time for each stage (normal spider, AJAX spider, active scan) recorded.

## 4. Pushing commits to GitHub

**Problem:** about 30 local commits have not been pushed. The GitHub account used on this machine is not allowed to write to the project's repository.

**Needed:** either push access for this account, or the owner pushing the commits.

## 5. Missing documents

The plan lists four documents that do not exist yet: `TEST_PLAN.md`, `UI.md`, `LITERATURE.md` and `REPRODUCIBILITY.md`.
