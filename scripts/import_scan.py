"""Import a scan exported by another copy of this app.

  python scripts/import_scan.py path/to/wasra-scan-N.json

Uses the running API (http://127.0.0.1:8080). Importing never starts a scan; the file is checked on the server.
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
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    body = pathlib.Path(sys.argv[1]).read_bytes()
    user, pw = _env("WEB_USER"), _env("WEB_PASSWORD")
    auth = (user, pw) if _env("AUTH_MODE") == "basic" else None
    r = requests.post(f"{API}/api/import", data=body, headers={"Content-Type": "application/json"},
                      auth=auth, timeout=120)
    print(r.status_code, r.text)
    raise SystemExit(0 if r.status_code == 201 else 1)


if __name__ == "__main__":
    main()
