"""Feed freshness rule for the status panel (decision D31): fresh within 30 days, stale after, missing if unreadable."""
import datetime as dt
import json

from src import health


def test_fresh_snapshot(tmp_path, monkeypatch):
    (tmp_path / "manifest.json").write_text(json.dumps({"snapshot_date": "2026-11-17"}))
    monkeypatch.setattr(health, "FEEDS", tmp_path)
    assert health.feeds(dt.date(2026, 11, 21))["status"] == "fresh"


def test_stale_after_30_days(tmp_path, monkeypatch):
    (tmp_path / "manifest.json").write_text(json.dumps({"snapshot_date": "2026-01-01"}))
    monkeypatch.setattr(health, "FEEDS", tmp_path)
    out = health.feeds(dt.date(2026, 11, 21))
    assert out["status"] == "stale" and out["age_days"] > 30


def test_missing_manifest_is_reported_not_raised(tmp_path, monkeypatch):
    monkeypatch.setattr(health, "FEEDS", tmp_path)
    assert health.feeds()["status"] == "missing"


def test_postgres_failure_is_reported(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://unused@127.0.0.1:1/unused")
    out = health.postgres()
    assert out["ok"] is False and "error" in out
