"""Results page: default sort is framework risk, descending; clicking a header reverses it.

Run with WASRA_E2E=1 after `make up`. Skips if there is no finished scan to look at.
"""
import os

import pytest

pytestmark = pytest.mark.skipif(os.environ.get("WASRA_E2E") != "1", reason="needs running stack and browser")
BASE = "http://127.0.0.1"


def _risks(page) -> list[float]:
    return [float(c.inner_text()) for c in page.locator("table tbody tr.clickable td:nth-child(4)").all()]


def test_default_sort_is_risk_descending_and_header_reverses():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page()
        scan = page.request.get("http://127.0.0.1:8080/api/targets/1/latest-scan").json()
        if not scan or scan.get("status") != "done":
            pytest.skip("no finished scan on target 1")
        page.goto(f"{BASE}/scans/{scan['id']}")
        page.wait_for_load_state("networkidle")
        risks = _risks(page)
        assert risks == sorted(risks, reverse=True), "default order is not risk descending"
        page.locator('th.sortable:text-is("Risk")').first.click()
        assert _risks(page) == sorted(risks), "second click does not reverse the order"
        b.close()
