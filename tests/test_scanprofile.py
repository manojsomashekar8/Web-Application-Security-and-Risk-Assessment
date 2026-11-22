"""Server-side validation of scan profiles and custom settings (src/scanprofile.py)."""
import pathlib

import pytest

from src.scanprofile import resolve, validate_custom


def test_named_profiles_resolve():
    for name in ("quick", "standard", "deep"):
        assert resolve(name)["profile"] == name


def test_quick_has_no_active_scan_and_standard_does():
    assert resolve("quick")["active_scan"] is False
    assert resolve("standard")["active_scan"] is True


@pytest.mark.parametrize("bad", [
    {"attack_strength": "INSANE"},
    {"attack_strength": "low"},
    {"alert_threshold": "OFF_ALL"},
    {"threads_per_host": 0},
    {"threads_per_host": 25},
    {"max_scan_minutes": 0},
    {"spider_minutes": True},
    {"ajax_spider": "yes"},
    {"unknown_field": 1},
    {"exclude_urls": ["x" * 201]},
    {"exclude_urls": ["a"] * 21},
    {"disable_rules": ["abc"]},
    {"disable_rules": [str(i) for i in range(101)]},
])
def test_bad_values_are_refused(bad):
    with pytest.raises(ValueError):
        validate_custom(bad)


def test_good_custom_settings_pass():
    clean = validate_custom({"attack_strength": "MEDIUM", "threads_per_host": 12, "exclude_urls": [r".*logout.*"],
                             "disable_rules": ["10021"], "active_scan": False})
    assert clean["attack_strength"] == "MEDIUM" and clean["disable_rules"] == ["10021"]


def test_unknown_profile_is_refused():
    with pytest.raises(ValueError):
        resolve("insane")


def test_custom_spider_choice_selects_the_spider_that_runs():
    # The custom form sends spider="ajax" without ajax_spider; the runner must still run the AJAX spider.
    import re
    src = pathlib.Path(__file__).resolve().parents[1].joinpath("src/collectors/zap_client.py").read_text()
    assert 'spider == "ajax" or s.get("ajax_spider")' in src
    assert 'spider = s.get("spider", "traditional")' in src
