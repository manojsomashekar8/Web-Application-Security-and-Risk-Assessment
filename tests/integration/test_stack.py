"""Live-stack checks. Run with WASRA_INTEGRATION=1 after `make up`. Skipped otherwise, so `make test` stays offline."""
import os
import time

import pytest
import requests

pytestmark = pytest.mark.skipif(os.environ.get("WASRA_INTEGRATION") != "1", reason="needs running stack")
BASE = "http://127.0.0.1:8080"
AUTH = (os.environ.get("WEB_USER", "admin"), os.environ.get("WEB_PASSWORD", ""))
TARGET = "http://juice-shop:3000"
CTX = {"criticality": "High", "data_sensitivity": "High", "internet_exposure": "High", "business_impact": "High"}


def test_health_and_auth_match_mode():
    assert requests.get(f"{BASE}/healthz", timeout=10).json() == {"ok": True}
    mode = requests.get(f"{BASE}/api/config", timeout=10).json()["auth_mode"]
    expected = 401 if mode == "basic" else 200
    assert requests.get(f"{BASE}/api/targets", timeout=10).status_code == expected


def test_scan_end_to_end_stores_ranked_findings():
    t = requests.post(f"{BASE}/api/targets", auth=AUTH, json={"name": "Juice Shop", "url": TARGET, **CTX}, timeout=30)
    assert t.status_code == 201, t.text
    sid = requests.post(f"{BASE}/api/targets/{t.json()['id']}/scan", auth=AUTH, timeout=30).json()["scan_id"]
    deadline = time.time() + 3600
    while time.time() < deadline:
        s = requests.get(f"{BASE}/api/scans/{sid}", auth=AUTH, timeout=30).json()
        if s["status"] in ("done", "failed"):
            break
        time.sleep(15)
    assert s["status"] == "done", s
    findings = requests.get(f"{BASE}/api/scans/{sid}/findings", auth=AUTH, timeout=30).json()
    assert findings and all(0 <= f["risk"] <= 100 and f["explanation"] for f in findings)
    assert sorted(f["rank_risk"] for f in findings) == list(range(1, len(findings) + 1))
    rep = requests.get(f"{BASE}/api/scans/{sid}/report.json", auth=AUTH, timeout=30).json()
    assert len(rep["findings"]) == len(findings)


def test_metrics_exposed():
    body = requests.get(f"{BASE}/metrics", timeout=10).text
    assert "wasra_scans" in body
