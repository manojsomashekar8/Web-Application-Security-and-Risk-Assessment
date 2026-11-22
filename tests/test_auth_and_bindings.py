"""AUTH_MODE rules, binding check, and the allowlist rule in both modes."""
import pytest
from fastapi.testclient import TestClient

from scripts.check_bindings import problems

GOOD = {"services": {"web": {"ports": [{"host_ip": "127.0.0.1", "published": "80", "target": 80}]}}}
BAD = {"services": {"web": {"ports": [{"host_ip": "0.0.0.0", "published": "80", "target": 80}]},
                    "db": {"ports": [{"published": "5432", "target": 5432}]}}}


def test_local_bindings_pass_in_none_mode():
    assert problems(GOOD, "none") == []


def test_public_bindings_are_refused_in_none_mode():
    found = problems(BAD, "none")
    assert len(found) == 2 and any("0.0.0.0:80" in f for f in found) and any("db" in f for f in found)


def test_basic_mode_allows_any_binding():
    assert problems(BAD, "basic") == []


def test_repo_compose_file_passes_the_check():
    import json, pathlib, subprocess
    root = pathlib.Path(__file__).resolve().parents[1]
    out = subprocess.run(["docker", "compose", "config", "--format", "json"], cwd=root,
                         capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        pytest.skip("docker compose not available")
    assert problems(json.loads(out.stdout), "none") == []


@pytest.fixture
def client(monkeypatch):
    # These tests never reach the database (validation and login run first), so a dummy URL is enough.
    monkeypatch.setenv("DATABASE_URL", "postgresql://unused@127.0.0.1:1/unused")
    from src.api import app as app_module
    return TestClient(app_module.app)


@pytest.mark.parametrize("mode", ["none", "basic"])
def test_non_allowlisted_url_rejected_in_both_modes(client, monkeypatch, mode):
    monkeypatch.setenv("AUTH_MODE", mode)
    monkeypatch.setenv("WEB_USER", "admin")
    monkeypatch.setenv("WEB_PASSWORD", "pw")
    auth = ("admin", "pw") if mode == "basic" else None
    r = client.post("/api/targets", json={"name": "x", "url": "http://evil.example", "criticality": "High",
                                          "data_sensitivity": "High", "internet_exposure": "High",
                                          "business_impact": "High"}, auth=auth)
    assert r.status_code == 422 and "allowlist" in r.text


def test_basic_mode_requires_login(client, monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "basic")
    monkeypatch.setenv("WEB_USER", "admin")
    monkeypatch.setenv("WEB_PASSWORD", "pw")
    assert client.get("/api/targets").status_code == 401
    assert client.get("/api/targets", auth=("admin", "wrong")).status_code == 401


@pytest.mark.parametrize("body", [
    {"profile": "custom", "custom": {"attack_strength": "INSANE"}},
    {"profile": "custom", "custom": {"threads_per_host": 999}},
    {"profile": "insane"},
])
def test_scan_request_with_bad_settings_is_refused_before_anything_starts(client, monkeypatch, body):
    monkeypatch.setenv("AUTH_MODE", "none")
    r = client.post("/api/targets/1/scan", json=body)
    assert r.status_code == 422
