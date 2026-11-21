"""Browser test of the React frontend (port 80): targets list, new target form, results page.

Read-only. Run with WASRA_E2E=1 after `make up`. Needs at least one finished scan for the results check.
"""
import os
import pathlib

import pytest

pytestmark = pytest.mark.skipif(os.environ.get("WASRA_E2E") != "1", reason="needs running stack and browser")
BASE = "http://127.0.0.1:80"
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
        pg = ctx.new_page()
        pg.errors = []
        pg.on("pageerror", lambda e: pg.errors.append(str(e)))
        yield pg
        browser.close()


def test_targets_page_renders(page):
    page.goto(f"{BASE}/")
    page.wait_for_load_state("networkidle")
    assert page.get_by_role("heading", name="Targets").is_visible()
    assert page.get_by_role("link", name="Add target").is_visible()


def test_new_target_form_offers_allowlisted_sites(page):
    page.goto(f"{BASE}/targets/new")
    page.wait_for_load_state("networkidle")
    options = page.locator("select").first.locator("option").all_inner_texts()
    assert any("juice-shop" in o for o in options)
    assert page.locator("select").count() == 5  # website + four context factors


def test_results_page_shows_summary_and_expands_row(page):
    page.goto(f"{BASE}/scans/1")
    page.wait_for_load_state("networkidle")
    assert page.get_by_text("Raw alerts").is_visible()
    assert page.get_by_text("Unique findings").is_visible()
    page.locator("tr.clickable").first.click()
    assert page.get_by_text("Why this score:").is_visible()


def test_no_uncaught_errors(page):
    assert page.errors == []
