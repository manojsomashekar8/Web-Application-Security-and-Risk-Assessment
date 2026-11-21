"""Minimal ZAP REST client: spider, passive wait, active scan, alert paging."""
import os
import time

import requests

ZAP_URL = os.environ.get("ZAP_URL", "http://127.0.0.1:8090")
POLL_SECONDS = 5


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

    def run(self, target: str, cookie: str | None = None) -> dict:
        """Run the four stages and return how long each took, in seconds."""
        timings, clock = {}, time.monotonic
        self.set_cookie(cookie)
        self._get("/JSON/core/action/newSession/", name="wasra", overwrite="true")  # clean state per run
        t0 = clock()
        sid = self._get("/JSON/spider/action/scan/", url=target, maxChildren=0, recurse=True)["scan"]
        self._wait("/JSON/spider/view/status/", sid)
        timings["spider"] = clock() - t0
        # AJAX spider renders client-side routes (SPA API endpoints the traditional spider misses).
        t0 = clock()
        self._get("/JSON/ajaxSpider/action/scan/", url=target, browserId="htmlunit",
                  maxDuration=10, maxCrawlDepth=5)
        while self._get("/JSON/ajaxSpider/view/status/")["status"] != "stopped":
            time.sleep(POLL_SECONDS)
        timings["ajax_spider"] = clock() - t0
        t0 = clock()
        while int(self._get("/JSON/pscan/view/recordsToScan/")["recordsToScan"]) > 0:
            time.sleep(POLL_SECONDS)
        timings["passive_wait"] = clock() - t0
        t0 = clock()
        aid = self._get("/JSON/ascan/action/scan/", url=target, recurse=True, inScopeOnly=False)["scan"]
        self._wait("/JSON/ascan/view/status/", aid)
        timings["active_scan"] = clock() - t0
        return {k: round(v, 1) for k, v in timings.items()}

    def alerts(self, baseurl: str, page: int = 500) -> list[dict]:
        out, start = [], 0
        while True:
            batch = self._get("/JSON/core/view/alerts/", baseurl=baseurl, start=start, count=page)["alerts"]
            out += batch
            if len(batch) < page:
                return out
            start += page
