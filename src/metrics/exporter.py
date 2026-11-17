"""Prometheus collector: reads current state from PostgreSQL on every scrape (no in-memory state)."""
from prometheus_client.core import GaugeMetricFamily
from prometheus_client.registry import Collector

from src import db


class WasraCollector(Collector):
    def collect(self):
        with db.connect() as conn:
            scans = GaugeMetricFamily("wasra_scans", "Scans by status", labels=["status"])
            for r in conn.execute("SELECT status, count(*) AS n FROM scans GROUP BY status"):
                scans.add_metric([r["status"]], r["n"])
            yield scans
            sev = GaugeMetricFamily("wasra_findings", "Findings by ZAP risk", labels=["zap_risk"])
            for r in conn.execute("SELECT zap_risk, count(*) AS n FROM findings GROUP BY zap_risk"):
                sev.add_metric([r["zap_risk"]], r["n"])
            yield sev
            avg = GaugeMetricFamily("wasra_avg_risk", "Mean framework risk per target", labels=["target"])
            for r in conn.execute(
                "SELECT t.url, avg(f.risk) AS a FROM findings f JOIN scans s ON s.id=f.scan_id "
                "JOIN targets t ON t.id=s.target_id GROUP BY t.url"
            ):
                avg.add_metric([r["url"]], r["a"])
            yield avg
            kev = GaugeMetricFamily("wasra_kev_findings", "Findings flagged KEV", labels=["target"])
            for r in conn.execute(
                "SELECT t.url, count(*) AS n FROM findings f JOIN scans s ON s.id=f.scan_id "
                "JOIN targets t ON t.id=s.target_id WHERE f.kev GROUP BY t.url"
            ):
                kev.add_metric([r["url"]], r["n"])
            yield kev
