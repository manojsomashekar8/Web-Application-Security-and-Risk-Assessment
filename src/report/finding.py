"""One finding as a report: JSON and HTML. Scanner text (evidence, descriptions) is escaped by Jinja2 autoescape."""
import json

from jinja2 import Environment, select_autoescape

from src.triage import fingerprint, group

_env = Environment(autoescape=select_autoescape(["html"]))

TEMPLATE = _env.from_string("""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Finding: {{ d.name }}</title>
<style>body{font-family:system-ui,sans-serif;max-width:860px;margin:2rem auto;padding:0 1rem;color:#1b2430}
dt{font-weight:600;margin-top:.6rem}dd{margin:.1rem 0 0 0}pre{white-space:pre-wrap;background:#f3f5f8;padding:.6rem;border-radius:6px}
table{border-collapse:collapse}td,th{border:1px solid #dfe3ea;padding:.3rem .5rem;text-align:left;vertical-align:top}</style>
</head><body>
<h1>{{ d.name }}</h1>
<p>Scan #{{ d.scan_id }} on {{ d.target }} · class <strong>{{ d.classification }}</strong> · score <strong>{{ '%.1f'|format(d.risk) }}</strong> ({{ d.band }}) · rank {{ d.rank }}</p>
<h2>What ZAP reported</h2>
<dl>
<dt>Description</dt><dd>{{ d.description or 'not stored for this scan' }}</dd>
<dt>Solution</dt><dd>{{ d.solution or 'not stored for this scan' }}</dd>
<dt>References</dt><dd>{{ d.reference or 'not stored for this scan' }}</dd>
<dt>URL</dt><dd>{{ d.url }}</dd>
<dt>Parameter</dt><dd>{{ d.param or '-' }}</dd>
<dt>Attack</dt><dd>{{ d.attack or '-' }}</dd>
<dt>Evidence</dt><dd><pre>{{ d.evidence or '-' }}</pre></dd>
<dt>Alerts merged into this finding</dt><dd>{{ d.occurrences }}</dd>
</dl>
<h2>Classification and enrichment</h2>
<dl>
<dt>CWE</dt><dd>{{ d.cwe or 'n/a' }}</dd>
<dt>OWASP category</dt><dd>{{ d.owasp or 'n/a' }}</dd>
<dt>ZAP risk / confidence</dt><dd>{{ d.zap_risk }} / {{ d.zap_confidence }}</dd>
<dt>CVE</dt><dd>{{ d.cve or 'n/a (no CVE mapped to this ZAP alert)' }}</dd>
<dt>CVSS / EPSS / KEV</dt><dd>{{ d.cvss if d.cvss is not none else 'n/a' }} / {{ d.epss if d.epss is not none else 'n/a' }} / {{ 'n/a' if d.kev is none else ('yes' if d.kev else 'no') }}</dd>
</dl>
<h2>How the score was made</h2>
<table><tr><th>Factor</th><th>Value</th></tr>
{% for k, v in d.factors.items() %}<tr><td>{{ k }}</td><td>{{ v }}</td></tr>{% endfor %}
</table>
<p>{{ d.explanation }}</p>
<h2>Context used</h2>
<table><tr><th>Factor</th><th>Rating</th></tr>
{% for k, v in d.context.items() %}<tr><td>{{ k }}</td><td>{{ v }}</td></tr>{% endfor %}
</table>
<h2>Rank under each method</h2>
<ul><li>Framework risk: {{ d.rank }}</li><li>CVSS only: {{ d.rank_cvss_only }}</li><li>ZAP risk only: {{ d.rank_zap_risk_only }}</li><li>Weighted sum: {{ d.rank_weighted_sum }}</li></ul>
</body></html>""")


def finding_detail(finding: dict, scan: dict, target_url: str, raw_alerts: list[dict] | None, band: str) -> dict:
    """Everything the per-finding report shows. Raw text comes from the stored alerts, found by fingerprint."""
    raw = None
    if raw_alerts:
        for key, alerts in group(raw_alerts).items():
            if "|".join(map(str, key)) == finding["fingerprint"]:
                raw = alerts[0]
                break
    factors = finding["factors"] if isinstance(finding["factors"], dict) else json.loads(finding["factors"] or "{}")
    ctx = {k: factors[k] for k in ("criticality", "data_sensitivity", "internet_exposure", "business_impact")
           if k in factors}
    return {
        "scan_id": scan["id"], "target": target_url, "name": finding["type"], "classification": finding["classification"],
        "risk": finding["risk"], "band": band, "rank": finding["rank_risk"], "url": finding["url"],
        "description": (raw or {}).get("description"), "solution": (raw or {}).get("solution"),
        "reference": (raw or {}).get("reference"), "param": (raw or {}).get("param") or "",
        "attack": (raw or {}).get("attack") or "", "evidence": (raw or {}).get("evidence") or "",
        "occurrences": finding["occurrences"], "cwe": finding["cwe"], "owasp": finding["owasp"],
        "zap_risk": finding["zap_risk"], "zap_confidence": finding["zap_confidence"], "cve": finding["cve"],
        "cvss": finding["cvss"], "epss": finding["epss"], "kev": finding["kev"], "factors": factors,
        "explanation": finding["explanation"], "context": ctx,
        "rank_cvss_only": finding["rank_cvss_only"], "rank_zap_risk_only": finding["rank_zap_risk_only"],
        "rank_weighted_sum": finding["rank_weighted_sum"],
        "raw_stored": raw is not None,
    }


def finding_html(detail: dict) -> str:
    return TEMPLATE.render(d=detail)
