"""Sample CPU and memory of the ZAP and backend containers while a scan runs, then store the summary.

  python scripts/sample_usage.py SCAN_ID          (run it when the scan starts; it stops when the scan ends)

Samples `docker stats` every 5 seconds. Stores peak and average per container on the scan (scans.usage).
"""
import json
import pathlib
import subprocess
import sys
import time

import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
API = "http://127.0.0.1:8080"
CONTAINERS = ("zap", "backend")
INTERVAL = 5


def _env(key: str) -> str:
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith(key + "="):
            return line.split("=", 1)[1]
    return ""


def _mem_mib(text: str) -> float:  # "7.1GiB / 23.3GiB" -> 7270.4
    used = text.split("/")[0].strip()
    units = {"GiB": 1024, "MiB": 1, "KiB": 1 / 1024}
    for u, f in units.items():
        if used.endswith(u):
            return float(used[: -len(u)]) * f
    return 0.0


def sample() -> dict:
    out = subprocess.run(["docker", "stats", "--no-stream", "--format", "{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}"],
                         capture_output=True, text=True, cwd=ROOT, timeout=60).stdout
    result = {}
    for line in out.splitlines():
        name, cpu, mem = line.split("|")
        for c in CONTAINERS:
            if f"-{c}-" in name:
                result[c] = (float(cpu.rstrip("%")), _mem_mib(mem))
    return result


def summarise(samples: list[dict]) -> dict:
    usage = {}
    for c in CONTAINERS:
        cpu = [s[c][0] for s in samples if c in s]
        mem = [s[c][1] for s in samples if c in s]
        if cpu:
            usage[c] = {"cpu_peak_pct": round(max(cpu), 1), "cpu_avg_pct": round(sum(cpu) / len(cpu), 1),
                        "mem_peak_mib": round(max(mem)), "mem_avg_mib": round(sum(mem) / len(mem)),
                        "samples": len(cpu)}
    return usage


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    sid = int(sys.argv[1])
    auth = (_env("WEB_USER"), _env("WEB_PASSWORD")) if _env("AUTH_MODE") == "basic" else None
    samples = []
    while True:
        status = requests.get(f"{API}/api/scans/{sid}", auth=auth, timeout=30).json().get("status")
        if status != "running":
            break
        try:
            samples.append(sample())
        except Exception as exc:  # a missed sample must not stop the measurement
            print("sample skipped:", exc, file=sys.stderr)
        time.sleep(INTERVAL)
    usage = summarise(samples)
    requests.post(f"{API}/api/scans/{sid}/usage", data=json.dumps(usage),
                  headers={"Content-Type": "application/json"}, auth=auth, timeout=30).raise_for_status()
    print(json.dumps(usage, indent=1))


if __name__ == "__main__":
    main()
