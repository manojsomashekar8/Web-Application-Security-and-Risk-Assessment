"""Per-finding report: scanner text is escaped in HTML (evidence can contain markup)."""
from src.report.finding import finding_html

PAYLOAD = "<script>alert(1)</script>"


def detail(**over):
    base = {"scan_id": 1, "target": "http://dvwa:80", "name": "X", "classification": "vulnerability",
            "risk": 12.0, "band": "Low", "rank": 1, "url": "http://dvwa:80/a", "description": "d",
            "solution": "s", "reference": "r", "param": "q", "attack": "a", "evidence": PAYLOAD,
            "occurrences": 2, "cwe": 79, "owasp": "A03", "zap_risk": "Low", "zap_confidence": "Medium",
            "cve": None, "cvss": None, "epss": None, "kev": None, "factors": {"S": 0.2},
            "explanation": "e", "context": {"criticality": "High"}, "rank_cvss_only": 1,
            "rank_zap_risk_only": 1, "rank_weighted_sum": 1, "raw_stored": True}
    return {**base, **over}


def test_scanner_evidence_is_escaped_in_html():
    html = finding_html(detail())
    assert PAYLOAD not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_missing_cve_shows_na_not_zero():
    html = finding_html(detail())
    assert "n/a" in html and "<dd>0" not in html


def test_csv_guards_against_formula_injection():
    from src import service
    orig = service.findings_for_scan
    service.findings_for_scan = lambda sid: [{"rank_risk": 1, "type": "=HYPERLINK(\"x\")", "classification": "vulnerability",
        "url": "u", "risk": 1.0, "zap_risk": "Low", "zap_confidence": "Low", "cwe": 79, "owasp": None, "cve": None,
        "cvss": None, "epss": None, "kev": None, "occurrences": 1, "explanation": "e"}]
    try:
        out = service.findings_csv(1)
    finally:
        service.findings_for_scan = orig
    assert "'=HYPERLINK" in out


def test_blank_cells_stay_blank_in_csv():
    from src import service
    orig = service.findings_for_scan
    service.findings_for_scan = lambda sid: [{"rank_risk": 1, "type": "plain", "classification": "vulnerability",
        "url": "u", "risk": 1.0, "zap_risk": "Low", "zap_confidence": "Low", "cwe": None, "owasp": None,
        "cve": None, "cvss": None, "epss": None, "kev": None, "occurrences": 1, "explanation": "e"}]
    try:
        out = service.findings_csv(1)
    finally:
        service.findings_for_scan = orig
    assert ",,,," in out.splitlines()[1]
