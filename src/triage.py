"""Classify alerts and group repeated ones. Pure functions, no I/O.

Classification (from ZAP risk and confidence; ZAP does not confirm exploits):
  excluded       confidence "False Positive"
  informational  ZAP risk "Informational" (scanner notes, not vulnerabilities)
  potential      confidence "Low" (possible issue, needs manual check)
  vulnerability  everything else (scanner-reported; not proven exploitable)

Fingerprint: plugin ID + URL path (no query) + parameter + attack string. Alerts with the
same fingerprint are one finding seen several times; the raw count is kept.
"""
from urllib.parse import urlsplit


def classify(f: dict) -> str:
    if f["zap_confidence"] == "False Positive":
        return "excluded"
    if f["zap_risk"] == "Informational":
        return "informational"
    if f["zap_confidence"] == "Low":
        return "potential"
    return "vulnerability"


def fingerprint(alert: dict) -> tuple:
    path = urlsplit(alert["url"]).path or "/"
    return (str(alert["pluginId"]), path, alert.get("param", ""), alert.get("attack", ""))


def group(alerts: list[dict]) -> dict[tuple, list[dict]]:
    """Map fingerprint -> alerts with that fingerprint, in input order."""
    out: dict[tuple, list[dict]] = {}
    for a in alerts:
        out.setdefault(fingerprint(a), []).append(a)
    return out
