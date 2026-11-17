"""Validation experiments 1-5 (docs/TEST_PLAN.md). Offline: reads saved raw alerts, the feed snapshot and configs.

  python -m src.experiments.run            # writes results/experiments/*.json and docs/RESULTS.md
  python -m src.experiments.run --store    # also writes detection rows to PostgreSQL (needs DATABASE_URL)
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib

from src.enrich.enrich import load_feeds
from src.normalize.normalize import normalize_all
from src.pipeline import run as run_pipeline
from src.scoring.compare import kendall_tau, top_k_overlap
from src.scoring.score import LEVEL, load_weights, risk, weighted_sum, severity, exploitability, context_values

ROOT = pathlib.Path(__file__).resolve().parents[2]
RAW = ROOT / "results" / "raw"
OUT = ROOT / "results" / "experiments"
SEED = 42  # no sampling is used; the seed is recorded so reruns are explicit
TARGETS = {  # name -> (raw alerts file stem, base URL as used by ZAP)
    "juiceshop": ("juiceshop", "http://juice-shop:3000"),
    "dvwa": ("dvwa", "http://dvwa:80"),
    "webgoat": ("webgoat", "http://webgoat:8080/WebGoat"),
    "bwapp": ("bwapp", "http://bwapp:80"),
}
DEFAULT_CTX = json.loads((ROOT / "configs" / "context_presets.json").read_text())["default"]
GT = json.loads((ROOT / "configs" / "ground_truth.json").read_text())


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_alerts(name: str) -> list[dict] | None:
    p = RAW / f"{TARGETS[name][0]}_alerts.json"
    return json.loads(p.read_text()) if p.exists() else None


def ranks(rows: list[dict], key: str) -> dict:
    return {r["id"] + "|" + r["url"]: r[key] for r in rows}


def detection(name: str, alerts: list[dict]) -> dict:
    classes = GT[TARGETS[name][1]]
    cwe_to_class = {c: cls for cls, cwes in classes.items() for c in cwes}
    norm = normalize_all(alerts)
    tp = [a for a in norm if a["cwe"] in cwe_to_class]
    detected = {cwe_to_class[a["cwe"]] for a in tp}
    return {
        "target": name, "alerts": len(norm), "true_pos_alerts": len(tp),
        "known_classes": len(classes), "detected_classes": len(detected),
        "missed_classes": sorted(set(classes) - detected),
        "precision": round(len(tp) / len(norm), 4) if norm else 0.0,
        "recall": round(len(detected) / len(classes), 4),
    }


def run_pipeline_for(alerts, ctx=None, feeds=None, weights=None):
    return run_pipeline(alerts, ctx or DEFAULT_CTX, feeds, weights)


def exp_ranking(rows: list[dict]) -> dict:
    base = ranks(rows, "rank_risk")
    out = {}
    for label, key in {"CVSS-only": "rank_cvss_only", "ZAP-risk-only": "rank_zap_risk_only",
                       "Weighted sum": "rank_weighted_sum"}.items():
        other = ranks(rows, key)
        out[label] = {"tau": round(kendall_tau(base, other), 4), "top10_overlap": round(top_k_overlap(base, other, 10), 4)}
    return out


def exp_context(alerts, feeds) -> list[dict]:
    base_rows = run_pipeline_for(alerts, DEFAULT_CTX, feeds)
    base = ranks(base_rows, "rank_risk")
    out = []
    for factor in DEFAULT_CTX:
        for level in ("Low", "High"):
            ctx = {**DEFAULT_CTX, factor: level}
            rows = run_pipeline_for(alerts, ctx, feeds)
            other = ranks(rows, "rank_risk")
            out.append({"factor": factor, "level": level,
                        "tau_vs_default": round(kendall_tau(base, other), 4),
                        "top10_overlap": round(top_k_overlap(base, other, 10), 4)})
    return out


def exp_weights(alerts, feeds, delta: float = 0.1) -> list[dict]:
    w0 = load_weights()
    base = ranks(run_pipeline_for(alerts, DEFAULT_CTX, feeds, w0), "rank_weighted_sum")
    out = []
    for k in ("S", "E", "C"):
        for sign in (-1, 1):
            w = dict(w0)
            w[k] = round(w[k] + sign * delta, 4)
            total = sum(w.values())
            w = {kk: round(v / total, 4) for kk, v in w.items()}  # renormalize to sum 1
            rows = run_pipeline_for(alerts, DEFAULT_CTX, feeds, w)
            other = ranks(rows, "rank_weighted_sum")
            out.append({"weight": k, "delta": sign * delta, "weights": w,
                        "tau_vs_default_weighted": round(kendall_tau(base, other), 4),
                        "top10_overlap": round(top_k_overlap(base, other, 10), 4)})
    # The framework score has no tunable weights (product form), so it is stable by construction.
    return out


def _risk_variant(f: dict, ctx: dict, drop: str | None) -> float:
    s, e = severity(f), exploitability(f)
    if drop == "E":
        e = 1.0
    if drop == "exposure":
        ctx = {**ctx, "internet_exposure": "High"}
    if drop == "context":
        ctx = {k: "High" for k in ctx}
    return risk(s, e, ctx)["risk"]


def exp_ablation(alerts, feeds) -> list[dict]:
    rows = run_pipeline_for(alerts, DEFAULT_CTX, feeds)
    full = {r["id"] + "|" + r["url"]: r["risk"] for r in rows}
    out = []
    for drop in ("E", "exposure", "context"):
        scores = {r["id"] + "|" + r["url"]: _risk_variant(r, DEFAULT_CTX, drop) for r in rows}
        order = sorted(scores, key=lambda k: (-scores[k], k))
        var_rank = {k: i + 1 for i, k in enumerate(order)}
        full_rank = {k: i + 1 for i, k in enumerate(sorted(full, key=lambda k: (-full[k], k)))}
        out.append({"removed": drop, "tau_vs_full": round(kendall_tau(full_rank, var_rank), 4),
                    "top10_overlap": round(top_k_overlap(full_rank, var_rank, 10), 4)})
    return out


def write(name: str, payload: dict, inputs: list[pathlib.Path]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    payload = {"experiment": name, "seed": SEED, "generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
               "inputs": {str(p.relative_to(ROOT)): sha(p) for p in inputs},
               "config": {"weights": load_weights(), "default_context": DEFAULT_CTX}, "output": payload}
    (OUT / f"{name}.json").write_text(json.dumps(payload, indent=2, sort_keys=True))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", action="store_true")
    args = ap.parse_args()
    feeds = load_feeds()
    feed_inputs = [ROOT / "data" / "feeds" / "epss.csv", ROOT / "data" / "feeds" / "kev.json",
                   ROOT / "data" / "feeds" / "nvd_subset.json"]
    detect, ranking, context, weights, ablation = {}, {}, {}, {}, {}
    for name in TARGETS:
        alerts = load_alerts(name)
        if alerts is None:
            continue
        raw = RAW / f"{TARGETS[name][0]}_alerts.json"
        detect[name] = detection(name, alerts)
        rows = run_pipeline_for(alerts, DEFAULT_CTX, feeds)
        ranking[name] = exp_ranking(rows)
        context[name] = exp_context(alerts, feeds)
        weights[name] = exp_weights(alerts, feeds)
        ablation[name] = exp_ablation(alerts, feeds)
        inp = [raw] + feed_inputs
        for n, data in (("exp2_ranking", ranking), ("exp3_context", context), ("exp4_weights", weights),
                        ("exp5_ablation", ablation)):
            write(n, data, inp)
    write("exp1_detection", detect, [RAW / f"{TARGETS[n][0]}_alerts.json" for n in detect])
    if args.store:
        from src import db
        with db.connect() as conn:
            conn.execute("DELETE FROM validation_results WHERE run_date = CURRENT_DATE")
            for d in detect.values():
                conn.execute(
                    "INSERT INTO validation_results (target, known_vulns, detected, true_pos, precision, recall) "
                    "VALUES (%s,%s,%s,%s,%s,%s)",
                    (d["target"], d["known_classes"], d["detected_classes"], d["true_pos_alerts"],
                     d["precision"], d["recall"]))
    print(json.dumps({"detection": detect}, indent=2))


if __name__ == "__main__":
    main()
