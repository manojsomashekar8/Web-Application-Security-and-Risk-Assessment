from src.scoring.compare import kendall_tau, top_k_overlap
from src.pipeline import run

CTX = {"criticality": "Medium", "data_sensitivity": "Medium", "internet_exposure": "Medium", "business_impact": "Medium"}
FEEDS = {"epss": {}, "kev": set(), "cvss": {}, "cve_map": {}}
ALERTS = [
    {"pluginId": "1", "alert": "A", "cweid": "89", "risk": "High", "confidence": "High", "url": "u1", "evidence": ""},
    {"pluginId": "2", "alert": "B", "cweid": "79", "risk": "Low", "confidence": "Low", "url": "u2", "evidence": ""},
    {"pluginId": "3", "alert": "C", "cweid": "-1", "risk": "Medium", "confidence": "Medium", "url": "u3", "evidence": ""},
]


def test_tau_identical_and_reversed():
    a = {"x": 1, "y": 2, "z": 3}
    assert kendall_tau(a, a) == 1.0
    assert kendall_tau(a, {"x": 3, "y": 2, "z": 1}) == -1.0


def test_top_k_overlap_full_and_none():
    a = {"x": 1, "y": 2}
    assert top_k_overlap(a, a, k=2) == 1.0
    assert top_k_overlap(a, {"x": 2, "y": 1}, k=1) == 0.0


def test_pipeline_is_deterministic_and_ranked():
    a = run(ALERTS, CTX, FEEDS)
    b = run(ALERTS, CTX, FEEDS)
    assert a == b
    assert [r["id"] for r in a] == ["1", "3", "2"]  # High > Medium > Low risk
    assert sorted(r["rank_risk"] for r in a) == [1, 2, 3]
    assert all("explanation" in r and "context" in r for r in a)
