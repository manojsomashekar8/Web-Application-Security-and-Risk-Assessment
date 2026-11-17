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

    def run(self, target: str) -> None:
        self._get("/JSON/core/action/newSession/", name="wasra", overwrite="true")  # clean state per run
        sid = self._get("/JSON/spider/action/scan/", url=target, maxChildren=0, recurse=True)["scan"]
        self._wait("/JSON/spider/view/status/", sid)
        # AJAX spider renders client-side routes (SPA API endpoints the traditional spider misses).
        self._get("/JSON/ajaxSpider/action/scan/", url=target, browserId="htmlunit",
                  maxDuration=10, maxCrawlDepth=5)
        while self._get("/JSON/ajaxSpider/view/status/")["status"] != "stopped":
            time.sleep(POLL_SECONDS)
        while int(self._get("/JSON/pscan/view/recordsToScan/")["recordsToScan"]) > 0:
            time.sleep(POLL_SECONDS)
        aid = self._get("/JSON/ascan/action/scan/", url=target, recurse=True, inScopeOnly=False)["scan"]
        self._wait("/JSON/ascan/view/status/", aid)

    def alerts(self, baseurl: str, page: int = 500) -> list[dict]:
        out, start = [], 0
        while True:
            batch = self._get("/JSON/core/view/alerts/", baseurl=baseurl, start=start, count=page)["alerts"]
            out += batch
            if len(batch) < page:
                return out
            start += page
