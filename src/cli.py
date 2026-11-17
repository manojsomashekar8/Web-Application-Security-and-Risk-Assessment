"""Host CLI that drives the running backend over its HTTP API (no direct DB access from the host).

  python -m src.cli scan --url http://juice-shop:3000 --name "Juice Shop"
"""
import argparse
import pathlib
import time

import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
API = "http://127.0.0.1:8080"
CTX = {"criticality": "High", "data_sensitivity": "High", "internet_exposure": "High", "business_impact": "High"}


def _env(key: str) -> str:
    return next(l.split("=", 1)[1] for l in (ROOT / ".env").read_text().splitlines() if l.startswith(key + "="))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["scan"])
    ap.add_argument("--url", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--timeout", type=int, default=7200)
    args = ap.parse_args()
    auth = (_env("WEB_USER"), _env("WEB_PASSWORD"))
    existing = next((x for x in requests.get(f"{API}/api/targets", auth=auth, timeout=30).json()
                     if x["url"] == args.url), None)
    if existing:
        tid = existing["id"]
    else:
        t = requests.post(f"{API}/api/targets", auth=auth, json={"name": args.name, "url": args.url, **CTX},
                          timeout=30)
        if t.status_code != 201:
            raise SystemExit(f"target rejected: {t.text}")
        tid = t.json()["id"]
    sid = requests.post(f"{API}/api/targets/{tid}/scan", auth=auth, timeout=30).json()["scan_id"]
    deadline = time.time() + args.timeout
    while time.time() < deadline:
        s = requests.get(f"{API}/api/scans/{sid}", auth=auth, timeout=30).json()
        if s["status"] in ("done", "failed"):
            print(f"scan {sid}: {s['status']} {s['error'] or ''}")
            return
        time.sleep(15)
    raise SystemExit(f"scan {sid} still running after {args.timeout}s")


if __name__ == "__main__":
    main()
