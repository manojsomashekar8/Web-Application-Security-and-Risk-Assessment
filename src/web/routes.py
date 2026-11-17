"""Server-rendered pages. Talks only to src.service, never to ZAP or Postgres directly."""
import pathlib

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src import db, service
from src.api.auth import require_auth
from src.scoring.compare import kendall_tau, top_k_overlap

HERE = pathlib.Path(__file__).parent
router = APIRouter(dependencies=[Depends(require_auth)])

templates = Jinja2Templates(directory=str(HERE / "templates"))
LEVELS = service.LEVELS
CONTEXT_HELP = {
    "criticality": "How important is the app to the business? High = core service.",
    "data_sensitivity": "What data does it hold? High = personal, financial or credentials.",
    "internet_exposure": "Can anyone on the internet reach it? High = public.",
    "business_impact": "Impact if it is compromised. High = major loss or outage.",
}


@router.get("/", response_class=RedirectResponse)
def index():
    return RedirectResponse("/targets")


@router.get("/targets", response_class=HTMLResponse)
def targets(request: Request):
    with db.connect() as conn:
        rows = conn.execute("SELECT * FROM targets ORDER BY id").fetchall()
    return templates.TemplateResponse(request, "targets.html", {"targets": rows})


@router.get("/targets/new", response_class=HTMLResponse)
def new_target(request: Request):
    return templates.TemplateResponse(request, "new_target.html",
                                      {"levels": LEVELS, "help": CONTEXT_HELP, "errors": [], "form": {}})


@router.post("/targets", response_class=HTMLResponse)
async def create(request: Request):
    form = dict((await request.form()).items())
    ctx = {k: form.get(k, "") for k in service.CONTEXT_FIELDS}
    errors = service.validate_target(form.get("name", ""), form.get("url", ""), ctx)
    if errors:
        return templates.TemplateResponse(request, "new_target.html", {
            "levels": LEVELS, "help": CONTEXT_HELP, "errors": errors, "form": form}, status_code=422)
    tid = service.create_target(form["name"], form["url"], ctx)
    return RedirectResponse(f"/targets/{tid}", status_code=303)


@router.get("/targets/{tid}", response_class=HTMLResponse)
def target_detail(request: Request, tid: int):
    with db.connect() as conn:
        t = conn.execute("SELECT * FROM targets WHERE id=%s", (tid,)).fetchone()
    return templates.TemplateResponse(request, "target.html", {
        "t": t, "scan": service.latest_scan(tid), "help": CONTEXT_HELP})


@router.post("/targets/{tid}/scan")
def scan(tid: int):
    scan_id = service.start_scan(tid)
    return RedirectResponse(f"/scans/{scan_id}", status_code=303)


@router.get("/scans/{sid}", response_class=HTMLResponse)
def scan_status(request: Request, sid: int):
    with db.connect() as conn:
        s = conn.execute("SELECT * FROM scans WHERE id=%s", (sid,)).fetchone()
    return templates.TemplateResponse(request, "scan.html", {"s": s})


@router.get("/scans/{sid}/findings", response_class=HTMLResponse)
def findings(request: Request, sid: int):
    rows = service.findings_for_scan(sid)
    return templates.TemplateResponse(request, "findings.html", {"sid": sid, "rows": rows})


@router.get("/scans/{sid}/compare", response_class=HTMLResponse)
def compare(request: Request, sid: int):
    rows = service.findings_for_scan(sid)
    methods = {"Framework": "rank_risk", "Weighted sum": "rank_weighted_sum",
               "CVSS-only": "rank_cvss_only", "ZAP-risk-only": "rank_zap_risk_only"}
    base = {r["id"]: r["rank_risk"] for r in rows}
    stats = {}
    for name, col in methods.items():
        other = {r["id"]: r[col] for r in rows}
        stats[name] = {"tau": round(kendall_tau(base, other), 3),
                       "top10": round(top_k_overlap(base, other, 10), 3)}
    return templates.TemplateResponse(request, "compare.html", {"sid": sid, "rows": rows, "stats": stats})
