"""Run each scan profile once per validation target, one scan at a time, and save each run's files.

  python scripts/validation_matrix.py --target 5 --name webgoat --profiles quick standard deep

For every run: starts the scan through the API, samples CPU and memory while it runs (scripts/sample_usage.py),
aborts it after MAX_MINUTES (stopping ZAP's scans; the backend then records what was collected), and writes
results/validation/<name>/<profile>/{raw_alerts.json, settings.json, meta.json}.
"""
import argparse
import json
import pathlib
import subprocess
import sys
import time

import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
API = "http://127.0.0.1:8080"
MAX_MINUTES = 90


def env(key: str) -> str:
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith(key + "="):
            return line.split("=", 1)[1]
    return ""


def psql(sql: str) -> str:
    return subprocess.run(["docker", "compose", "exec", "-T", "postgres", "psql", "-U", "wasra", "-d", "wasra",
                           "-tAc", sql], capture_output=True, text=True, cwd=ROOT, timeout=120).stdout.strip()


def run_one(target_id: int, name: str, profile: str) -> dict:
    started = time.time()
    scan_id = requests.post(f"{API}/api/targets/{target_id}/scan", json={"profile": profile}, timeout=60).json()["scan_id"]
    sampler = subprocess.Popen([sys.executable, str(ROOT / "scripts" / "sample_usage.py"), str(scan_id)],
                               cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    aborted = False
    while True:
        status = psql(f"select status from scans where id={scan_id}")
        if status in ("done", "failed"):
            break
        if time.time() - started > MAX_MINUTES * 60:
            aborted = True
            subprocess.run(["curl", "-s", "-G", "http://127.0.0.1:8090/JSON/ascan/action/stopAllScans/",
                            "--data-urlencode", f"apikey={env('ZAP_API_KEY')}"], timeout=60)
            subprocess.run(["curl", "-s", "-G", "http://127.0.0.1:8090/JSON/spider/action/stopAllScans/",
                            "--data-urlencode", f"apikey={env('ZAP_API_KEY')}"], timeout=60)
            subprocess.run(["curl", "-s", "-G", "http://127.0.0.1:8090/JSON/ajaxSpider/action/stop/",
                            "--data-urlencode", f"apikey={env('ZAP_API_KEY')}"], timeout=60)
        time.sleep(20)
    sampler.wait(timeout=600)
    out = ROOT / "results" / "validation" / name / profile
    out.mkdir(parents=True, exist_ok=True)
    raw = psql(f"select coalesce(raw_alerts::text,'null') from scans where id={scan_id}")
    (out / "raw_alerts.json").write_text(json.dumps(json.loads(raw), indent=1, sort_keys=True))
    settings = psql(f"select coalesce(settings::text,'null') from scans where id={scan_id}")
    (out / "settings.json").write_text(json.dumps(json.loads(settings), indent=1, sort_keys=True))
    meta = json.loads(psql(
        f"select json_build_object('scan_id',id,'target',url,'profile',settings->>'profile','status',status,"
        f"'error',error,'zap_version',zap_version,'started_at',started_at,'finished_at',finished_at,"
        f"'wall_seconds',round(extract(epoch from finished_at-started_at)::numeric,1),'stage_seconds',stage_seconds,"
        f"'url_counts_after_spider',stage_urls,'usage',usage,'aborted_at_90_min',{str(aborted).lower()},"
        f"'zap_image','zaproxy/zap-stable:2.16.1@sha256:7840969c7c9fead565bf9734b12f49f6886db90b1d35b1f74d79710bbd081dab')"
        f" from scans s join targets t on t.id=s.target_id where s.id={scan_id}"))
    (out / "meta.json").write_text(json.dumps(meta, indent=1, sort_keys=True))
    return {"scan_id": scan_id, "profile": profile, "status": meta["status"], "aborted": aborted}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--profiles", nargs="+", default=["quick", "standard", "deep"])
    a = ap.parse_args()
    for p in a.profiles:
        print(json.dumps(run_one(a.target, a.name, p)), flush=True)


if __name__ == "__main__":
    main()
