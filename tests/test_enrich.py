import json

from src.enrich.enrich import enrich, load_feeds

FEEDS = {
    "epss": {"CVE-2020-0001": 0.42},
    "kev": {"CVE-2020-0001"},
    "cvss": {"CVE-2020-0001": 9.8},
    "cve_map": {"10003": ["CVE-2020-0001"]},
}
BASE = {"id": "10003", "cve": None, "cvss": None, "epss": None, "kev": False}


def test_mapped_cve_gets_all_three_feeds():
    out = enrich({**BASE, "id": "10003"}, FEEDS)
    assert (out["cve"], out["cvss"], out["epss"], out["kev"]) == ("CVE-2020-0001", 9.8, 0.42, True)


def test_unmapped_finding_falls_back_to_none():
    out = enrich({**BASE, "id": "40018"}, FEEDS)
    assert (out["cve"], out["cvss"], out["epss"], out["kev"]) == (None, None, None, False)


def test_mapped_cve_missing_from_feeds_is_not_kev_or_scored():
    feeds = {**FEEDS, "epss": {}, "kev": set(), "cvss": {}}
    out = enrich({**BASE, "id": "10003"}, feeds)
    assert (out["cvss"], out["epss"], out["kev"]) == (None, None, False)


def test_loads_real_snapshot_without_network(tmp_path):
    (tmp_path / "epss.csv").write_text("#model\ncve,epss,percentile\nCVE-1,0.5,0.9\n")
    (tmp_path / "kev.json").write_text(json.dumps({"vulnerabilities": [{"cveID": "CVE-1"}]}))
    (tmp_path / "nvd_subset.json").write_text(json.dumps([{"cve": {"id": "CVE-1", "metrics": {
        "cvssMetricV31": [{"cvssData": {"baseScore": 7.5}}]}}}]))
    cm = tmp_path / "cm.json"
    cm.write_text(json.dumps({"_comment": "x", "1": ["CVE-1"]}))
    f = load_feeds(tmp_path, cm)
    assert f["epss"] == {"CVE-1": 0.5} and f["kev"] == {"CVE-1"} and f["cvss"] == {"CVE-1": 7.5}
    assert f["cve_map"] == {"1": ["CVE-1"]}
