"""raw ZAP alerts -> normalized -> enriched -> scored -> ranked. Deterministic for fixed inputs."""
from src.enrich.enrich import enrich, load_feeds
from src.normalize.normalize import normalize_all
from src.scoring.score import score_finding, load_weights
from src.triage import classify, group

METHODS = ("risk", "weighted_sum", "cvss_only", "zap_risk_only")


def run(raw_alerts: list[dict], context: dict, feeds: dict | None = None, weights: dict | None = None) -> list[dict]:
    feeds = feeds or load_feeds()
    weights = weights or load_weights()
    rows = []
    for key, alerts in group(raw_alerts).items():  # one finding per fingerprint; raw count kept
        f = enrich(normalize_all([alerts[0]])[0], feeds)
        f = {**f, "classification": classify(f), "occurrences": len(alerts),
             "fingerprint": "|".join(map(str, key))}
        rows.append({**f, **score_finding(f, context, weights), "context": context})
    for m in METHODS:  # rank per method; tie-break by id then url for determinism
        order = sorted(rows, key=lambda r: (-r[m], r["id"], r["url"]))
        for i, r in enumerate(order, 1):
            r[f"rank_{m}"] = i
    return sorted(rows, key=lambda r: r["rank_risk"])
