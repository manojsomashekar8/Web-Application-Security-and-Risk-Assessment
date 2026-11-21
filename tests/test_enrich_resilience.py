"""A missing or unreadable feed file must log a warning, give n/a values, and let the scan continue."""
import json
import logging

import pytest

from src.enrich.enrich import load_feeds
from src.pipeline import run

CTX = {"criticality": "High", "data_sensitivity": "High", "internet_exposure": "High", "business_impact": "High"}
GOOD = {
    "epss.csv": "#model\ncve,epss,percentile\nCVE-2020-0001,0.42,0.9\n",
    "kev.json": json.dumps({"vulnerabilities": [{"cveID": "CVE-2020-0001"}]}),
    "nvd_subset.json": json.dumps([{"cve": {"id": "CVE-2020-0001", "metrics": {
        "cvssMetricV31": [{"cvssData": {"baseScore": 9.8}}]}}}]),
    "manifest.json": json.dumps({"snapshot_date": "2026-11-17", "files": {}}),
}
ALERT = {"pluginId": "10003", "alert": "x", "cweid": "89", "url": "http://t/", "risk": "High",
         "confidence": "High", "evidence": "", "param": "", "attack": ""}


def make_feeds(tmp_path, overrides=None):
    d = tmp_path / "feeds"
    d.mkdir()
    files = {**GOOD, **(overrides or {})}
    for name, text in files.items():
        if text is not None:
            (d / name).write_text(text)
    cm = tmp_path / "cve_map.json"
    cm.write_text(json.dumps({"10003": ["CVE-2020-0001"]}))
    return d, cm


def test_good_feeds_record_provenance(tmp_path):
    d, cm = make_feeds(tmp_path)
    f = load_feeds(d, cm)
    assert f["provenance"]["epss"] == {"feed": "EPSS", "file": "epss.csv", "snapshot_date": "2026-11-17", "status": "ok"}
    assert f["unavailable"] == {}


@pytest.mark.parametrize("name,field", [("epss.csv", "epss"), ("kev.json", "kev"), ("nvd_subset.json", "cvss")])
def test_missing_feed_warns_and_continues(tmp_path, caplog, name, field):
    d, cm = make_feeds(tmp_path, {name: None})
    with caplog.at_level(logging.WARNING):
        feeds = load_feeds(d, cm)
        rows = run([ALERT], CTX, feeds)
    assert name in caplog.text and "n/a" in caplog.text
    assert field in feeds["unavailable"]
    row = rows[0]
    assert row["provenance"][field]["status"] == "unavailable"
    assert row[{"epss": "epss", "kev": "kev", "cvss": "cvss"}[field]] is None
    assert row["risk"] >= 0  # the scan still produced a score


@pytest.mark.parametrize("name,field", [("epss.csv", "epss"), ("kev.json", "kev"), ("nvd_subset.json", "cvss")])
def test_unreadable_feed_warns_and_continues(tmp_path, caplog, name, field):
    d, cm = make_feeds(tmp_path, {name: "{not valid"})  # corrupt content
    with caplog.at_level(logging.WARNING):
        feeds = load_feeds(d, cm)
        rows = run([ALERT], CTX, feeds)
    assert name in caplog.text
    assert rows[0]["provenance"][field]["status"] == "unavailable"
    assert rows[0][{"epss": "epss", "kev": "kev", "cvss": "cvss"}[field]] is None


def test_missing_manifest_leaves_snapshot_date_unknown(tmp_path, caplog):
    d, cm = make_feeds(tmp_path, {"manifest.json": None})
    with caplog.at_level(logging.WARNING):
        feeds = load_feeds(d, cm)
    assert feeds["provenance"]["cvss"]["snapshot_date"] is None
    assert "manifest" in caplog.text
