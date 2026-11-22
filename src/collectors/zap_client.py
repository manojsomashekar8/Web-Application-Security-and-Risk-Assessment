"""Minimal ZAP REST client: spider, passive wait, active scan, alert paging."""
import os
import time

import requests

ZAP_URL = os.environ.get("ZAP_URL", "http://127.0.0.1:8090")
POLL_SECONDS = 5
POLICY = "Default Policy"


class ZapClient:
    def __init__(self, api_key: str, base: str = ZAP_URL):
        self.key = api_key
        self.base = base.rstrip("/")

    def _get(self, path: str, **params) -> dict:
        params["apikey"] = self.key
        r = requests.get(f"{self.base}{path}", params=params, timeout=60)
        r.raise_for_status()
        return r.json()

    def _wait(self, status_path: str, scan_id: str) -> None:
        while int(self._get(status_path, scanId=scan_id)["status"]) < 100:
            time.sleep(POLL_SECONDS)

    def set_cookie(self, cookie: str | None) -> None:
        """Send a fixed Cookie header on every request (session seeded by collectors/auth.py)."""
        try:  # ZAP answers 400 when no rule with this description exists yet (first run)
            self._get("/JSON/replacer/action/removeRule/", description="wasra-auth")
        except requests.HTTPError:
            pass
        if cookie:
            self._get("/JSON/replacer/action/addRule/", description="wasra-auth", enabled="true",
                      matchType="REQ_HEADER", matchRegex="false", matchString="Cookie", replacement=cookie,
                      initiators="")

    def apply_settings(self, s: dict) -> None:
        """Set ZAP options for one scan from a validated profile (src/scanprofile.py). Values are per run."""
        self._get("/JSON/ascan/action/setOptionMaxScanDurationInMins/", Integer=s.get("max_scan_minutes") or 0)
        self._get("/JSON/ascan/action/setOptionMaxRuleDurationInMins/", Integer=s.get("max_rule_minutes") or 0)
        self._get("/JSON/ascan/action/setOptionThreadPerHost/", Integer=s.get("threads_per_host") or 24)
        self._get("/JSON/ascan/action/setOptionDelayInMs/", Integer=s.get("delay_ms") or 0)
        self._get("/JSON/spider/action/setOptionMaxDuration/", Integer=s.get("spider_minutes") or 0)
        self._get("/JSON/ajaxSpider/action/setOptionBrowserId/", String="htmlunit")  # shortcut: installed default is firefox-headless, kept for comparability (D53)
        scanners = self._get("/JSON/ascan/view/scanners/", scanPolicyName=POLICY)["scanners"]
        ids = ",".join(str(x["id"]) for x in scanners)
        self._get("/JSON/ascan/action/enableScanners/", ids=ids, scanPolicyName=POLICY)
        if s.get("disable_rules"):
            self._get("/JSON/ascan/action/disableScanners/", ids=",".join(s["disable_rules"]), scanPolicyName=POLICY)
        if s.get("attack_strength"):
            for x in scanners:
                self._get("/JSON/ascan/action/setScannerAttackStrength/", id=x["id"],
                          attackStrength=s["attack_strength"], scanPolicyName=POLICY)
        if s.get("alert_threshold"):
            for x in scanners:
                self._get("/JSON/ascan/action/setScannerAlertThreshold/", id=x["id"],
                          alertThreshold=s["alert_threshold"], scanPolicyName=POLICY)
        for url in s.get("exclude_urls") or []:
            self._get("/JSON/spider/action/excludeFromScan/", regex=url)
            self._get("/JSON/ascan/action/excludeFromScan/", regex=url)

    def clear_exclusions(self) -> None:
        self._get("/JSON/spider/action/clearExcludedFromScan/")
        self._get("/JSON/ascan/action/clearExcludedFromScan/")

    def run(self, target: str, cookie: str | None = None, settings: dict | None = None) -> dict:
        """Run the stages the profile asks for; return how long each one took, in seconds."""
        from src.scanprofile import resolve
        s = settings or resolve("deep")
        timings, clock = {}, time.monotonic
        self.set_cookie(cookie)
        self._get("/JSON/core/action/newSession/", name="wasra", overwrite="true")  # clean state per run
        try:
            self.apply_settings(s)
            spider = s.get("spider", "traditional")  # the spider choice decides which spider runs
            if spider == "traditional":
                t0 = clock()
                sid = self._get("/JSON/spider/action/scan/", url=target, maxChildren=0, recurse=True)["scan"]
                self._wait("/JSON/spider/view/status/", sid)
                timings["spider"] = clock() - t0
            if spider == "ajax" or s.get("ajax_spider"):
                t0 = clock()
                self._get("/JSON/ajaxSpider/action/scan/", url=target, browserId="htmlunit",
                          maxDuration=s.get("ajax_minutes", 10), maxCrawlDepth=s.get("ajax_depth", 5))
                while self._get("/JSON/ajaxSpider/view/status/")["status"] != "stopped":
                    time.sleep(POLL_SECONDS)
                timings["ajax_spider"] = clock() - t0
            t0 = clock()
            while int(self._get("/JSON/pscan/view/recordsToScan/")["recordsToScan"]) > 0:
                time.sleep(POLL_SECONDS)
            timings["passive_wait"] = clock() - t0
            if s.get("active_scan"):
                t0 = clock()
                aid = self._get("/JSON/ascan/action/scan/", url=target, recurse=True, inScopeOnly=False)["scan"]
                self._wait("/JSON/ascan/view/status/", aid)
                timings["active_scan"] = clock() - t0
        finally:
            self.clear_exclusions()
        return {k: round(v, 1) for k, v in timings.items()}

    def generate_report(self, file_name: str, template: str = "traditional-html") -> str:
        """ZAP's own report for the current session (the latest scan). Written to ZAP's /zap/reports folder,
        which is results/zap-reports on the host. Returns the file name."""
        self._get("/JSON/reports/action/generate/", title="WASRA scan report", template=template,
                  reportDir="/zap/reports", reportFileName=file_name,
                  description="Generated by WASRA when the scan finished")
        return file_name

    def alerts(self, baseurl: str, page: int = 500) -> list[dict]:
        out, start = [], 0
        while True:
            batch = self._get("/JSON/core/view/alerts/", baseurl=baseurl, start=start, count=page)["alerts"]
            out += batch
            if len(batch) < page:
                return out
            start += page
