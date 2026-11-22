# ZAP notes: what we use, what the installed version does

Written from two sources, in this order of trust:
1. **The installed ZAP** (container `zaproxy/zap-stable:2.16.1`, API on 127.0.0.1:8090). Every value below marked *verified* was read or set through its REST API on 2026-11-22.
2. **The official documentation** at zaproxy.org (URLs in each section). Scraping the doc pages was unreliable (site navigation mixed into the text), so doc facts are summarised and should be re-checked against the page before citing.

## Version and sources read

- ZAP version: **2.16.1** (`/JSON/core/view/version/`, verified).
- Docs read: packaged scans (baseline, full, API), the scan policy page, the active scan options page, the spider and AJAX spider pages, the automation options page, and the Client Spider blog post of 2026-07-06 (https://www.zaproxy.org/blog/2026-07-06-client-spider-now-recommended/). The internet was reachable from the host.

## 1. Scan modes ZAP offers

| Mode | What it does | Sends attacks? | Source |
|---|---|---|---|
| Baseline scan (packaged) | Spider, then passive checks only; reports warnings. Optional `-j` adds the modern spider | No | https://www.zaproxy.org/docs/docker/baseline-scan/ |
| Full scan (packaged) | Spider, then full active scan | Yes | https://www.zaproxy.org/docs/docker/full-scan/ |
| API scan (packaged) | Imports an API definition, then active scan of its operations | Yes | https://www.zaproxy.org/docs/docker/api-scan/ |
| Quick Start / ZAPit | Spider and active scan of one URL from the desktop UI | Yes | https://www.zaproxy.org/docs/desktop/addons/quick-start |
| Automation Framework | A YAML plan of jobs (spider, spiderAjax, passiveScan-config, activeScan, activeScan-policy, delay, report) | Depends on jobs | https://www.zaproxy.org/docs/automate/automation-framework/ |
| Daemon REST API (what we use) | We call each job ourselves: spider, AJAX spider, passive wait, active scan, alerts | Yes, when we start the active scan | https://www.zaproxy.org/docs/api |

The baseline scan's own help says the spider has no time limit by default (`-m` sets minutes), and that the AJAX spider is the default extra spider unless `-j` asks for the modern one. Source: the baseline page above.

## 2. Settings that affect time or coverage, with installed defaults

| Setting | Where (API) | Installed default (verified) | Meaning and source |
|---|---|---|---|
| Max scan duration (minutes, 0 = unlimited) | `ascan/view/optionMaxScanDurationInMins` | **0** (unlimited) | Stops the whole active scan. Doc: active scan options page https://www.zaproxy.org/docs/desktop/ui/dialogs/options/ascan/ |
| Max rule duration (minutes, 0 = unlimited) | `ascan/view/optionMaxRuleDurationInMins` | **0** | Stops one rule. Same doc page |
| Threads per host | `ascan/view/optionThreadPerHost` | **24** | Parallel requests per host. Doc: "may put extra strain on the target". Same doc page |
| Hosts per scan | `ascan/view/optionHostPerScan` | **2** | Hosts scanned at once |
| Delay between requests (ms) | `ascan/view/optionDelayInMs` | **0** | Slows the scan. Set in the scan's options |
| Spider max depth | `spider/view/optionMaxDepth` | **5** | Link depth |
| Spider max children | `spider/view/optionMaxChildren` | **0** (no limit) | Children per node |
| Spider max duration (minutes) | `spider/view/optionMaxDuration` | **0** (no limit) | Time cap |
| Spider threads | `spider/view/optionThreadCount` | **24** | Parallel requests |
| AJAX spider max duration (minutes) | `ajaxSpider/view/optionMaxDuration` | **60** | Time cap. Our code overrides it per run |
| AJAX spider max crawl depth | `ajaxSpider/view/optionMaxCrawlDepth` | **10** | Our code overrides it per run |
| AJAX spider browser | `ajaxSpider/view/optionBrowserId` | **firefox-headless** | Our code passes `htmlunit` per run (see section 4) |
| AJAX spider event wait (ms) | `ajaxSpider/view/optionEventWait` | **1000** | Wait after each click |
| AJAX spider reload wait (ms) | `ajaxSpider/view/optionReloadWait` | **1000** | Wait after each reload |

Attack strength and alert threshold (per scanner, per policy) are covered in section 3.

## 3. Attack strength and alert threshold (verified)

Set through `ascan/action/setScannerAttackStrength` and `ascan/action/setScannerAlertThreshold`, on the scanner id and the policy name. Checked on scanner 10045 of "Default Policy", then restored to DEFAULT:

- Strength accepted: **LOW, MEDIUM, HIGH, DEFAULT**. A value that is not in the list is rejected with `does_not_exist`.
- Threshold accepted: **OFF, LOW, MEDIUM, HIGH, DEFAULT**.
- The default policy has **12 enabled scanners**, all at DEFAULT strength and threshold (`ascan/view/scanners/?policyId=0`).
- INSANE exists in ZAP's UI and API. **We do not offer it** (task rule).

Example responses:
```
GET /JSON/ascan/action/setScannerAttackStrength/?id=10045&attackStrength=LOW&scanPolicyName=Default%20Policy
{"Result":"OK"}
GET /JSON/ascan/action/setScannerAttackStrength/?id=10045&attackStrength=BOGUS&scanPolicyName=Default%20Policy
{"code":"does_not_exist","message":"Does Not Exist"}
```

## 4. How our scan maps onto ZAP

Our scan (`src/collectors/zap_client.py`, `run`):

| Step | Our call | Value we pass | Installed default we override |
|---|---|---|---|
| Fresh session | `core/action/newSession` | name `wasra`, overwrite | — |
| Traditional spider | `spider/action/scan` | `maxChildren=0`, `recurse=true` | depth stays 5, duration stays unlimited |
| AJAX spider | `ajaxSpider/action/scan` | `browserId=htmlunit`, `maxDuration=10`, `maxCrawlDepth=5` | browser firefox-headless, duration 60, depth 10 |
| Passive wait | `pscan/view/recordsToScan` | waits for 0 | — |
| Active scan | `ascan/action/scan` | `recurse=true`, `inScopeOnly=false` | all scanner settings stay at DEFAULT, no duration limit |

**What we currently leave at defaults:** the active scan's duration and rule-duration limits (both unlimited), thread count (24), delay (0), and every scanner's strength and threshold (DEFAULT). That is why the deep scan is slow and why its coverage is what it is.

**Client Spider.** The blog recommends it, but it is not usable here: the image ships `client-alpha` (the Client Side Integration add-on), yet `client/view/sites`, `client/view/clientMap` and `client/action/startSpider` all return `bad_view` / `bad_action` in this running instance (verified). The Client Spider also needs the ZAP browser extension in the browser it launches. **Decision D52:** keep the AJAX spider for the standard and deep profiles. Revisit when the Client Side Integration add-on is confirmed loaded.

**Browser for the AJAX spider.** We pass `htmlunit`. The installed default is `firefox-headless`. A scan with `htmlunit` completed on Juice Shop (scan 2), so it works here. Decision D53: keep `htmlunit` for the same results as before; record it in every scan's settings.

## 5. Reports

- The report add-on is installed (`reports-release-0.42.0`). The API lists templates including `traditional-html`, `traditional-json`, `traditional-md`, `traditional-xml`, `traditional-pdf`, `modern` and `sarif-json` (verified, `reports/view/templates/`).
- `reports/action/generate` exists and needs parameters (it returned `missing_parameter` without them). We will confirm the parameter names by calling it in Task 2.
- Our per-finding reports (Task 2) are written by our backend, not by ZAP. The whole-scan ZAP HTML report is offered as an extra download only if the API call works.

## 6. Values the frontend may expose, with bounds we enforce

| Field | Allowed values (server-side check) | Source of the list |
|---|---|---|
| Spider | `traditional`, `ajax`, `none` | Section 4 (Client Spider excluded, see above) |
| Spider time cap (minutes) | 1 to 60 | Spider options (0 = unlimited is not offered, to bound scan time) |
| Active scan | on / off | — |
| Attack strength | LOW, MEDIUM, HIGH | Section 3 (INSANE not offered) |
| Alert threshold | OFF, LOW, MEDIUM, HIGH | Section 3 |
| Max scan duration (minutes) | 1 to 240 | Section 2 (0 = unlimited is not offered) |
| Max rule duration (minutes) | 1 to 60 | Section 2 |
| Threads per host | 1 to 24 | Section 2 (installed default 24 is the upper bound) |
| Delay between requests (ms) | 0 to 2000 | Section 2 |
| Excluded URL patterns | up to 20 regular-expression strings, each up to 200 characters | ZAP's context exclusion, to be confirmed in Task 1 |
| Disabled rule ids | up to 100 numeric ids, each must exist in the default policy | Section 3 |

## 7. Where the documentation was unclear or disagreed with the installed ZAP

| Point | What we tested | Result |
|---|---|---|
| Spider and AJAX spider defaults are not all on the doc pages we could read | Read the values from the running API | Recorded in section 2 |
| Doc pages list Client Spider as recommended, but the add-on is not active in this image | Called the client API endpoints | `bad_view` / `bad_action` (section 4) |
| Our AJAX spider browser (`htmlunit`) differs from the installed default (`firefox-headless`) | Ran a full AJAX spider on Juice Shop with `htmlunit` (scan 2) | Works; kept (D53) |
| Scan policy edits are persistent in the container | Set LOW and MEDIUM on scanner 10045, then restored DEFAULT | Restored; the container's default policy is unchanged |
| Doc text on "thread per host" default is not on the page we read | Read the installed value | 24; the docs page does not state a number we could confirm |

## 8. Option setters and exclusions (verified on 2.16.1, 2026-11-22)

Each call below returned `{"Result":"OK"}` in the running container. Values were set to the defaults they already had, except where noted.

| Call | Parameter | Used for |
|---|---|---|
| `ascan/action/setOptionMaxScanDurationInMins` | `Integer` | Max active scan duration (0 = unlimited) |
| `ascan/action/setOptionMaxRuleDurationInMins` | `Integer` | Max duration per rule (0 = unlimited) |
| `ascan/action/setOptionThreadPerHost` | `Integer` | Threads per host |
| `ascan/action/setOptionDelayInMs` | `Integer` | Delay between requests |
| `spider/action/setOptionMaxDuration` | `Integer` | Traditional spider time cap (0 = unlimited) |
| `spider/action/setOptionThreadCount` | `Integer` | Traditional spider threads |
| `ajaxSpider/action/setOptionMaxDuration` | `Integer` | AJAX spider time cap, minutes |
| `ajaxSpider/action/setOptionBrowserId` | `String` | AJAX browser (we use `htmlunit`) |
| `spider/action/excludeFromScan` and `ascan/action/excludeFromScan` | `regex` | Exclude URLs from the spider or the active scan |
| `spider/view/excludedFromScan` and `ascan/view/excludedFromScan` | — | List the current exclusions |
| `spider/action/clearExcludedFromScan` and `ascan/action/clearExcludedFromScan` | — | Clear **all** exclusions (no per-item removal exists) |
| `ascan/action/disableScanners` and `ascan/action/enableScanners` | `ids` (comma list), `scanPolicyName` | Disable or enable scanners in a policy (verified; the singular `setScannerEnabled` does not exist) |

**Mistake found and fixed:** while testing, an exclusion for `http://dvwa:80/logout.*` was added to both lists during DVWA scan 6. It was cleared about a minute later with the clear calls above. Both lists were verified empty afterwards. The effect on scan 6 is not measured; see docs/OPEN_QUESTIONS.md.



## 9. AJAX spider failure: diagnosis (2026-11-22)

Found without scanning, from the running container, its log, and the stored scans.

**Proxy.** The AJAX spider's browser is not given an explicit proxy in our code. ZAP starts its own local servers for each browser: the container listens on several ephemeral ports besides the API port 8090 (read from `/proc/net/tcp`). No proxy variables are set in the container (`env | grep -i proxy` is empty).

**Reachability.** From inside the ZAP container, `dvwa` resolves to 172.19.0.3 (Docker DNS, `127.0.0.11`), and `http://dvwa:80/` returns HTTP 200. So the name and the port are not the problem.

**Browser.** The AJAX spider was set to `htmlunit` (our choice in D53). The container also has Firefox (`/usr/bin/firefox`) and the Selenium WebDriver add-ons. `firefox-headless` is ZAP's default.

**What fails.** HtmlUnit's request goes through ZAP's local server, and the message handlers run on each response. The log shows:
- `ERROR ... ExtensionSelenium - ClientProtocolException`, then `Caused by: ProtocolException: Invalid response: HTTP/1.0 0`. The browser got no valid HTTP response.
- The stack trace goes through `MainServerHandler.notifyMessageHandlers` into `DomXssScanRule` (ZAP's DOM XSS add-on), which calls `AbstractPlugin.sendAndReceive` and `ParosTableHistory.write`.
- The root exception is `org.parosproxy.paros.db.DatabaseException: java.sql.SQLNonTransientConnectionException: connection exception: closed` (HSQLDB). ZAP's history database is closed when the handler tries to write, so the handler throws and no response is sent.

**When it fails.** A stored scan's AJAX spider stage takes about 5 seconds when it fails, and about 135 to 145 seconds when it runs. Recent scans (9 deep scans from the reproduce runs, scan 13, and scan 14) all took about 5 seconds, so the AJAX spider failed in nearly every one of them. Scan 6 (135 s) and the Juice Shop timed run (145 s) show it worked earlier.

**What I have not confirmed.** The exact trigger that closes the database is not known. The per-scan call `core/action/newSession` (overwrite) runs just before each spider; the log shows "New session file created: wasra.session" near each scan start. That correlation is not proof, because scan 13 also called it and its AJAX spider ran, and this is not yet tested.

**Fix applied (D67).** The AJAX spider uses `firefox-headless` (`AJAX_BROWSER` in `src/collectors/zap_client.py`). Its result is checked by the URL count and the stage time of the next scan (scan 15). Client Spider: its API is not active in this container (see section 4), so it cannot be used here.
