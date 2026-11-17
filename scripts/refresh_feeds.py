"""Download EPSS, KEV and an NVD CVE subset into data/feeds/ with a manifest (date + SHA-256).

Run only when refreshing. The pipeline reads data/feeds/ only and never needs the network.
"""
import datetime as dt
import gzip
import hashlib
import json
import pathlib
import time

import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
FEEDS = ROOT / "data" / "feeds"
CVE_LIST = ROOT / "configs" / "cve_list.txt"
SOURCES = {
    "epss.csv": "https://epss.cyentia.com/epss_scores-current.csv.gz",
    "kev.json": "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
}
NVD = "https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={}"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    FEEDS.mkdir(parents=True, exist_ok=True)
    for name, url in SOURCES.items():
        r = requests.get(url, timeout=120, allow_redirects=True)
        r.raise_for_status()
        body = gzip.decompress(r.content) if url.endswith(".gz") else r.content
        (FEEDS / name).write_bytes(body)
    cves = [c.strip() for c in CVE_LIST.read_text().splitlines() if c.strip() and not c.startswith("#")]
    nvd = []
    for cve in cves:  # NVD public rate limit without a key: 5 requests / 30 s
        r = requests.get(NVD.format(cve), timeout=60)
        r.raise_for_status()
        nvd += r.json().get("vulnerabilities", [])
        time.sleep(6)
    (FEEDS / "nvd_subset.json").write_text(json.dumps(nvd, indent=2, sort_keys=True))
    manifest = {
        "snapshot_date": dt.date.today().isoformat(),
        "files": {p.name: sha256(p) for p in sorted(FEEDS.iterdir()) if p.name != "manifest.json"},
        "cve_count": len(cves),
    }
    (FEEDS / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
    print(f"snapshot written: {FEEDS}")


if __name__ == "__main__":
    main()
