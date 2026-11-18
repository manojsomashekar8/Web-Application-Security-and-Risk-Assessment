"""Browser smoke test of Grafana: login works, data source is healthy, a dashboard loads.

Run with WASRA_E2E=1 after `make up`.
"""
import os
import pathlib

import pytest

pytestmark = pytest.mark.skipif(os.environ.get("WASRA_E2E") != "1", reason="needs running stack and browser")
BASE = "http://127.0.0.1:3001"
ENV = pathlib.Path(__file__).resolve().parents[2] / ".env"


def _env(key: str) -> str:
    for line in ENV.read_text().splitlines():
        if line.startswith(key + "="):
            return line.split("=", 1)[1]
    raise KeyError(key)


@pytest.fixture(scope="module")
def page():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page()
        pg.goto(f"{BASE}/login")
        pg.fill("input[name=user]", "admin")
        pg.fill("input[name=password]", _env("GRAFANA_ADMIN_PASSWORD"))
        pg.click("button[type=submit]")
        pg.wait_for_url(lambda url: "/login" not in url, timeout=30_000)
        yield pg
        browser.close()


def test_grafana_health(page):
    assert page.request.get(f"{BASE}/api/health").status == 200


def test_prometheus_datasource_healthy(page):
    ds = page.request.get(f"{BASE}/api/datasources").json()
    prom = [d for d in ds if d.get("type") == "prometheus"]
    assert prom, "no Prometheus data source provisioned"
    res = page.request.get(f"{BASE}/api/datasources/uid/{prom[0]['uid']}/health").json()
    assert res.get("status") == "OK", res


def test_dashboard_loads(page):
    found = page.request.get(f"{BASE}/api/search?type=dash-db").json()
    assert found, "no dashboards provisioned"
    page.goto(f"{BASE}{found[0]['url']}")
    page.wait_for_load_state("networkidle", timeout=60_000)
    assert "login" not in page.url
