"""Scan one target through ZAP and save raw alerts to results/raw/<name>_alerts.json.

Run inside the backend container so the target's service name and any login seeding resolve:
  docker compose exec -T backend python -m src.collectors.run_scan --target http://dvwa:80 --name dvwa
"""
import argparse
import json
import os
import pathlib

from src.collectors import auth
from src.collectors.zap_client import ZapClient

ROOT = pathlib.Path(__file__).resolve().parents[2]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True)
    ap.add_argument("--name", required=True)
    args = ap.parse_args()
    zap = ZapClient(os.environ["ZAP_API_KEY"], os.environ.get("ZAP_URL", "http://zap:8090"))
    zap.run(args.target, cookie=auth.cookie_for(args.target))
    alerts = zap.alerts(args.target)
    out = ROOT / "results" / "raw" / f"{args.name}_alerts.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(alerts, indent=2, sort_keys=True))
    print(f"{len(alerts)} alerts -> {out}")


if __name__ == "__main__":
    main()
