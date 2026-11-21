"""Refuse to start in AUTH_MODE=none unless every published port is bound to 127.0.0.1.

Reads `docker compose config --format json` on stdin and exits 1 with the offending ports.
  docker compose config --format json | python scripts/check_bindings.py none
"""
import json
import sys

LOCAL = "127.0.0.1"


def problems(config: dict, mode: str) -> list[str]:
    if mode != "none":  # basic auth protects the app itself, so any binding is allowed
        return []
    bad = []
    for name, svc in config.get("services", {}).items():
        for p in svc.get("ports", []):
            host_ip = p.get("host_ip") or "0.0.0.0"
            if host_ip != LOCAL:
                bad.append(f"{name}: {host_ip}:{p.get('published')} -> {p.get('target')}")
    return bad


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "none"
    found = problems(json.load(sys.stdin), mode)
    for line in found:
        print("NOT LOCAL:", line, file=sys.stderr)
    sys.exit(1 if found else 0)
