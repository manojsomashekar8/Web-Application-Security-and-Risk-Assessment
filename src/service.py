"""Core services shared by the web UI and the JSON API: targets, scans, findings, allowlist."""
import json
import os
import pathlib
import re
import threading
from datetime import datetime, timezone

from src import db
from src.collectors import auth
from src.collectors.zap_client import ZapClient
from src.enrich.enrich import load_feeds
from src.pipeline import run as run_pipeline
from src.scoring.score import LEVEL

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEVELS = tuple(LEVEL)
CONTEXT_FIELDS = ("criticality", "data_sensitivity", "internet_exposure", "business_impact")


def allowed_targets() -> set[str]:
    """Parse '- <url> | note' lines from docs/TARGETS.md. Only these URLs may be scanned."""
    text = (ROOT / "docs" / "TARGETS.md").read_text()
    return set(re.findall(r"^- (\S+)\s*\|", text, re.M))


def validate_target(name: str, url: str, ctx: dict) -> list[str]:
    errors = []
    if not name.strip():
        errors.append("name: required")
    if url not in allowed_targets():
        errors.append("url: not in the allowlist (docs/TARGETS.md)")
    for k in CONTEXT_FIELDS:
        if ctx.get(k) not in LEVELS:
            errors.append(f"{k}: must be Low, Medium or High")
    return errors


def create_target(name: str, url: str, ctx: dict) -> int:
    with db.connect() as conn:
        row = conn.execute(
            "INSERT INTO targets (name, url, criticality, data_sensitivity, internet_exposure, business_impact) "
            "VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
            (name.strip(), url, *(ctx[k] for k in CONTEXT_FIELDS)),
        ).fetchone()
    return row["id"]


def start_scan(target_id: int) -> int:
    conn = db.connect()
    scan_id = conn.execute(
        "INSERT INTO scans (target_id, status, started_at) VALUES (%s,'running',now()) RETURNING id", (target_id,)
    ).fetchone()["id"]
    threading.Thread(target=_run_scan, args=(scan_id, target_id), daemon=True).start()
    return scan_id


_ZAP_LOCK = threading.Lock()  # one ZAP instance: scans run one at a time, the rest queue here


def _run_scan(scan_id: int, target_id: int) -> None:
    conn = db.connect()
    try:
        t = conn.execute("SELECT * FROM targets WHERE id=%s", (target_id,)).fetchone()
        zap = ZapClient(os.environ["ZAP_API_KEY"], os.environ.get("ZAP_URL", "http://zap:8090"))
        with _ZAP_LOCK:
            zap.run(t["url"], cookie=auth.cookie_for(t["url"]))
            raw = zap.alerts(t["url"])
        ctx = {k: t[k] for k in CONTEXT_FIELDS}
        rows = run_pipeline(raw, ctx, load_feeds())
        for r in rows:
            conn.execute(
                "INSERT INTO findings (scan_id, plugin_id, type, cwe, owasp, url, zap_risk, zap_confidence, "
                "cve, cvss, epss, kev, risk, weighted_sum, cvss_only, zap_risk_only, rank_risk, "
                "rank_weighted_sum, rank_cvss_only, rank_zap_risk_only, explanation, factors) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (scan_id, r["id"], r["type"], r["cwe"], r["owasp"], r["url"], r["zap_risk"], r["zap_confidence"],
                 r["cve"], r["cvss"], r["epss"], r["kev"], r["risk"], r["weighted_sum"], r["cvss_only"],
                 r["zap_risk_only"], r["rank_risk"], r["rank_weighted_sum"], r["rank_cvss_only"],
                 r["rank_zap_risk_only"], r["explanation"], json.dumps({"S": r["S"], "E": r["E"],
                                                                         "exposure": r["exposure"],
                                                                         "I": r["I"], "L": r["L"], **ctx})),
            )
        conn.execute("UPDATE scans SET status='done', finished_at=now() WHERE id=%s", (scan_id,))
    except Exception as exc:  # record failure, never leave the scan 'running'
        conn.execute("UPDATE scans SET status='failed', finished_at=now(), error=%s WHERE id=%s",
                     (str(exc)[:1000], scan_id))


def findings_for_scan(scan_id: int) -> list[dict]:
    with db.connect() as conn:
        return conn.execute("SELECT * FROM findings WHERE scan_id=%s ORDER BY rank_risk", (scan_id,)).fetchall()


def latest_scan(target_id: int) -> dict | None:
    with db.connect() as conn:
        return conn.execute("SELECT * FROM scans WHERE target_id=%s ORDER BY id DESC LIMIT 1", (target_id,)).fetchone()
