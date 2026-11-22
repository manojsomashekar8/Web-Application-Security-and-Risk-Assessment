"""Versioned scan export and import (format 'wasra-scan', format_version 1).

Import never trusts stored scores: every finding is recomputed from the raw alerts with the current code.
Nothing in the file is executed or evaluated; it is parsed as plain JSON and checked field by field.
"""
import datetime as dt
import hashlib
import json

from src.enrich.enrich import FEED_FILES
from src.normalize.normalize import CONFIDENCE_SCORE, RISK_SCORE
from src.scanprofile import FIELDS, PROFILES, validate_custom

FORMAT = "wasra-scan"
FORMAT_VERSION = 1
MAX_BYTES = 25 * 1024 * 1024  # 25 MB: larger files are refused before they are parsed
MAX_ALERTS = 50_000
TARGET_FIELDS = ("criticality", "data_sensitivity", "internet_exposure", "business_impact")


class ImportError_(ValueError):
    """A clear, user-facing reason the file was refused."""


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ImportError_(msg)


def parse(raw: bytes) -> dict:
    _require(len(raw) <= MAX_BYTES, f"file is larger than {MAX_BYTES // (1024 * 1024)} MB")
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ImportError_(f"not valid JSON: {exc}") from None
    _require(isinstance(data, dict), "top level must be a JSON object")
    _require(data.get("format") == FORMAT, f"format must be {FORMAT!r}")
    version = data.get("format_version")
    _require(version == FORMAT_VERSION, f"unsupported format_version {version!r}; this app reads {FORMAT_VERSION}")
    return data


def validate(data: dict) -> dict:
    """Check the shape and values of a parsed export. Returns the cleaned pieces the importer needs."""
    t = data.get("target")
    _require(isinstance(t, dict), "target: missing or not an object")
    _require(isinstance(t.get("name"), str) and 0 < len(t["name"]) <= 200, "target.name: 1 to 200 characters")
    _require(isinstance(t.get("url"), str) and t["url"].startswith("http"), "target.url: must be a web address")
    for k in TARGET_FIELDS:
        _require(t.get(k) in ("Low", "Medium", "High"), f"target.{k}: must be Low, Medium or High")
    s = data.get("scan")
    _require(isinstance(s, dict), "scan: missing or not an object")
    profile = s.get("profile")
    # "unrecorded": the scan's settings were not saved (a raw alert file re-imported). Stored as such, never guessed.
    _require(profile in PROFILES or profile in ("custom", "unrecorded"), f"scan.profile: unknown profile {profile!r}")
    settings = s.get("settings")
    _require(isinstance(settings, dict), "scan.settings: must be an object")
    clean_settings = validate_custom({k: v for k, v in settings.items() if k in FIELDS}) if profile == "custom" else {}
    alerts = s.get("raw_alerts")
    _require(isinstance(alerts, list) and 0 < len(alerts) <= MAX_ALERTS,
             f"scan.raw_alerts: a list of 1 to {MAX_ALERTS} alerts")
    for i, a in enumerate(alerts):
        _require(isinstance(a, dict), f"raw_alerts[{i}]: not an object")
        for key in ("pluginId", "alert", "url", "risk", "confidence"):
            _require(key in a, f"raw_alerts[{i}]: missing {key}")
        _require(a["risk"] in RISK_SCORE, f"raw_alerts[{i}].risk: {a['risk']!r} is not a ZAP risk level")
        _require(a["confidence"] in CONFIDENCE_SCORE, f"raw_alerts[{i}].confidence: not a ZAP confidence")
        _require(isinstance(a["url"], str) and len(a["url"]) <= 2000, f"raw_alerts[{i}].url: too long or not text")
    stage = s.get("stage_seconds") or {}
    _require(isinstance(stage, dict) and all(isinstance(v, (int, float)) for v in stage.values()),
             "scan.stage_seconds: numbers only")
    snap = data.get("feed_snapshot") or {}
    _require(isinstance(snap, dict), "feed_snapshot: must be an object")
    return {"target": t, "profile": profile, "settings": clean_settings, "alerts": alerts,
            "stage_seconds": stage, "feed_snapshot": snap}


def content_hash(data: dict) -> str:
    """Identifies this scan's content: same target, same profile, same raw alerts, same time -> same hash."""
    body = {"target": data["target"]["url"], "started_at": data["scan"].get("started_at"),
            "alerts": data["scan"]["raw_alerts"]}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def export_document(scan: dict, target: dict, findings_count: int) -> dict:
    """The versioned document for one finished scan. Scores are included only as a record; import recomputes them."""
    return {
        "format": FORMAT, "format_version": FORMAT_VERSION,
        "exported_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "target": {k: target[k] for k in ("name", "url", *TARGET_FIELDS)},
        "scan": {"profile": (scan["settings"] or {}).get("profile", "deep"), "settings": scan["settings"] or {},
                 "started_at": scan["started_at"].isoformat() if scan["started_at"] else None,
                 "finished_at": scan["finished_at"].isoformat() if scan["finished_at"] else None,
                 "stage_seconds": scan["stage_seconds"] or {}, "raw_alerts": scan["raw_alerts"],
                 "unique_findings_when_exported": findings_count},
        "feed_snapshot": {"files": list(FEED_FILES.values())},
    }
