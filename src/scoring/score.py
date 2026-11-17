"""Deterministic, explainable risk scoring (SCORING.md). Pure functions, no I/O."""
import json
import pathlib

LEVEL = {"Low": 0.33, "Medium": 0.66, "High": 1.0}
CONTEXT_KEYS = ("criticality", "data_sensitivity", "internet_exposure", "business_impact")
ROOT = pathlib.Path(__file__).resolve().parents[2]


def load_weights(path: pathlib.Path = ROOT / "configs" / "weights.json") -> dict:
    return json.loads(path.read_text())["weighted_sum"]


def severity(f: dict) -> float:
    """S: CVSS/10 when a CVE with a score is mapped, otherwise ZAP risk."""
    return f["cvss"] / 10 if f.get("cvss") is not None else f["zap_risk_score"]


def exploitability(f: dict) -> float:
    """E: 1.0 if KEV, else EPSS, else ZAP confidence."""
    if f.get("kev"):
        return 1.0
    if f.get("epss") is not None:
        return f["epss"]
    return f["zap_confidence_score"]


def context_values(ctx: dict) -> dict:
    return {k: LEVEL[ctx[k]] for k in CONTEXT_KEYS}


def risk(s: float, e: float, ctx: dict) -> dict:
    c = context_values(ctx)
    exposure = c["internet_exposure"]
    impact = s * (c["criticality"] + c["data_sensitivity"] + c["business_impact"]) / 3
    likelihood = e * exposure
    return {"S": s, "E": e, "exposure": exposure, "I": impact, "L": likelihood,
            "risk": 100 * likelihood * impact}


def weighted_sum(s: float, e: float, ctx: dict, w: dict) -> float:
    c = sum(context_values(ctx).values()) / 4
    return 100 * (w["S"] * s + w["E"] * e + w["C"] * c)


def band(score: float) -> str:
    return "High" if score >= 60 else "Medium" if score >= 30 else "Low"


def explain(f: dict, ctx: dict, score: float) -> str:
    kev = "KEV-listed" if f.get("kev") else "not KEV-listed"
    return (f"{band(score)}: {kev}, internet exposure {ctx['internet_exposure']}, "
            f"criticality {ctx['criticality']}, data sensitivity {ctx['data_sensitivity']}, "
            f"business impact {ctx['business_impact']}.")


def score_finding(f: dict, ctx: dict, w: dict | None = None) -> dict:
    s, e = severity(f), exploitability(f)
    r = risk(s, e, ctx)
    w = w or load_weights()
    out = {**r, "weighted_sum": weighted_sum(s, e, ctx, w),
           "cvss_only": 100 * s, "zap_risk_only": 100 * f["zap_risk_score"]}
    out["explanation"] = explain(f, ctx, r["risk"])
    return out
