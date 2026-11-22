"""Write each validation run as a versioned export (results/exports/validation/<target>-<profile>.json).

  python scripts/validation_exports.py

The files load into any fresh install with `make load-validation` (scripts/import_scan.py, which recomputes
every score and refuses duplicates). Nothing is scanned.
"""
import datetime as dt
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
TARGETS = {"webgoat": ("WebGoat", "http://webgoat:8080/WebGoat/"), "bwapp": ("bWAPP", "http://bwapp:80")}
RATINGS = {"criticality": "High", "data_sensitivity": "High", "internet_exposure": "High", "business_impact": "High"}


def main() -> None:
    out = ROOT / "results" / "exports" / "validation"
    out.mkdir(parents=True, exist_ok=True)
    for name, (label, url) in TARGETS.items():
        for prof in ("quick", "standard", "deep"):
            base = ROOT / "results" / "validation" / name / prof
            meta = json.loads((base / "meta.json").read_text())
            settings = json.loads((base / "settings.json").read_text()) or {}
            doc = {
                "format": "wasra-scan", "format_version": 1,
                "exported_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "source": f"results/validation/{name}/{prof}",
                "target": {"name": label, "url": url, **RATINGS},
                "scan": {"profile": prof, "settings": {k: v for k, v in settings.items() if k != "profile"},
                         "started_at": meta.get("started_at"), "finished_at": meta.get("finished_at"),
                         "stage_seconds": meta.get("stage_seconds") or {},
                         "raw_alerts": json.loads((base / "raw_alerts.json").read_text())},
                "feed_snapshot": {"snapshot_date": json.loads((ROOT / "data/feeds/manifest.json").read_text())["snapshot_date"]},
            }
            (out / f"{name}-{prof}.json").write_text(json.dumps(doc, indent=1, sort_keys=True))
            print("wrote", out / f"{name}-{prof}.json")


if __name__ == "__main__":
    main()
