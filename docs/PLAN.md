# Plan

Status key: [ ] todo, [x] done

## Phase 1: Environment
- [ ] docker-compose.yml: juice-shop, zap, postgres, backend, prometheus, grafana, dvwa, webgoat, bwapp
- [ ] All published ports bound to 127.0.0.1
- [ ] ZAP API reachable from backend
- [ ] Juice Shop scanned once, raw alerts saved to results/

## Phase 2: Normalization and feeds
- [ ] Finding schema, ZAP alert parser, CWE/OWASP mapping
- [ ] Feed snapshots (NVD subset, EPSS, KEV) with date + SHA-256
- [ ] Unit tests

## Phase 3: Scoring
- [ ] Framework score (SCORING.md formulas), baselines, explanation text
- [ ] configs/weights.yaml
- [ ] Unit + property tests

## Phase 4: API, storage, web UI, reports
- [ ] PostgreSQL schema + migrations (incl. read-only grafana user)
- [ ] FastAPI endpoints: targets, scans, findings, risk, comparison
- [ ] Web UI pages 1-4 + login
- [ ] HTML + JSON report (PDF deferred, see DECISIONS D6)

## Phase 5: Grafana and metrics
- [ ] Prometheus exporter
- [ ] Grafana provisioning: datasources, 3 dashboards, KEV alert rule
- [ ] Grafana health check in make test

## Phase 6: Validation
- [ ] DVWA and WebGoat/bWAPP scanned
- [ ] Experiments 1-5 saved to results/
- [ ] docs/RESULTS.md with screenshots from Playwright

## Phase 7 (stretch)
- [ ] Advisory watcher, Nuclei, local LLM explanations (only after 1-6)
