"""Each ranking method must follow its own score, not input order or plugin ID.

Synthetic data: alerts differ only in ZAP risk, confidence and CVE mapping, so the methods
should disagree where the factors disagree and agree where they do not.
"""
from src.pipeline import run

CTX = {"criticality": "High", "data_sensitivity": "High", "internet_exposure": "High", "business_impact": "High"}
FEEDS = {"epss": {}, "kev": set(), "cvss": {}, "cve_map": {}}


def alert(plugin, risk, conf, url="http://t/x"):
    return {"pluginId": plugin, "alert": f"alert {plugin}", "cweid": "-1", "url": url,
            "risk": risk, "confidence": conf, "evidence": ""}


def by_plugin(rows):
    return {r["id"]: r for r in rows}


def test_methods_diverge_when_factors_differ():
    # 1: ZAP High/High, no CVE. 2: Informational/Low, no CVE. 3: Medium/Medium but KEV CVE 9.8.
    feeds = {**FEEDS, "cve_map": {"3": ["CVE-2099-0003"]}, "cvss": {"CVE-2099-0003": 9.8},
             "kev": {"CVE-2099-0003"}}
    rows = by_plugin(run([alert("1", "High", "High"), alert("2", "Informational", "Low"),
                          alert("3", "Medium", "Medium")], CTX, feeds))
    assert rows["3"]["rank_cvss_only"] == 1          # CVSS 9.8 wins on CVSS alone
    assert rows["1"]["rank_zap_risk_only"] == 1      # High ZAP risk wins on ZAP alone
    assert rows["3"]["rank_risk"] == 1               # KEV makes E = 1.0, so the framework agrees with CVSS here
    assert rows["3"]["rank_zap_risk_only"] != rows["3"]["rank_cvss_only"]  # the two baselines genuinely differ


def test_identical_inputs_give_deterministic_order_only_as_tie_break():
    # Equal scores: order is fixed by plugin ID then URL, so repeated runs match exactly.
    raw = [alert("7", "High", "High", "http://t/b"), alert("7", "High", "High", "http://t/a")]
    first = [(r["url"], r["rank_risk"]) for r in run(raw, CTX, FEEDS)]
    second = [(r["url"], r["rank_risk"]) for r in run(list(reversed(raw)), CTX, FEEDS)]
    assert first == second


def test_no_cve_means_cvss_and_zap_rankings_agree():
    # Without a CVE, CVSS-only falls back to ZAP risk, so the two baselines must be identical.
    rows = run([alert("1", "High", "Low"), alert("2", "Medium", "High"), alert("3", "Low", "Medium")], CTX, FEEDS)
    assert all(r["rank_cvss_only"] == r["rank_zap_risk_only"] for r in rows)
