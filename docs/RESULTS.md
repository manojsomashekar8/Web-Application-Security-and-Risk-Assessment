# Results

## What we did

We scanned three practice websites that are built to be hacked. Each one has known security holes, so we can check whether the scanner finds them.

We ran one scan per website. The results are in `results/raw/`. The tables below are built from those raw files by `make experiments`, and the outputs are in `results/experiments/`.

## What the scanner found

| Website | Pages reached | Alerts | Known problem types found | Precision | Recall |
|---|---|---|---|---|---|
| DVWA | 71 | 775 | 2 out of 7 | 0.007 | 0.286 |
| bWAPP | 94 | 609 | 1 out of 8 | 0.028 | 0.125 |
| WebGoat | 2 | 26 | 0 out of 7 | 0.000 | 0.000 |

**What these words mean:**
- **Pages reached**: how many pages the scanner visited. More pages means a fuller scan.
- **Alerts**: the number of warnings the scanner raised.
- **Known problem types found**: how many of the website's known problem types appeared in the alerts.
- **Precision**: out of all the alerts, how many were real problems. Low means lots of noise.
- **Recall**: out of all the real problems, how many were found. Higher is better.

## Why the numbers look low

- **Lots of noise.** Most alerts are minor, like missing security headers. They are real, but they are not the big problems we are testing for.
- **WebGoat was barely scanned.** Its lessons load with JavaScript, so the scanner only saw the front page. Its zero is a coverage problem, not proof the scanner missed anything. See [Open questions](OPEN_QUESTIONS.md).
- **One run per website.** We have no repeat runs yet, so we cannot say how much the results vary.

## Limits to keep in mind

- Juice Shop was scanned earlier, in a separate run. Its raw results are kept in `results/raw/` for comparison, but they are not in the table above.
- We have not recorded how long each scan took. The full Juice Shop scan is expected to be slow.
- The experiments in `results/experiments/` depend on the scans above, so treat them as preliminary.

## Timed Juice Shop scan (scan 2, current code)

Run on 2026-11-21 with the current code, through the normal web API. The timings are also saved in `results/scan2_timings.json`.

| Stage | Duration |
|---|---|
| Spider | 20.1 s |
| AJAX spider | 145.3 s |
| Passive wait | 0.0 s |
| Active scan | 754.6 s (12 min 35 s) |
| **Scanner total** | **920 s (15 min 20 s)** |
| Wall clock, start to done (includes alert download and scoring) | 929.9 s (15 min 30 s) |

- Raw alerts stored: 1,103. Unique findings after grouping: 493.
- Top-10 overlap between the framework ranking and the CVSS-only ranking: 0.8.
- The active scan is almost all of the time. The machine was otherwise idle; load peaked near 70 while ZAP ran.
- This scan replaces the earlier pre-grouping raw file in `results/raw/juiceshop_alerts.json`. The earlier file is kept as `juiceshop_pre_grouping_alerts.json` for comparison (decision D39).


## DVWA: the three scan profiles compared (2026-11-22)

All runs against http://dvwa:80 with DVWA reset before each scan, security level low, ZAP 2.16.1. One run per profile (no repeats). Times are wall clock from the database.

| Profile | Scan | Wall time | Unique findings | Vulnerability-class findings | Top-10 overlap with deep |
|---|---|---|---|---|---|
| quick (spider with 2 min cap, passive only) | 8 | 7.4 s | 4 | 4 | 4 of 4 (all findings) |
| standard (traditional + AJAX spider, active at Low strength, time limits) | 9 | 198.5 s | 16 | 4 | 10 of 10 |
| deep (reference, uncapped) | 13 | 501.0 s | 16 | 4 | reference |

- Deep run 6 (same settings, before the profile code existed) took 689 s and found the same 16 findings.
- Measured on the deep run (scan 13, with the usage sampler): ZAP CPU peaked at 865% of one core (average 281%); ZAP memory peaked at 12.8 GB (average 8.7 GB). The backend stayed under 52 MB.
- Standard took about 2.5 times less time than deep here and produced the same 16 findings. Why the same set is reached was not tested.
- Quick is not a substitute for the others: it found 4 findings and sent no attacks.
- The "vulnerability-class" count is the number of findings classified as vulnerability (ZAP-reported, not proven). It is not detection recall; see the validation tables for that.

Earlier failures, kept as history: scans 10 and 11 failed while ZAP was restarting; scan 12 failed after the 8 GB memory cap was applied to ZAP (ZAP reached 7.8 GiB of 8 GiB and timed out). See decision D57.
