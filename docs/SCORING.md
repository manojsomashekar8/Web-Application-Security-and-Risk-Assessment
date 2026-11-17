# Scoring

Implementation: `src/scoring/score.py`. Weights and context presets: `configs/weights.json`, `configs/context_presets.json`. All values below were computed with that code (`tests/test_scoring.py` checks the same numbers).

## Inputs per finding

| Symbol | Meaning | Source |
|---|---|---|
| S | Severity, 0–1 | CVSS base score / 10 if the finding maps to a CVE (`configs/cve_map.json`). Otherwise ZAP risk: High 0.8, Medium 0.5, Low 0.2, Informational 0.1 |
| E | Exploitability, 0–1 | 1.0 if the CVE is in CISA KEV. Otherwise EPSS if available. Otherwise ZAP confidence: High 0.9, Medium 0.6, Low 0.3, False Positive 0.0 |
| criticality, data sensitivity, business impact | Context, per target | Low 0.33, Medium 0.66, High 1.0 |
| internet exposure | Context, per target | Low 0.33, Medium 0.66, High 1.0 (also used as Exposure) |

## Formulas

- Impact: `I = S × mean(criticality, data sensitivity, business impact)`
- Likelihood: `L = E × exposure`
- Framework risk: `Risk = 100 × L × I`, range 0–100

Baselines, for comparison only:

- CVSS-only: `100 × S`, ranked high to low. For findings without a CVE this is the ZAP-risk value.
- ZAP-risk-only: `100 × zap_risk_score`.
- Weighted sum: `100 × (0.4·S + 0.3·E + 0.3·C)`, where `C` is the mean of the four context values. Weights are equal-spec defaults and live in `configs/weights.json`.

Band for the explanation text: High ≥ 60, Medium ≥ 30, otherwise Low.

## Worked examples

Computed with the implementation.

**A. KEV-listed CVE, all context High.** CVSS 9.8, KEV true, EPSS 0.42.
- S = 0.98, E = 1.0 (KEV overrides EPSS), exposure = 1.0
- I = 0.98 × (1 + 1 + 1)/3 = 0.98
- L = 1.0 × 1.0 = 1.0
- **Risk = 98.0**, weighted sum = 99.2, CVSS-only = 98.0, ZAP-risk-only = 80.0
- Explanation: "High: KEV-listed, internet exposure High, criticality High, data sensitivity High, business impact High."

**B. No CVE, ZAP Medium risk and Medium confidence, all context Medium.**
- S = 0.5, E = 0.6, exposure = 0.66
- I = 0.5 × 0.66 = 0.33
- L = 0.6 × 0.66 = 0.396
- **Risk = 13.07**, weighted sum = 57.8, CVSS-only = 50.0, ZAP-risk-only = 50.0
- The framework ranks this finding far below the baselines. The reason is the context: a medium-exposure, medium-impact target discounts the finding. This is the intended behaviour of the product form, and it is why context changes the ranking.

**C. No CVE, ZAP Low risk and Low confidence, all context Low.**
- S = 0.2, E = 0.3, exposure = 0.33
- I = 0.2 × 0.33 = 0.066, L = 0.3 × 0.33 = 0.099
- **Risk = 0.65**, weighted sum = 26.9, CVSS-only = 20.0, ZAP-risk-only = 20.0

## Properties checked by tests

- Risk always lies in [0, 100] for random inputs (fixed seed 42, 2000 cases).
- Scoring is deterministic (same input, same output).
- Risk increases with each input: ZAP risk, ZAP confidence, and each context factor.
- Boundaries: a CVSS 10 KEV finding with all context High gives exactly 100.0. A zero-risk, zero-confidence finding with all context Low gives exactly 0.0.
- A missing or unknown context level raises an error, rather than defaulting silently.

## Known limits

- Most ZAP web-application findings have no CVE, so S and E use ZAP fallbacks. The framework's advantage over the baselines therefore comes mainly from context, not from CVE data. RESULTS.md reports how many findings in each run had a CVE.
- The framework score has no tunable weights (the product form is fixed), so the weight-sensitivity experiment varies only the weighted-sum baseline. This is stated in RESULTS.md.
