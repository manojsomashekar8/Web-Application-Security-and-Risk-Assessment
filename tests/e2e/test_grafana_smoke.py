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


REQUIRED_OVERVIEW_PANELS = {
    "Findings by framework band (latest scan per target)",
    "Scan duration per stage (seconds)",
    "Findings with n/a enrichment (no CVSS)",
    "Top-10 overlap: framework vs CVSS-only",
}


def test_overview_has_target_variable_and_new_panels(page):
    found = page.request.get(f"{BASE}/api/search?query=WASRA%20overview").json()
    uid = next(d["uid"] for d in found if d["title"] == "WASRA overview")
    dash = page.request.get(f"{BASE}/api/dashboards/uid/{uid}").json()["dashboard"]
    assert any(v["name"] == "target" for v in dash["templating"]["list"])
    titles = {p["title"] for p in dash["panels"]}
    assert REQUIRED_OVERVIEW_PANELS <= titles, REQUIRED_OVERVIEW_PANELS - titles


def test_every_provisioned_dashboard_is_present(page):
    titles = {d["title"] for d in page.request.get(f"{BASE}/api/search?type=dash-db").json()}
    assert {"WASRA overview", "WASRA ranking stability", "WASRA validation"} <= titles


def _ds_query(page, sql: str) -> dict:
    """Run one SQL query through Grafana's own query API (the same path the panels use)."""
    body = {"queries": [{"refId": "A", "datasource": {"type": "postgres", "uid": "wasra-db"},
                         "rawSql": sql, "format": "table", "rawQuery": True}],
            "from": "now-6h", "to": "now"}
    return page.request.post(f"{BASE}/api/ds/query", data=body).json()["results"]["A"]


def _validation_sql(page) -> list[tuple[str, str]]:
    found = page.request.get(f"{BASE}/api/search?query=WASRA%20validation").json()
    uid = next(d["uid"] for d in found if d["title"] == "WASRA validation")
    dash = page.request.get(f"{BASE}/api/dashboards/uid/{uid}").json()["dashboard"]
    return [(p["title"], t["rawSql"]) for p in dash["panels"] for t in p.get("targets", []) if t.get("rawSql")]


def test_validation_panels_load(page):
    for title, sql in _validation_sql(page):
        result = _ds_query(page, sql.replace("$run_date", "latest"))
        assert "error" not in result, f"{title}: {result.get('error')}"


def test_latest_run_filter_returns_one_row_per_target(page):
    sql = next(s for t, s in _validation_sql(page) if t.startswith("Validation results"))
    rows = _ds_query(page, sql.replace("$run_date", "latest"))["frames"][0]["data"]["values"]
    targets = rows[0]
    distinct = _ds_query(page, "SELECT count(DISTINCT target) AS n FROM validation_results")["frames"][0]["data"]["values"][0][0]
    assert len(targets) == len(set(targets)) == distinct, (len(targets), distinct)
