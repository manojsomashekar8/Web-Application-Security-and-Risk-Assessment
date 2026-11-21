"""FastAPI app: web UI pages, JSON API, Prometheus /metrics."""
import pathlib

from fastapi import Depends, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, generate_latest, REGISTRY
from fastapi.responses import Response

from src import db, health as health_checks, service
from src.api.auth import auth_mode, require_auth
from src.metrics.exporter import WasraCollector
from src.report.build import build_report
from src.web.routes import router as web_router

HERE = pathlib.Path(__file__).resolve().parents[1]
app = FastAPI(title="WASRA")
app.include_router(web_router)
app.mount("/static", StaticFiles(directory=str(HERE / "web" / "static")), name="static")
REGISTRY.register(WasraCollector())


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/targets", dependencies=[Depends(require_auth)])
def list_targets():
    with db.connect() as conn:
        return conn.execute("SELECT * FROM targets ORDER BY id").fetchall()


@app.post("/api/targets", dependencies=[Depends(require_auth)], status_code=201)
def create_target(body: dict):
    ctx = {k: body.get(k, "") for k in service.CONTEXT_FIELDS}
    errors = service.validate_target(body.get("name", ""), body.get("url", ""), ctx)
    if errors:
        raise HTTPException(422, errors)
    return {"id": service.create_target(body["name"], body["url"], ctx)}


@app.get("/api/health", dependencies=[Depends(require_auth)])
def health():
    return health_checks.all_checks()


@app.post("/api/scans/{sid}/rescore", dependencies=[Depends(require_auth)])
def rescore(sid: int):
    try:
        return {"findings": service.rescore(sid)}
    except LookupError:
        raise HTTPException(404, "no such scan")
    except ValueError as exc:
        raise HTTPException(409, str(exc))


@app.get("/api/config")
def config():
    return {"auth_mode": auth_mode()}  # public: the frontend reads it before it can log in


@app.get("/api/allowed-targets", dependencies=[Depends(require_auth)])
def allowed_targets():
    return sorted(service.allowed_targets())


@app.get("/api/targets/{tid}/latest-scan", dependencies=[Depends(require_auth)])
def latest_scan(tid: int):
    s = service.latest_scan(tid)
    return {"id": s["id"], "status": s["status"], "error": s["error"]} if s else None


@app.post("/api/targets/{tid}/scan", dependencies=[Depends(require_auth)], status_code=202)
def api_scan(tid: int):
    return {"scan_id": service.start_scan(tid)}


@app.get("/api/scans/{sid}", dependencies=[Depends(require_auth)])
def scan_status(sid: int):
    with db.connect() as conn:
        s = conn.execute("SELECT * FROM scans WHERE id=%s", (sid,)).fetchone()
    if not s:
        raise HTTPException(404, "no such scan")
    return {"id": s["id"], "status": s["status"], "error": s["error"]}


@app.get("/api/scans/{sid}/findings", dependencies=[Depends(require_auth)])
def scan_findings(sid: int):
    return service.findings_for_scan(sid)


@app.get("/api/scans/{sid}/report.json", dependencies=[Depends(require_auth)])
def scan_report(sid: int):
    return build_report(sid)
