"""Grafana check: dashboards provisioned, Prometheus and read-only Postgres datasources healthy.
Runs only with WASRA_INTEGRATION=1 (stack up)."""
import os

import pytest
import requests

pytestmark = pytest.mark.skipif(os.environ.get("WASRA_INTEGRATION") != "1", reason="needs running stack")
G = "http://127.0.0.1:3001"
AUTH = ("admin", os.environ.get("GRAFANA_ADMIN_PASSWORD", ""))


def test_anonymous_access_disabled():
    assert requests.get(f"{G}/api/search", timeout=10).status_code == 401


def test_dashboards_provisioned():
    titles = {d["title"] for d in requests.get(f"{G}/api/search", auth=AUTH, timeout=10).json()}
    assert {"WASRA overview", "WASRA ranking stability", "WASRA validation"} <= titles


@pytest.mark.parametrize("uid", ["prom", "wasra-db"])
def test_datasource_healthy(uid):
    r = requests.get(f"{G}/api/datasources/uid/{uid}/health", auth=AUTH, timeout=30)
    assert r.json().get("status") == "OK", r.text


def test_kev_alert_rule_provisioned():
    rules = requests.get(f"{G}/api/v1/provisioning/alert-rules", auth=AUTH, timeout=10).json()
    assert any(r["uid"] == "kev-finding" for r in rules)
