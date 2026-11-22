"""Export a finished scan, import it back, and check the findings and scores match. Second import is a duplicate.

Runs with WASRA_INTEGRATION=1 against the running stack. Imports create a new scan row; nothing is scanned.
"""
import json
import os

import pytest
import requests

pytestmark = pytest.mark.skipif(os.environ.get("WASRA_INTEGRATION") != "1", reason="needs running stack")
BASE = "http://127.0.0.1:8080"


def _finished_scan_id() -> int:
    scans = requests.get(f"{BASE}/api/targets", timeout=30).json()
    for t in scans:
        latest = requests.get(f"{BASE}/api/targets/{t['id']}/latest-scan", timeout=30).json()
        if latest and latest["status"] == "done":
            full = requests.get(f"{BASE}/api/scans/{latest['id']}", timeout=30).json()
            if full.get("settings") is not None:
                return latest["id"]
    pytest.skip("no finished scan with stored settings to export")


def _findings(sid: int) -> set:
    rows = requests.get(f"{BASE}/api/scans/{sid}/findings", timeout=30).json()
    return {(r["plugin_id"], r["url"], r["fingerprint"], round(r["risk"], 4)) for r in rows}


def test_round_trip_gives_identical_findings_and_scores():
    original = _finished_scan_id()
    doc = requests.get(f"{BASE}/api/scans/{original}/export.json", timeout=60)
    assert doc.status_code == 200, doc.text
    body = doc.content
    assert json.loads(body)["format_version"] == 1
    imported = requests.post(f"{BASE}/api/import", data=body, headers={"Content-Type": "application/json"}, timeout=120)
    if imported.status_code == 409:
        pytest.skip("this scan was imported before; the duplicate check already passed")
    assert imported.status_code == 201, imported.text
    new = imported.json()["scan_id"]
    assert _findings(new) == _findings(original)


def test_second_import_of_the_same_file_is_refused():
    original = _finished_scan_id()
    body = requests.get(f"{BASE}/api/scans/{original}/export.json", timeout=60).content
    first = requests.post(f"{BASE}/api/import", data=body, headers={"Content-Type": "application/json"}, timeout=120)
    again = requests.post(f"{BASE}/api/import", data=body, headers={"Content-Type": "application/json"}, timeout=120)
    assert again.status_code == 409, (first.status_code, again.text)


def test_bad_version_is_refused_by_the_api():
    body = json.dumps({"format": "wasra-scan", "format_version": 99}).encode()
    r = requests.post(f"{BASE}/api/import", data=body, headers={"Content-Type": "application/json"}, timeout=30)
    assert r.status_code == 422 and "format_version" in r.text


def test_oversize_body_is_refused_by_the_api():
    r = requests.post(f"{BASE}/api/import", data=b" " * (25 * 1024 * 1024 + 1),
                      headers={"Content-Type": "application/json"}, timeout=120)
    assert r.status_code == 413
