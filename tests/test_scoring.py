import random

import pytest

from src.scoring.score import LEVEL, risk, score_finding, weighted_sum, band, load_weights

CTX_HI = {"criticality": "High", "data_sensitivity": "High", "internet_exposure": "High", "business_impact": "High"}
CTX_LO = {k: "Low" for k in CTX_HI}
W = {"S": 0.4, "E": 0.3, "C": 0.3}


def fnd(**kw):
    base = {"cvss": None, "kev": False, "epss": None, "zap_risk_score": 0.5, "zap_confidence_score": 0.6}
    return {**base, **kw}


def test_worked_example_matches_spec():
    # S=0.5 (ZAP Medium), E=0.6 (ZAP Medium confidence), all context Medium (0.66)
    ctx = {k: "Medium" for k in CTX_HI}
    r = score_finding(fnd(), ctx, W)
    assert r["S"] == 0.5 and r["E"] == 0.6
    assert r["I"] == pytest.approx(0.5 * 0.66)
    assert r["L"] == pytest.approx(0.6 * 0.66)
    assert r["risk"] == pytest.approx(100 * 0.6 * 0.66 * 0.5 * 0.66)


def test_kev_forces_exploitability_one():
    assert score_finding(fnd(kev=True, epss=0.01), CTX_HI, W)["E"] == 1.0


def test_epss_used_before_zap_confidence():
    assert score_finding(fnd(epss=0.42), CTX_HI, W)["E"] == 0.42


def test_cvss_overrides_zap_risk_for_severity():
    assert score_finding(fnd(cvss=9.8), CTX_HI, W)["S"] == pytest.approx(0.98)


def test_max_and_min_bounds():
    assert score_finding(fnd(cvss=10.0, kev=True), CTX_HI, W)["risk"] == pytest.approx(100.0)
    assert score_finding(fnd(zap_risk_score=0.0, zap_confidence_score=0.0), CTX_LO, W)["risk"] == 0.0


def test_missing_context_value_raises():
    with pytest.raises(KeyError):
        score_finding(fnd(), {"criticality": "High"}, W)


def test_bad_context_level_raises():
    with pytest.raises(KeyError):
        score_finding(fnd(), {**CTX_HI, "criticality": "Critical"}, W)


def test_risk_always_in_0_100_and_deterministic():
    rng = random.Random(42)  # fixed seed
    levels = list(LEVEL)
    for _ in range(2000):
        f = fnd(cvss=rng.choice([None, rng.uniform(0, 10)]), kev=rng.random() < 0.3,
                epss=rng.choice([None, rng.random()]), zap_risk_score=rng.random(),
                zap_confidence_score=rng.random())
        ctx = {k: rng.choice(levels) for k in CTX_HI}
        a, b = score_finding(f, ctx, W), score_finding(f, ctx, W)
        assert 0 <= a["risk"] <= 100
        assert a == b


def test_monotonic_in_each_input():
    base = fnd(zap_risk_score=0.5, zap_confidence_score=0.5)
    ctx = {k: "Medium" for k in CTX_HI}
    for field, lo, hi in [("zap_risk_score", 0.2, 0.8), ("zap_confidence_score", 0.3, 0.9)]:
        assert score_finding({**base, field: lo}, ctx, W)["risk"] < score_finding({**base, field: hi}, ctx, W)["risk"]
    for key in CTX_HI:
        lo_ctx, hi_ctx = {**ctx, key: "Low"}, {**ctx, key: "High"}
        assert score_finding(base, lo_ctx, W)["risk"] < score_finding(base, hi_ctx, W)["risk"]


def test_band_boundaries():
    assert (band(60), band(59.99), band(30), band(29.99)) == ("High", "Medium", "Medium", "Low")


def test_explanation_mentions_factors():
    text = score_finding(fnd(kev=True, cvss=10.0), CTX_HI, W)["explanation"]
    assert text.startswith("High:") and "KEV-listed" in text and "internet exposure High" in text


def test_weighted_sum_formula():
    assert weighted_sum(1.0, 1.0, CTX_HI, W) == pytest.approx(100.0)
    assert weighted_sum(0, 0, CTX_LO, W) == pytest.approx(100 * 0.3 * 0.33)


def test_default_weights_are_equal_spec_values():
    assert load_weights() == W
