import pytest

from src.normalize.normalize import normalize, CONFIDENCE_SCORE, RISK_SCORE

ALERT = {
    "pluginId": "40018", "alert": "SQL Injection", "cweid": "89", "risk": "High",
    "confidence": "Medium", "url": "http://juice-shop:3000/rest/user/login", "evidence": "x",
}


def test_maps_fields_and_scores():
    f = normalize(ALERT)
    assert (f.id, f.type, f.cwe) == ("40018", "SQL Injection", 89)
    assert f.owasp == "A03:2021 Injection"
    assert f.zap_risk_score == 0.8 and f.zap_confidence_score == 0.6


def test_missing_cwe_becomes_none_and_no_owasp():
    f = normalize({**ALERT, "cweid": "-1"})
    assert f.cwe is None and f.owasp is None


def test_false_positive_confidence_is_zero():
    assert normalize({**ALERT, "confidence": "False Positive"}).zap_confidence_score == 0.0


@pytest.mark.parametrize("risk", list(RISK_SCORE))
def test_every_zap_risk_has_score(risk):
    assert 0 <= normalize({**ALERT, "risk": risk}).zap_risk_score <= 1


def test_unknown_risk_raises():
    with pytest.raises(KeyError):
        normalize({**ALERT, "risk": "Critical"})
