"""Browser smoke test of the web UI: pages load, forms render, auth is enforced.

Read-only: creates no targets or scans. Run with WASRA_E2E=1 after `make up`.
"""
import os
import pathlib

import pytest

pytestmark = pytest.mark.skipif(os.environ.get("WASRA_E2E") != "1", reason="needs running stack and browser")
BASE = "http://127.0.0.1:8080"
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
        ctx = browser.new_context(http_credentials={"username": _env("WEB_USER"), "password": _env("WEB_PASSWORD")})
        yield ctx.new_page()
        browser.close()


def test_auth_is_enforced():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        resp = browser.new_page().goto(f"{BASE}/targets")
        assert resp.status == 401
        browser.close()


def test_targets_page_loads(page):
    resp = page.goto(f"{BASE}/targets")
    assert resp.status == 200
    assert page.title()


def test_new_target_form_has_all_fields(page):
    assert page.goto(f"{BASE}/targets/new").status == 200
    for name in ("name", "url"):
        assert page.locator(f"input[name={name}]").count() == 1
    for name in ("criticality", "data_sensitivity", "internet_exposure", "business_impact"):
        assert page.locator(f"select[name={name}]").count() == 1
    assert page.locator("button[type=submit]").count() >= 1


def test_metrics_and_health_endpoints(page):
    assert page.request.get(f"{BASE}/healthz").status == 200
    body = page.request.get(f"{BASE}/metrics").text()
    assert "# HELP" in body or "# TYPE" in body
