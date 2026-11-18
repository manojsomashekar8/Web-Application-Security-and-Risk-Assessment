SHELL := /bin/bash
.DEFAULT_GOAL := help
PY := .venv/bin/python
DBURL = postgresql://wasra:$$(grep ^POSTGRES_PASSWORD= .env | cut -d= -f2)@127.0.0.1:5432/wasra

help:  ## list targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/'

venv:  ## create .venv with the locked dependencies
	python3.12 -m venv .venv
	.venv/bin/pip install -q -r requirements.lock
	.venv/bin/python -m playwright install chromium

env:  ## create .env with random secrets (first setup)
	@scripts/gen_env.sh

up: env  ## start the stack (bound to 127.0.0.1) and wait until the endpoints answer
	docker compose up -d --build
	timeout 900 bash -c 'until curl -sf -o /dev/null http://127.0.0.1:8080/healthz; do sleep 5; done'
	timeout 900 bash -c 'until curl -sf -o /dev/null http://127.0.0.1:3001/api/health; do sleep 5; done'
	timeout 900 bash -c 'until curl -sf -o /dev/null http://127.0.0.1:3000/; do sleep 10; done'

down:  ## stop the stack
	docker compose down

test:  ## unit tests (offline); with the stack up, also integration and e2e
	$(PY) -m pytest -q tests --cov=src/normalize --cov=src/scoring --cov=src/enrich --cov-report=term-missing
	@if [ "$(WASRA_INTEGRATION)" = 1 ]; then WASRA_INTEGRATION=1 $(PY) -m pytest -q tests/integration; fi
	@if [ "$(WASRA_E2E)" = 1 ]; then WASRA_E2E=1 $(PY) -m pytest -q tests/e2e; fi

scan-juiceshop:  ## scan Juice Shop through the backend API
	$(PY) -m src.cli scan --url http://juice-shop:3000 --name "Juice Shop"

scan-validation:  ## raw ZAP scans of DVWA, WebGoat, bWAPP (inside the backend container, logged in)
	docker compose exec -T backend python -m src.collectors.run_scan --target http://dvwa:80 --name dvwa
	docker compose exec -T backend python -m src.collectors.run_scan --target http://webgoat:8080/WebGoat --name webgoat
	docker compose exec -T backend python -m src.collectors.run_scan --target http://bwapp:80 --name bwapp

experiments:  ## validation experiments 1-5 from saved raw alerts (offline)
	DATABASE_URL="$(DBURL)" $(PY) -m src.experiments.run --store

report:  ## write JSON and HTML reports for finished scans to results/reports/
	DATABASE_URL="$(DBURL)" $(PY) -m src.report.build

clean:  ## remove containers, volumes and generated reports (keeps data/feeds and results/raw)
	docker compose down -v
	rm -rf results/reports .pytest_cache htmlcov .coverage

reproduce:  ## full run from a clean state: env, stack, tests, scan, report, reproducibility doc
	$(MAKE) clean
	$(MAKE) up
	WASRA_INTEGRATION=1 WASRA_E2E=1 $(MAKE) test
	$(MAKE) scan-juiceshop
	$(MAKE) report
	$(PY) scripts/gen_reproducibility.py
	@echo "Outputs: results/reports/, results/, docs/RESULTS.md, docs/REPRODUCIBILITY.md"
	@echo "UI: http://127.0.0.1:8080   Grafana: http://127.0.0.1:3001"
