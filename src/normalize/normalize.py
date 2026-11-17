"""Convert ZAP alert JSON into the internal Finding schema."""
from dataclasses import asdict, dataclass

# ZAP risk / confidence -> numeric ratings used by scoring (SCORING.md)
RISK_SCORE = {"High": 0.8, "Medium": 0.5, "Low": 0.2, "Informational": 0.1}
CONFIDENCE_SCORE = {"High": 0.9, "Medium": 0.6, "Low": 0.3, "False Positive": 0.0}

# CWE -> OWASP Top 10 (2021). Covers the CWEs ZAP emits for the targets in scope.
CWE_TO_OWASP = {
    22: "A01:2021 Broken Access Control", 284: "A01:2021 Broken Access Control",
    352: "A01:2021 Broken Access Control", 639: "A01:2021 Broken Access Control",
    200: "A01:2021 Broken Access Control",
    319: "A02:2021 Cryptographic Failures", 311: "A02:2021 Cryptographic Failures",
    614: "A02:2021 Cryptographic Failures", 1004: "A02:2021 Cryptographic Failures",
    89: "A03:2021 Injection", 79: "A03:2021 Injection", 78: "A03:2021 Injection",
    77: "A03:2021 Injection", 94: "A03:2021 Injection", 611: "A03:2021 Injection",
    917: "A03:2021 Injection",
    521: "A07:2021 Identification and Authentication Failures",
    307: "A07:2021 Identification and Authentication Failures",
    620: "A07:2021 Identification and Authentication Failures",
    384: "A07:2021 Identification and Authentication Failures",
    502: "A08:2021 Software and Data Integrity Failures",
    601: "A01:2021 Broken Access Control",
    16: "A05:2021 Security Misconfiguration", 1021: "A05:2021 Security Misconfiguration",
    693: "A05:2021 Security Misconfiguration", 884: "A05:2021 Security Misconfiguration",
    918: "A10:2021 Server-Side Request Forgery",
}


@dataclass
class Finding:
    id: str
    type: str
    cwe: int | None
    owasp: str | None
    url: str
    zap_risk: str
    zap_risk_score: float
    zap_confidence: str
    zap_confidence_score: float
    evidence: str
    cve: str | None = None  # filled by enrich step; ZAP does not report CVEs


def normalize(alert: dict) -> Finding:
    cwe = int(alert["cweid"]) if str(alert.get("cweid", "-1")) not in ("", "-1", "0") else None
    risk = alert["risk"]
    conf = alert["confidence"]
    return Finding(
        id=str(alert["pluginId"]),
        type=alert["alert"],
        cwe=cwe,
        owasp=CWE_TO_OWASP.get(cwe),
        url=alert["url"],
        zap_risk=risk,
        zap_risk_score=RISK_SCORE[risk],
        zap_confidence=conf,
        zap_confidence_score=CONFIDENCE_SCORE[conf],
        evidence=alert.get("evidence", ""),
    )


def normalize_all(alerts: list[dict]) -> list[dict]:
    return [asdict(normalize(a)) for a in alerts]
