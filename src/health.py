"""Health checks for the status panel: Postgres, ZAP and feed freshness. Each check reports its own error."""
import datetime as dt
import json
import os
import pathlib

import requests

from src import db

FEEDS = pathlib.Path(__file__).resolve().parents[1] / "data" / "feeds"
FRESH_DAYS = 30  # a feed snapshot older than this is reported as stale (decision D31)


def postgres() -> dict:
    try:
        with db.connect() as conn:
            conn.execute("SELECT 1").fetchone()
        return {"ok": True}
    except Exception as exc:  # report, never raise: the panel must still render
        return {"ok": False, "error": str(exc)[:200]}


def zap() -> dict:
    url = os.environ.get("ZAP_URL", "http://zap:8090")
    try:
        r = requests.get(f"{url}/JSON/core/view/version/", params={"apikey": os.environ["ZAP_API_KEY"]}, timeout=5)
        r.raise_for_status()
        return {"ok": True, "version": r.json()["version"]}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200]}


def feeds(today: dt.date | None = None) -> dict:
    today = today or dt.date.today()
    try:
        snap = dt.date.fromisoformat(json.loads((FEEDS / "manifest.json").read_text())["snapshot_date"])
    except (OSError, ValueError, KeyError) as exc:
        return {"status": "missing", "error": str(exc)[:200]}
    age = (today - snap).days
    return {"status": "fresh" if age <= FRESH_DAYS else "stale", "snapshot_date": snap.isoformat(), "age_days": age}


def all_checks() -> dict:
    pg, z, f = postgres(), zap(), feeds()
    overall = "ok" if pg["ok"] and z["ok"] and f["status"] == "fresh" else "degraded"
    return {"status": overall, "postgres": pg, "zap": z, "feeds": f}
