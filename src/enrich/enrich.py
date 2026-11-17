"""Attach CVSS, EPSS and KEV to findings from the local feed snapshot. Never touches the network."""
import csv
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
FEEDS = ROOT / "data" / "feeds"


def load_feeds(feeds: pathlib.Path = FEEDS, cve_map_path: pathlib.Path = ROOT / "configs" / "cve_map.json") -> dict:
    with open(feeds / "epss.csv") as fh:
        rows = (r for r in fh if not r.startswith("#"))
        epss = {r["cve"]: float(r["epss"]) for r in csv.DictReader(rows)}
    kev = {v["cveID"] for v in json.loads((feeds / "kev.json").read_text())["vulnerabilities"]}
    cvss = {}
    for item in json.loads((feeds / "nvd_subset.json").read_text()):
        c = item["cve"]
        for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
            if c.get("metrics", {}).get(key):
                cvss[c["id"]] = c["metrics"][key][0]["cvssData"]["baseScore"]
                break
    cve_map = {k: v for k, v in json.loads(cve_map_path.read_text()).items() if not k.startswith("_")}
    return {"epss": epss, "kev": kev, "cvss": cvss, "cve_map": cve_map}


def enrich(finding: dict, feeds: dict) -> dict:
    cves = feeds["cve_map"].get(finding["id"], [])
    cve = cves[0] if cves else None
    return {**finding, "cve": cve,
            "cvss": feeds["cvss"].get(cve) if cve else None,
            "epss": feeds["epss"].get(cve) if cve else None,
            "kev": bool(cve and cve in feeds["kev"])}
