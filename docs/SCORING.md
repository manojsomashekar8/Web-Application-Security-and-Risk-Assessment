# How the risk score works

## The idea in one paragraph

Every problem the scanner finds gets a score from 0 to 100. A high score means "fix this first." The score combines two questions:

- **How bad is the problem?** (severity)
- **How likely is someone to exploit it?** (exploitability, plus how exposed the website is to the internet)

The score also depends on the business: a payment website with personal data counts for more than a test site.

The code is in `src/scoring/score.py`. The settings are in `configs/weights.json` and `configs/context_presets.json`.

## The letters we use

| Letter | Meaning | Where the number comes from |
|---|---|---|
| S | Severity, 0 to 1 | If the problem has a known CVE number: its CVSS score divided by 10. Otherwise the scanner's risk level: High 0.8, Medium 0.5, Low 0.2, Informational 0.1 |
| E | Exploitability, 0 to 1 | 1.0 if the CVE is on CISA's list of actively exploited problems (KEV). Otherwise the EPSS score if we have one. Otherwise the scanner's confidence: High 0.9, Medium 0.6, Low 0.3, False Positive 0.0 |
| Context | How much the business cares, per website | Low 0.33, Medium 0.66, High 1.0 |

The context has four parts: criticality (how important the site is), data sensitivity (what data it holds), business impact (what happens if it is broken into), and internet exposure (can anyone on the internet reach it).

## The formulas

- **Impact** = S × average of (criticality, data sensitivity, business impact)
- **Likelihood** = E × internet exposure
- **Risk score** = 100 × Likelihood × Impact, so it always lands between 0 and 100

We also compute three simpler scores to compare against. They are not the main result, just a yardstick:
- **CVSS only**: 100 × S, ranked from high to low
- **Scanner risk only**: 100 × the scanner's risk level
- **Weighted sum**: 100 × (0.4 × S + 0.3 × E + 0.3 × context)

The score bands are: High is 60 or more, Medium is 30 to 59, and Low is under 30.

## Three worked examples

**A. A serious, actively exploited problem on an important site.** CVSS 9.8, on the KEV list, all context High.
- Risk score: **98.0**. This is the top priority.

**B. A medium problem with no CVE, on a medium-importance site.** Scanner risk Medium, confidence Medium, all context Medium.
- Risk score: **13.1**. The simple scores put it at 50 to 58, so the framework ranks it much lower. This is intended: a medium-importance site makes the problem less urgent.

**C. A minor problem on a low-importance site.** Scanner risk Low, confidence Low, all context Low.
- Risk score: **0.65**. Close to nothing.

## Checks the code runs automatically

- The score is always between 0 and 100 (tested with 2000 random inputs).
- The same input always gives the same score.
- Raising any input never lowers the score.
- Edge cases work: the worst possible problem scores exactly 100, and the harmless one scores exactly 0.
- A missing or unknown context value stops with an error instead of guessing.

## Limits to know about

- Most web scanner findings have no CVE number. For those, the score relies on the scanner's own levels, so the context matters more than the CVE data.
- The main formula has fixed weights. The weight experiment only changes the weighted-sum comparison score, not the main score.
