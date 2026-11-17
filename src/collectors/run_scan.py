"""Scan one target through ZAP and save raw alerts to results/raw/."""
import argparse
import json
import os
import pathlib

from src.collectors.zap_client import ZapClient

ROOT = pathlib.Path(__file__).resolve().parents[2]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True)
    ap.add_argument("--name", default=None)
    args = ap.parse_args()
    key = os.environ.get("ZAP_API_KEY") or next(
        l.split("=", 1)[1] for l in (ROOT / ".env").read_text().splitlines() if l.startswith("ZAP_API_KEY=")
    )
    zap = ZapClient(key)
    zap.run(args.target)
    alerts = zap.alerts(args.target)
    name = args.name or args.target.split("//")[-1].split(":")[0]
    out = ROOT / "results" / "raw" / f"{name}_alerts.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(alerts, indent=2, sort_keys=True))
    print(f"{len(alerts)} alerts -> {out}")


if __name__ == "__main__":
    main()
