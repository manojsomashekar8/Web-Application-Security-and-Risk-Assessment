"""Classification and fingerprint grouping of ZAP alerts (src/triage.py)."""
from src.pipeline import run
from src.triage import classify, fingerprint, group

CTX = {"criticality": "High", "data_sensitivity": "High", "internet_exposure": "High", "business_impact": "High"}
FEEDS = {"epss": {}, "kev": set(), "cvss": {}, "cve_map": {}}


def f(risk, conf):
    return {"zap_risk": risk, "zap_confidence": conf}


def test_classification_rules():
    assert classify(f("High", "False Positive")) == "excluded"
    assert classify(f("Informational", "High")) == "informational"
    assert classify(f("Medium", "Low")) == "potential"
    assert classify(f("High", "Medium")) == "vulnerability"


def alert(url, plugin="10016", param="", attack=""):
    return {"pluginId": plugin, "alert": "x", "cweid": "-1", "url": url, "risk": "Low",
            "confidence": "Medium", "evidence": "", "param": param, "attack": attack}


def test_repeated_alerts_on_same_endpoint_are_one_finding():
    raw = [alert("http://t/a?x=1"), alert("http://t/a?x=2"), alert("http://t/a?x=3")]
    assert len(group(raw)) == 1
    rows = run(raw, CTX, FEEDS)
    assert len(rows) == 1 and rows[0]["occurrences"] == 3


def test_distinct_parameters_stay_separate():
    raw = [alert("http://t/a", param="q"), alert("http://t/a", param="id")]
    assert len(group(raw)) == 2
    assert {r["occurrences"] for r in run(raw, CTX, FEEDS)} == {1}


def test_different_paths_stay_separate():
    assert fingerprint(alert("http://t/a")) != fingerprint(alert("http://t/b"))
