"""Export a finished scan to a versioned JSON file.

  python scripts/export_scan.py SCAN_ID [OUTPUT.json]

Writes results/exports/wasra-scan-SCAN_ID.json by default. Read-only.
"""
import pathlib
import sys

import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
API = "http://127.0.0.1:8080"


def _env(key: str) -> str:
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith(key + "="):
            return line.split("=", 1)[1]
    return ""


def main() -> None:
    if len(sys.argv) not in (2, 3):
        raise SystemExit(__doc__)
    sid = int(sys.argv[1])
    out = pathlib.Path(sys.argv[2]) if len(sys.argv) == 3 else ROOT / "results" / "exports" / f"wasra-scan-{sid}.json"
    auth = (_env("WEB_USER"), _env("WEB_PASSWORD")) if _env("AUTH_MODE") == "basic" else None
    r = requests.get(f"{API}/api/scans/{sid}/export.json", auth=auth, timeout=120)
    if r.status_code != 200:
        raise SystemExit(f"export failed: {r.status_code} {r.text}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(r.content)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
