"""Browser flow: create target -> scan Juice Shop -> view ranked findings -> open explanation -> download report.

Run with WASRA_E2E=1 after `make up`. Needs Playwright browsers (`playwright install chromium`).
"""
import os
import re

import pytest

pytestmark = pytest.mark.skipif(os.environ.get("WASRA_E2E") != "1", reason="needs running stack and browser")
BASE = "http://127.0.0.1:8080"


def test_full_flow():
    from playwright.sync_api import expect, sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(http_credentials={"username": os.environ["WEB_USER"],
                                                    "password": os.environ["WEB_PASSWORD"]})
        page = ctx.new_page()
        page.goto(f"{BASE}/targets/new")
        page.fill("input[name=name]", "DVWA (e2e)")
        page.fill("input[name=url]", "http://dvwa:80")
        for k in ("criticality", "data_sensitivity", "internet_exposure", "business_impact"):
            page.select_option(f"select[name={k}]", "High")
        page.click("button[type=submit]")
        page.click("text=Start scan")
        expect(page.locator("#status")).to_have_text("done", timeout=3_600_000)
        page.click("text=View ranked findings")
        page.wait_for_load_state("networkidle")  # the row toggle script must be attached before the click
        page.locator("tr.row").first.click()
        expect(page.locator("tr[id^=d]:not([hidden])")).to_contain_text(re.compile(r"Risk [0-9.]+ \((High|Medium|Low)\)"))
        href = page.get_attribute("text=JSON report", "href")
        resp = ctx.request.get(f"{BASE}{href}")
        assert resp.status == 200 and resp.json()["findings"]
        browser.close()
