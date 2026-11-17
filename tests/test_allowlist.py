import pytest

from src.service import allowed_targets, validate_target

GOOD_CTX = {"criticality": "High", "data_sensitivity": "Low", "internet_exposure": "Medium", "business_impact": "High"}


def test_allowlist_parsed_from_targets_doc():
    assert {"http://juice-shop:3000", "http://dvwa:80", "http://webgoat:8080/WebGoat/", "http://bwapp:80"} \
        <= allowed_targets()


def test_public_host_is_rejected():
    errs = validate_target("x", "https://example.com", GOOD_CTX)
    assert any("allowlist" in e for e in errs)


@pytest.mark.parametrize("bad", ["", "Critical", "high", None])
def test_bad_context_value_rejected(bad):
    errs = validate_target("x", "http://juice-shop:3000", {**GOOD_CTX, "criticality": bad})
    assert any(e.startswith("criticality") for e in errs)


def test_missing_name_rejected():
    assert any(e.startswith("name") for e in validate_target("   ", "http://juice-shop:3000", GOOD_CTX))


def test_valid_target_has_no_errors():
    assert validate_target("Juice Shop", "http://juice-shop:3000", GOOD_CTX) == []
