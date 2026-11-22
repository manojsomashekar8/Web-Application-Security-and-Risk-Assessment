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
from src.scoring.compare import top_k_overlap
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


class ResourceError(Exception):
    """Not enough free memory to start a scan safely."""


class DuplicateTarget(Exception):
    """A target with this URL already exists (targets.url is unique)."""


def target_id_for_url(url: str) -> int | None:
    with db.connect() as conn:
        row = conn.execute("SELECT id FROM targets WHERE url=%s", (url,)).fetchone()
    return row["id"] if row else None


def create_target(name: str, url: str, ctx: dict) -> int:
    import psycopg.errors
    try:
        with db.connect() as conn:
            row = conn.execute(
                "INSERT INTO targets (name, url, criticality, data_sensitivity, internet_exposure, business_impact) "
                "VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
                (name.strip(), url, *(ctx[k] for k in CONTEXT_FIELDS)),
            ).fetchone()
    except psycopg.errors.UniqueViolation as exc:
        raise DuplicateTarget(url) from exc
    return row["id"]


def mem_available_mib() -> int:
    return next((int(l.split()[1]) // 1024 for l in open("/proc/meminfo") if l.startswith("MemAvailable")), 0)


def start_scan(target_id: int, profile: str = "deep", custom: dict | None = None) -> int:
    settings = resolve_settings(profile, custom)  # raises ValueError on bad input, before anything is stored
    need = json.loads((ROOT / "configs" / "resources.json").read_text())["min_mem_available_mb"]
    if mem_available_mib() < need:  # refuse rather than start a scan that will run the host out of memory
        raise ResourceError(f"only {mem_available_mib()} MB of memory is free; a scan needs {need} MB")
    conn = db.connect()
    scan_id = conn.execute(
        "INSERT INTO scans (target_id, status, started_at, settings) VALUES (%s,'running',now(),%s::jsonb) RETURNING id",
        (target_id, json.dumps(settings)),
    ).fetchone()["id"]
    threading.Thread(target=_run_scan, args=(scan_id, target_id, settings), daemon=True).start()
    return scan_id


def resolve_settings(profile: str, custom: dict | None) -> dict:
    from src.scanprofile import resolve
    return resolve(profile, custom)


_ZAP_LOCK = threading.Lock()  # one ZAP instance: scans run one at a time, the rest queue here


def scan_rows(raw: list[dict], ctx: dict) -> tuple[list[dict], float | None]:
    """Pipeline plus the top-10 overlap between the framework and CVSS-only rankings (None if no findings)."""
    rows = run_pipeline(raw, ctx, load_feeds())
    if not rows:
        return rows, None
    key = {r["fingerprint"]: r for r in rows}
    overlap = top_k_overlap({k: r["rank_risk"] for k, r in key.items()},
                            {k: r["rank_cvss_only"] for k, r in key.items()}, k=10)
    return rows, overlap


def _store_findings(conn, scan_id: int, rows: list[dict], ctx: dict) -> None:
    for r in rows:
        conn.execute(
            "INSERT INTO findings (scan_id, plugin_id, type, cwe, owasp, url, zap_risk, zap_confidence, "
            "cve, cvss, epss, kev, risk, weighted_sum, cvss_only, zap_risk_only, rank_risk, "
            "rank_weighted_sum, rank_cvss_only, rank_zap_risk_only, explanation, factors, "
            "classification, occurrences, fingerprint, provenance, enrichment_na) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s)",
            (scan_id, r["id"], r["type"], r["cwe"], r["owasp"], r["url"], r["zap_risk"], r["zap_confidence"],
             r["cve"], r["cvss"], r["epss"], r["kev"], r["risk"], r["weighted_sum"], r["cvss_only"],
             r["zap_risk_only"], r["rank_risk"], r["rank_weighted_sum"], r["rank_cvss_only"],
             r["rank_zap_risk_only"], r["explanation"], json.dumps({"S": r["S"], "E": r["E"],
                                                                     "exposure": r["exposure"],
                                                                     "I": r["I"], "L": r["L"], **ctx}),
             r["classification"], r["occurrences"], r["fingerprint"], json.dumps(r["provenance"]),
             r["enrichment_na"]),
        )


def _run_scan(scan_id: int, target_id: int, settings: dict) -> None:
    conn = db.connect()
    try:
        t = conn.execute("SELECT * FROM targets WHERE id=%s", (target_id,)).fetchone()
        zap = ZapClient(os.environ["ZAP_API_KEY"], os.environ.get("ZAP_URL", "http://zap:8090"))
        with _ZAP_LOCK:
            zap_version = zap.version()
            timings = zap.run(t["url"], cookie=auth.cookie_for(t["url"]), settings=settings)
            url_counts = dict(zap.url_counts)
            raw = zap.alerts(t["url"])
        conn.execute("UPDATE scans SET raw_alerts=%s::jsonb, stage_seconds=%s::jsonb, zap_version=%s, stage_urls=%s::jsonb "
                     "WHERE id=%s", (json.dumps(raw), json.dumps(timings), zap_version, json.dumps(url_counts), scan_id))
        ctx = {k: t[k] for k in CONTEXT_FIELDS}
        rows, overlap = scan_rows(raw, ctx)
        _store_findings(conn, scan_id, rows, ctx)
        try:  # ZAP's report is a bonus: a failure here must not fail the scan
            with _ZAP_LOCK:
                report = zap.generate_report(f"scan-{scan_id}.html")
        except Exception as exc:
            report = None
            print("ZAP report not generated:", exc, flush=True)
        conn.execute("UPDATE scans SET status='done', finished_at=now(), top10_overlap=%s, zap_report=%s WHERE id=%s",
                     (overlap, report, scan_id))
    except Exception as exc:  # record failure, never leave the scan 'running'
        conn.execute("UPDATE scans SET status='failed', finished_at=now(), error=%s WHERE id=%s",
                     (str(exc)[:1000], scan_id))


def rescore(scan_id: int) -> int:
    """Recompute findings from the scan's stored raw alerts with the target's current context. No new scan."""
    with db.connect() as conn:
        s = conn.execute("SELECT s.raw_alerts, t.* FROM scans s JOIN targets t ON t.id = s.target_id "
                         "WHERE s.id=%s", (scan_id,)).fetchone()
        if s is None:
            raise LookupError("no such scan")
        if s["raw_alerts"] is None:
            raise ValueError("this scan has no stored raw alerts (it ran before storage existed); run a new scan")
        ctx = {k: s[k] for k in CONTEXT_FIELDS}
        rows, overlap = scan_rows(s["raw_alerts"], ctx)
        with conn.transaction():
            conn.execute("DELETE FROM findings WHERE scan_id=%s", (scan_id,))
            _store_findings(conn, scan_id, rows, ctx)
            conn.execute("UPDATE scans SET top10_overlap=%s WHERE id=%s", (overlap, scan_id))
    return len(rows)


def findings_for_scan(scan_id: int) -> list[dict]:
    with db.connect() as conn:
        return conn.execute("SELECT * FROM findings WHERE scan_id=%s ORDER BY rank_risk", (scan_id,)).fetchall()


def latest_scan(target_id: int) -> dict | None:
    with db.connect() as conn:
        return conn.execute("SELECT * FROM scans WHERE target_id=%s ORDER BY id DESC LIMIT 1", (target_id,)).fetchone()


def finding_detail_for(finding_id: int) -> dict | None:
    from src.report.finding import finding_detail
    from src.scoring.score import band
    with db.connect() as conn:
        f = conn.execute("SELECT * FROM findings WHERE id=%s", (finding_id,)).fetchone()
        if f is None:
            return None
        scan = conn.execute("SELECT s.id, s.raw_alerts, t.url FROM scans s JOIN targets t ON t.id = s.target_id "
                            "WHERE s.id=%s", (f["scan_id"],)).fetchone()
    return finding_detail(f, {"id": scan["id"]}, scan["url"], scan["raw_alerts"], band(f["risk"]))


def findings_csv(scan_id: int) -> str:
    """Findings table as CSV. Cells starting with = + - @ are prefixed with ' so spreadsheets do not run them."""
    import csv
    import io
    cols = ["rank_risk", "type", "classification", "url", "risk", "zap_risk", "zap_confidence", "cwe", "owasp",
            "cve", "cvss", "epss", "kev", "occurrences", "explanation"]
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(cols)
    for r in findings_for_scan(scan_id):
        row = []
        for c in cols:
            v = "" if r[c] is None else r[c]
            if isinstance(v, str) and v and v[0] in "=+-@":  # empty cells must stay empty
                v = "'" + v
            row.append(v)
        w.writerow(row)
    return buf.getvalue()


def scan_html_for(scan_id: int) -> str | None:
    from src.report.finding import scan_html
    with db.connect() as conn:
        s = conn.execute("SELECT s.id, t.url FROM scans s JOIN targets t ON t.id=s.target_id WHERE s.id=%s",
                         (scan_id,)).fetchone()
    if s is None:
        return None
    return scan_html(scan_id, s["url"], findings_for_scan(scan_id))


class DuplicateImport(Exception):
    """This exact scan was already imported."""


def export_scan(scan_id: int) -> dict | None:
    from src import importexport
    with db.connect() as conn:
        row = conn.execute("SELECT s.*, t.name, t.url, t.criticality, t.data_sensitivity, t.internet_exposure, "
                           "t.business_impact FROM scans s JOIN targets t ON t.id=s.target_id WHERE s.id=%s",
                           (scan_id,)).fetchone()
    if row is None:
        return None
    if row["status"] != "done":
        raise ValueError("only finished scans can be exported")
    if row["raw_alerts"] is None:
        raise ValueError("this scan has no stored raw alerts, so it cannot be exported")
    n = len(findings_for_scan(scan_id))
    return importexport.export_document(row, row, n)


def import_scan(raw: bytes) -> int:
    from src import importexport
    from src.scanprofile import resolve
    data = importexport.parse(raw)
    v = importexport.validate(data)
    t = v["target"]
    errors = validate_target(t["name"], t["url"], {k: t[k] for k in CONTEXT_FIELDS})
    if errors:  # the allowlist still applies to imported targets
        raise importexport.ImportError_("; ".join(errors))
    digest = importexport.content_hash(data)
    if v["profile"] == "unrecorded":
        settings = {"profile": "unrecorded", "description": "Settings were not recorded for this scan (re-imported raw alerts)."}
    else:
        settings = resolve(v["profile"], v["settings"] if v["profile"] == "custom" else None)
    ctx = {k: t[k] for k in CONTEXT_FIELDS}
    rows, overlap = scan_rows(v["alerts"], ctx)  # recomputed from the raw alerts; stored scores are ignored
    with db.connect() as conn:
        if conn.execute("SELECT 1 FROM scans WHERE import_hash=%s", (digest,)).fetchone():
            raise DuplicateImport(digest[:12])
        target = conn.execute("SELECT id FROM targets WHERE url=%s", (t["url"],)).fetchone()
        tid = target["id"] if target else conn.execute(
            "INSERT INTO targets (name, url, criticality, data_sensitivity, internet_exposure, business_impact) "
            "VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
            (t["name"], t["url"], *(t[k] for k in CONTEXT_FIELDS))).fetchone()["id"]
        with conn.transaction():
            sid = conn.execute(
                "INSERT INTO scans (target_id, status, started_at, finished_at, settings, stage_seconds, raw_alerts, "
                "top10_overlap, imported_from, imported_at, import_hash) "
                "VALUES (%s,'done',now(),now(),%s::jsonb,%s::jsonb,%s::jsonb,%s,%s,now(),%s) RETURNING id",
                (tid, json.dumps(settings), json.dumps(v["stage_seconds"]), json.dumps(v["alerts"]), overlap,
                 f"export {data['exported_at']} (format {data['format_version']})", digest)).fetchone()["id"]
            _store_findings(conn, sid, rows, ctx)
    return sid
