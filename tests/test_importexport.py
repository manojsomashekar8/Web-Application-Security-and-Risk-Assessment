"""Import validation: bad version, corrupt file, oversize file, malformed alerts are refused with clear messages."""
import json

import pytest

from src import importexport as ie

GOOD_ALERT = {"pluginId": "10038", "alert": "CSP", "url": "http://dvwa:80/", "risk": "Medium",
              "confidence": "High", "cweid": "693"}


def doc(**over):
    base = {"format": "wasra-scan", "format_version": 1, "exported_at": "2026-11-22T00:00:00+00:00",
            "target": {"name": "DVWA", "url": "http://dvwa:80", "criticality": "High", "data_sensitivity": "High",
                       "internet_exposure": "High", "business_impact": "High"},
            "scan": {"profile": "deep", "settings": {}, "stage_seconds": {"spider": 1.0},
                     "raw_alerts": [GOOD_ALERT]},
            "feed_snapshot": {}}
    base.update(over)
    return base


def raw(d) -> bytes:
    return json.dumps(d).encode()


def test_valid_document_passes():
    v = ie.validate(ie.parse(raw(doc())))
    assert v["profile"] == "deep" and len(v["alerts"]) == 1


@pytest.mark.parametrize("version", [0, 2, "1", None])
def test_unknown_format_version_is_refused(version):
    with pytest.raises(ie.ImportError_, match="format_version"):
        ie.parse(raw(doc(format_version=version)))


def test_corrupt_file_is_refused():
    with pytest.raises(ie.ImportError_, match="not valid JSON"):
        ie.parse(b"{not json")


def test_wrong_format_name_is_refused():
    with pytest.raises(ie.ImportError_, match="format must be"):
        ie.parse(raw(doc(format="something-else")))


def test_oversize_file_is_refused_before_parsing():
    with pytest.raises(ie.ImportError_, match="larger than"):
        ie.parse(b" " * (ie.MAX_BYTES + 1))


@pytest.mark.parametrize("change,msg", [
    ({"risk": "Insane"}, "risk"),
    ({"confidence": "Certain"}, "confidence"),
    ({"url": "x" * 2001}, "url"),
])
def test_malformed_alert_is_refused(change, msg):
    bad = {**GOOD_ALERT, **change}
    with pytest.raises(ie.ImportError_, match=msg):
        ie.validate(ie.parse(raw(doc(scan={"profile": "deep", "settings": {}, "raw_alerts": [bad]}))))


def test_unknown_profile_is_refused():
    d = doc()
    d["scan"]["profile"] = "insane"
    with pytest.raises(ie.ImportError_, match="unknown profile"):
        ie.validate(ie.parse(raw(d)))


def test_bad_context_rating_is_refused():
    d = doc()
    d["target"]["criticality"] = "Extreme"
    with pytest.raises(ie.ImportError_, match="criticality"):
        ie.validate(ie.parse(raw(d)))


def test_content_hash_is_stable_for_the_same_scan():
    a = ie.content_hash(ie.parse(raw(doc())))
    b = ie.content_hash(ie.parse(raw(doc())))
    assert a == b
