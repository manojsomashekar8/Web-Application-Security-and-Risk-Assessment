"""Turn a raw alert file (results/raw/<name>_alerts.json) into a versioned export the importer accepts.

  python scripts/raw_to_export.py results/raw/bwapp_alerts.json "bWAPP" http://bwapp:80 OUT.json

The original settings of old runs were not saved, so the profile is written as "unrecorded". Business ratings
default to the 'default' preset in configs/context_presets.json (Medium); pass --high to use High for all four.
"""
import datetime as dt
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 4:
        raise SystemExit(__doc__)
    raw_path, name, url, out = args
    alerts = json.loads(pathlib.Path(raw_path).read_text())
    preset = json.loads((ROOT / "configs" / "context_presets.json").read_text())["default"]
    ctx = {k: ("High" if "--high" in sys.argv else preset[k]) for k in preset}
    doc = {
        "format": "wasra-scan", "format_version": 1,
        "exported_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "source_file": str(raw_path),
        "target": {"name": name, "url": url, **ctx},
        "scan": {"profile": "unrecorded", "settings": {}, "started_at": None, "finished_at": None,
                 "stage_seconds": {}, "raw_alerts": alerts},
        "feed_snapshot": {"snapshot_date": json.loads((ROOT / "data/feeds/manifest.json").read_text())["snapshot_date"]},
    }
    pathlib.Path(out).write_text(json.dumps(doc, indent=1))
    print(f"wrote {out}: {len(alerts)} alerts for {name}")


if __name__ == "__main__":
    main()
