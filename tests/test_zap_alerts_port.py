"""Regression: ZAP stores URLs without default ports, so the alert lookup must drop them (bug found 2026-11-22)."""
from src.collectors.zap_client import ZapClient


def test_alert_lookup_drops_default_port(monkeypatch):
    seen = []
    z = ZapClient("key", "http://unused")
    monkeypatch.setattr(z, "_get", lambda path, **params: seen.append(params["baseurl"]) or {"alerts": []})
    z.alerts("http://bwapp:80")
    z.alerts("http://dvwa:80")
    z.alerts("https://x:443/a")
    z.alerts("http://webgoat:8080/WebGoat/")  # non-default port is kept
    assert seen == ["http://bwapp", "http://dvwa", "https://x/a", "http://webgoat:8080/WebGoat/"]
