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
