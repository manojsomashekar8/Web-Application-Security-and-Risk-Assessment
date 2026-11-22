"""Attach CVSS, EPSS and KEV to findings from the local feed snapshot. Never touches the network.

Every value carries provenance (feed name, file, snapshot date, status). A feed file that is missing or
unreadable is logged as a warning; its values become None ("n/a") and the scan continues.
"""
import csv
import json
import logging
import pathlib

log = logging.getLogger(__name__)
ROOT = pathlib.Path(__file__).resolve().parents[2]
FEEDS = ROOT / "data" / "feeds"
FEED_FILES = {  # field -> (feed name, file)
    "epss": ("EPSS", "epss.csv"),
    "kev": ("CISA KEV", "kev.json"),
    "cvss": ("NVD subset", "nvd_subset.json"),
}


def _snapshot_date(feeds: pathlib.Path) -> str | None:
    try:
        return json.loads((feeds / "manifest.json").read_text()).get("snapshot_date")
    except (OSError, ValueError) as exc:
        log.warning("feed manifest unreadable (%s): snapshot date unknown", exc)
        return None


def _read(name: str, path: pathlib.Path):
    """Parse one feed file. Returns (value, None) or (None, reason) and logs a warning on failure."""
    try:
        if name == "epss":
            with open(path) as fh:
                rows = csv.DictReader(r for r in fh if not r.startswith("#"))
                if not {"cve", "epss"} <= set(rows.fieldnames or []):  # wrong or corrupt header
                    raise ValueError("missing 'cve' or 'epss' column")
                return {r["cve"]: float(r["epss"]) for r in rows}, None
        if name == "kev":
            return {v["cveID"] for v in json.loads(path.read_text())["vulnerabilities"]}, None
        out = {}
        for item in json.loads(path.read_text()):
            c = item["cve"]
            for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
                if c.get("metrics", {}).get(key):
                    out[c["id"]] = c["metrics"][key][0]["cvssData"]["baseScore"]
                    break
        return out, None
    except (OSError, ValueError, KeyError, TypeError) as exc:
        reason = f"{type(exc).__name__}: {exc}"
        log.warning("feed %s unavailable (%s); those values will be n/a", path.name, reason)
        return None, reason


def load_feeds(feeds: pathlib.Path = FEEDS, cve_map_path: pathlib.Path = ROOT / "configs" / "cve_map.json") -> dict:
    date = _snapshot_date(feeds)
    data, unavailable, provenance = {}, {}, {}
    for field, (name, filename) in FEED_FILES.items():
        value, reason = _read(field, feeds / filename)
        data[field] = value if value is not None else {} if field != "kev" else set()
        if reason:
            unavailable[field] = reason
        provenance[field] = {"feed": name, "file": filename, "snapshot_date": date,
                             "status": "unavailable" if reason else "ok"}
    try:
        cve_map = {k: v for k, v in json.loads(cve_map_path.read_text()).items() if not k.startswith("_")}
    except (OSError, ValueError) as exc:
        log.warning("CVE mapping unavailable (%s): no CVE-based enrichment", exc)
        cve_map = {}
    return {"epss": data["epss"], "kev": data["kev"], "cvss": data["cvss"], "cve_map": cve_map,
            "unavailable": unavailable, "provenance": provenance}


def enrich(finding: dict, feeds: dict) -> dict:
    cves = feeds["cve_map"].get(finding["id"], [])
    cve = cves[0] if cves else None
    unavailable = feeds.get("unavailable", {})
    prov = feeds.get("provenance", {})

    def value(field, present):
        if not cve:
            status = "no_cve"
        elif field in unavailable:
            status = "unavailable"
        else:
            status = "ok" if present else "not_in_feed"
        out = {**prov.get(field, {"feed": None, "file": None, "snapshot_date": None}), "status": status}
        return out

    cvss = feeds["cvss"].get(cve) if cve and "cvss" not in unavailable else None
    epss = feeds["epss"].get(cve) if cve and "epss" not in unavailable else None
    kev = None if (not cve or "kev" in unavailable) else cve in feeds["kev"]  # no CVE means KEV does not apply: n/a, not "no"
    provenance = {"cvss": value("cvss", cvss is not None), "epss": value("epss", epss is not None),
                  "kev": value("kev", kev is not None)}
    return {**finding, "cve": cve, "cvss": cvss, "epss": epss, "kev": kev, "provenance": provenance,
            "enrichment_na": cvss is None}
