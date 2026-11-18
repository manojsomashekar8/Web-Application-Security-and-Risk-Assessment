# Results

Generated from `results/raw/` by `make experiments`. Raw outputs and hashes are in `results/experiments/`.

## Validation scans (ZAP, authenticated, one run each)

| Target | URLs covered | Alerts | Known classes detected | Precision | Recall |
|---|---|---|---|---|---|
| DVWA | 71 | 775 | 2 / 7 | 0.007 | 0.286 |
| bWAPP | 94 | 609 | 1 / 8 | 0.028 | 0.125 |
| WebGoat | 2 | 26 | 0 / 7 | 0.000 | 0.000 |

Precision and recall are against the class mapping in `configs/ground_truth.json`. They are low because ZAP reports many informational and header findings that are not in the ground truth.

## Limits

- WebGoat is a client-side single-page app. The server-side spider reaches only the root page, so its numbers reflect coverage, not detection. See `docs/OPEN_QUESTIONS.md`.
- Each target was scanned once. No repeat runs, so no variance estimate yet.
- Juice Shop raw alerts from the first scan are kept for comparison (`results/raw/juiceshop_*`), but they are not in the validation table above.

## Experiments

Experiments 1 to 5 are written to `results/experiments/` (detection, ranking, context, weights, ablation). Their numbers depend on the scan coverage above, so treat the WebGoat rows as invalid until its coverage is fixed.
