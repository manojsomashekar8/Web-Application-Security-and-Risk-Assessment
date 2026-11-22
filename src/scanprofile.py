"""Scan profiles and custom scan settings, validated on the server. Only the fields below are accepted.

Bounds follow docs/ZAP_NOTES.md. INSANE strength and 'no limit' (0) are deliberately not offered.
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROFILES = {k: v for k, v in json.loads((ROOT / "configs" / "scan_profiles.json").read_text()).items()
            if not k.startswith("_")}

FIELDS = {  # name -> (allowed values or (min, max))
    "spider": {"traditional", "ajax", "none"},
    "spider_minutes": (1, 60),
    "ajax_spider": (False, True),
    "ajax_minutes": (1, 60),
    "ajax_depth": (1, 10),
    "active_scan": (False, True),
    "attack_strength": {"LOW", "MEDIUM", "HIGH", "DEFAULT"},
    "alert_threshold": {"OFF", "LOW", "MEDIUM", "HIGH", "DEFAULT"},
    "max_scan_minutes": (1, 240),
    "max_rule_minutes": (1, 60),
    "threads_per_host": (1, 24),
    "delay_ms": (0, 2000),
    "exclude_urls": None,  # list of regex strings
    "disable_rules": None,  # list of numeric ZAP plugin ids
}
MAX_EXCLUDES, MAX_EXCLUDE_LEN, MAX_DISABLED = 20, 200, 100


def _check_one(name: str, value):
    rule = FIELDS[name]
    if isinstance(rule, set):
        if value not in rule:
            raise ValueError(f"{name}: must be one of {sorted(rule)}")
    elif isinstance(rule, tuple) and rule[0] is False:
        if not isinstance(value, bool):
            raise ValueError(f"{name}: must be true or false")
    elif isinstance(rule, tuple):
        if not isinstance(value, int) or isinstance(value, bool) or not rule[0] <= value <= rule[1]:
            raise ValueError(f"{name}: must be a whole number from {rule[0]} to {rule[1]}")
    return value


def validate_custom(settings: dict) -> dict:
    """Return a clean copy of a custom scan request, or raise ValueError naming the bad field."""
    unknown = set(settings) - set(FIELDS)
    if unknown:
        raise ValueError(f"unknown field(s): {sorted(unknown)}")
    clean = {}
    for name, value in settings.items():
        if name == "exclude_urls":
            if not isinstance(value, list) or len(value) > MAX_EXCLUDES:
                raise ValueError(f"exclude_urls: a list of at most {MAX_EXCLUDES} patterns")
            if any(not isinstance(p, str) or not p or len(p) > MAX_EXCLUDE_LEN for p in value):
                raise ValueError(f"exclude_urls: each pattern is 1 to {MAX_EXCLUDE_LEN} characters")
            clean[name] = list(value)
        elif name == "disable_rules":
            if not isinstance(value, list) or len(value) > MAX_DISABLED:
                raise ValueError(f"disable_rules: a list of at most {MAX_DISABLED} ids")
            if any(not isinstance(i, str) or not i.isdigit() for i in value):
                raise ValueError("disable_rules: each id must be a number (ZAP plugin id)")
            clean[name] = list(value)
        else:
            clean[name] = _check_one(name, value)
    return clean


def resolve(profile: str | None, custom: dict | None = None) -> dict:
    """The exact settings a scan will use: a named profile, or 'custom' with validated fields."""
    if profile == "custom":
        base = {"description": "Custom settings", **validate_custom(custom or {})}
        base.setdefault("spider", "traditional")
        base.setdefault("active_scan", True)
        return {"profile": "custom", **base}
    if profile not in PROFILES:
        raise ValueError(f"profile must be one of {sorted(PROFILES) + ['custom']}")
    return {"profile": profile, **PROFILES[profile]}
