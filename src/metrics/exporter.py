"""Prometheus collector: reads current state from PostgreSQL on every scrape (no in-memory state)."""
from prometheus_client.core import GaugeMetricFamily
from prometheus_client.registry import Collector

from src import db


class WasraCollector(Collector):
    def describe(self):
        # Empty on purpose: registering must not query the database (prometheus_client calls collect() otherwise).
        return []

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
            cls = GaugeMetricFamily("wasra_findings_by_class", "Unique findings by classification",
                                    labels=["classification"])
            for r in conn.execute("SELECT classification, count(*) AS n FROM findings GROUP BY classification"):
                cls.add_metric([r["classification"]], r["n"])
            yield cls
            raw = GaugeMetricFamily("wasra_alerts", "Raw alerts vs unique findings per target",
                                    labels=["target", "kind"])
            for r in conn.execute(
                "SELECT t.url, sum(f.occurrences) AS raw, count(*) AS uniq FROM findings f "
                "JOIN scans s ON s.id=f.scan_id JOIN targets t ON t.id=s.target_id GROUP BY t.url"
            ):
                raw.add_metric([r["url"], "raw"], r["raw"])
                raw.add_metric([r["url"], "unique"], r["uniq"])
            yield raw
            # Latest finished scan per target: used for the per-target panels below.
            latest = ("WITH latest AS (SELECT DISTINCT ON (s.target_id) s.id, s.target_id, s.stage_seconds, "
                      "s.top10_overlap FROM scans s WHERE s.status='done' ORDER BY s.target_id, s.id DESC) ")
            bands = GaugeMetricFamily("wasra_findings_by_band", "Findings per framework band (latest scan)",
                                      labels=["target", "band"])
            for r in conn.execute(latest + "SELECT t.url, CASE WHEN f.risk >= 60 THEN 'High' "
                                  "WHEN f.risk >= 30 THEN 'Medium' ELSE 'Low' END AS band, count(*) AS n "
                                  "FROM findings f JOIN latest l ON l.id = f.scan_id "
                                  "JOIN targets t ON t.id = l.target_id GROUP BY 1, 2"):
                bands.add_metric([r["url"], r["band"]], r["n"])
            yield bands
            stages = GaugeMetricFamily("wasra_scan_stage_seconds", "Duration of each scan stage (latest scan)",
                                       labels=["target", "stage"])
            overlap = GaugeMetricFamily("wasra_top10_overlap", "Top-10 overlap, framework vs CVSS-only (latest scan)",
                                        labels=["target"])
            na = GaugeMetricFamily("wasra_enrichment_na", "Findings with no CVSS (enrichment n/a), latest scan",
                                   labels=["target"])
            for r in conn.execute(latest + "SELECT t.url, l.stage_seconds, l.top10_overlap, "
                                  "(SELECT count(*) FROM findings f WHERE f.scan_id = l.id AND f.enrichment_na) AS na "
                                  "FROM latest l JOIN targets t ON t.id = l.target_id"):
                for stage, secs in (r["stage_seconds"] or {}).items():
                    stages.add_metric([r["url"], stage], secs)
                if r["top10_overlap"] is not None:
                    overlap.add_metric([r["url"]], r["top10_overlap"])
                na.add_metric([r["url"]], r["na"])
            yield stages
            yield overlap
            yield na
