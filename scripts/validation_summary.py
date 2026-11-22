"""Summarise the validation matrix (results/validation/<target>/<profile>/) into one table.

  python scripts/validation_summary.py             # writes results/validation/summary.json and summary.csv
  python scripts/validation_summary.py --store     # also stores one validation row per target (dashboard data)

Pages reached = ZAP's site-tree size after the spiders (stored with each scan: results/validation/<t>/<p>/meta.json).
Coverage rule: below configs/validation.json min_pages, precision and recall are null (shown as "Coverage too low").
"""
import csv
import collections
import datetime as dt
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.enrich.enrich import load_feeds  # noqa: E402
from src.experiments.run import DEFAULT_CTX, detection, categories  # noqa: E402
from src.pipeline import run as run_pipeline  # noqa: E402

MIN_PAGES = json.loads((ROOT / "configs" / "validation.json").read_text())["min_pages"]
TARGETS = {"webgoat": "http://webgoat:8080/WebGoat/", "bwapp": "http://bwapp:80"}
PROFILES = ("quick", "standard", "deep")


def summarise() -> list[dict]:
    feeds = load_feeds()
    rows = []
    for name, url in TARGETS.items():
        tops = {}
        per = {}
        for prof in PROFILES:
            base = ROOT / "results" / "validation" / name / prof
            alerts = json.loads((base / "raw_alerts.json").read_text())
            meta = json.loads((base / "meta.json").read_text())
            found = run_pipeline(alerts, DEFAULT_CTX, feeds)
            det = detection(name, alerts)
            pages = (meta.get("url_counts_after_spider") or {}).get("traditional", 0)
            ajax = (meta.get("url_counts_after_spider") or {}).get("ajax")
            ok = pages >= MIN_PAGES
            tops[prof] = [r["fingerprint"] for r in sorted(found, key=lambda r: r["rank_risk"])][:10]
            per[prof] = dict(
                target=name, url=url, profile=prof, zap_version=meta.get("zap_version"),
                zap_image=meta.get("zap_image"), total_seconds=round(meta["wall_seconds"]),
                stage_seconds=meta.get("stage_seconds"), active_scan_seconds=(meta.get("stage_seconds") or {}).get("active_scan"),
                urls_after_traditional=pages, urls_after_ajax=ajax, raw_alerts=len(alerts), unique_findings=len(found),
                classes=dict(collections.Counter(r["classification"] for r in found)),
                bands=dict(collections.Counter("High" if r["risk"] >= 60 else "Medium" if r["risk"] >= 30 else "Low" for r in found)),
                detected_types=det["detected_classes"], known_types=det["known_classes"], matching_alerts=det["true_pos_alerts"],
                missed_types=det["missed_classes"],
                precision=round(det["true_pos_alerts"] / len(alerts), 4) if alerts and ok else None,
                recall=round(det["detected_classes"] / det["known_classes"], 4) if ok else None,
                coverage_ok=ok, plugin_10003_alerts=sum(1 for a in alerts if a["pluginId"] == "10003"),
                cve_text_alerts=sum(1 for a in alerts if "CVE-" in json.dumps(a)),
                category_recall=categories(name, alerts) if ok else None,
                peak_zap_memory_mib=(meta.get("usage") or {}).get("zap", {}).get("mem_peak_mib"),
                peak_zap_cpu_pct=(meta.get("usage") or {}).get("zap", {}).get("cpu_peak_pct"),
            )
        deep = tops["deep"]
        for prof in PROFILES:
            k = tops[prof]
            per[prof]["top10_overlap_with_deep"] = (f"{len(set(k) & set(deep))}/{min(10, len(k))}" if k else "n/a")
            rows.append(per[prof])
    return rows


def write(rows: list[dict]) -> None:
    out = ROOT / "results" / "validation"
    (out / "summary.json").write_text(json.dumps({"generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                                                  "rows": rows}, indent=1, sort_keys=True, default=str))
    flat = [{k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in r.items()} for r in rows]
    with open(out / "summary.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(flat[0]))
        w.writeheader()
        w.writerows(flat)


def store(rows: list[dict]) -> None:
    import os
    from src import db
    with db.connect() as conn:
        conn.execute("DELETE FROM validation_results WHERE run_date = CURRENT_DATE AND target IN ('webgoat','bwapp')")
        for r in rows:
            if r["profile"] != "deep":  # one row per target: the deep run is the reference
                continue
            conn.execute("DELETE FROM validation_categories WHERE run_date = CURRENT_DATE AND target = %s", (r["target"],))
            for c in r["category_recall"] or []:
                conn.execute("INSERT INTO validation_categories (target, category, detected) VALUES (%s,%s,%s)",
                             (c["target"], c["category"], c["detected"]))
            conn.execute("INSERT INTO validation_results (target, known_vulns, detected, true_pos, precision, recall, "
                         "pages_reached, total_alerts, matching_alerts, coverage_ok) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                         (r["target"], r["known_types"], r["detected_types"], r["matching_alerts"], r["precision"],
                          r["recall"], r["urls_after_traditional"], r["raw_alerts"], r["matching_alerts"], r["coverage_ok"]))


if __name__ == "__main__":
    data = summarise()
    write(data)
    if "--store" in sys.argv:
        store(data)
    print(f"{len(data)} rows written to results/validation/summary.json")
