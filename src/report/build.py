"""Build JSON and HTML reports for a finished scan. `python -m src.report.build` writes all of them."""
import json
import pathlib

from jinja2 import Environment, FileSystemLoader

from src import db, service

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "reports"
_env = Environment(loader=FileSystemLoader(str(ROOT / "src" / "report" / "templates")), autoescape=True)


def build_report(sid: int) -> dict:
    with db.connect() as conn:
        s = conn.execute("SELECT s.*, t.name, t.url FROM scans s JOIN targets t ON t.id=s.target_id WHERE s.id=%s",
                         (sid,)).fetchone()
    rows = service.findings_for_scan(sid)
    keep = ("rank_risk", "risk", "id", "type", "url", "cwe", "owasp", "zap_risk", "zap_confidence",
            "cve", "cvss", "epss", "kev", "rank_cvss_only", "rank_zap_risk_only", "rank_weighted_sum",
            "explanation", "factors")
    return {"scan_id": sid, "target": s["url"], "name": s["name"], "status": s["status"],
            "findings": [{k: r[k] for k in keep} for r in rows]}


def write_all() -> list[pathlib.Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    with db.connect() as conn:
        ids = [r["id"] for r in conn.execute("SELECT id FROM scans WHERE status='done' ORDER BY id")]
    written = []
    for sid in ids:
        rep = build_report(sid)
        j = OUT / f"scan_{sid}.json"
        j.write_text(json.dumps(rep, indent=2, sort_keys=True, default=str))
        h = OUT / f"scan_{sid}.html"
        h.write_text(_env.get_template("report.html").render(r=rep))
        written += [j, h]
    return written


if __name__ == "__main__":
    for p in write_all():
        print(p)
