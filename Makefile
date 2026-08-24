.PHONY: install test coverage lint typecheck quality security package-check docker-build docker-test compose-config compose-demo compose-api-smoke

install:
	python3 -m pip install -e .
	python3 -m pip install -r requirements-dev.txt

test:
	PYTHONPATH=src python3 -m pytest tests -v

coverage:
	PYTHONPATH=src python3 -m pytest --cov=data_query --cov-report=term-missing --cov-fail-under=90

lint:
	python3 -m ruff check .

typecheck:
	python3 -m mypy src/data_query examples

quality: lint typecheck coverage

security:
	python3 -m pip_audit -r requirements-dev.txt

package-check:
	rm -rf dist .package-check-venv
	python3 -m pip wheel . --no-deps --wheel-dir dist
	python3 -m venv .package-check-venv
	.package-check-venv/bin/python -m pip install --no-deps dist/*.whl
	.package-check-venv/bin/data-query --help
	.package-check-venv/bin/python -c "from data_query.api import create_app; assert callable(create_app)"
	rm -rf .package-check-venv

docker-build:
	docker build -t data-query .

docker-test: docker-build
	docker run --rm data-query python3 -m pytest tests -v

compose-config:
	docker compose config --quiet

compose-demo:
	mkdir -p .local
	rm -f .local/input.db .local/report.json .local/customers.csv .local/monthly.csv
	docker compose up --build --abort-on-container-exit --exit-code-from report report
	test -s .local/report.json
	test -s .local/customers.csv
	test -s .local/monthly.csv

compose-api-smoke:
	@set -eu; \
		mkdir -p .local; \
		rm -f .local/input.db; \
		trap 'docker compose down --remove-orphans >/dev/null 2>&1 || true' EXIT; \
		docker compose up --build -d api; \
		for i in $$(seq 1 30); do \
			if python3 -c 'import json, urllib.request; payload=json.load(urllib.request.urlopen("http://127.0.0.1:8000/healthz", timeout=2)); assert payload["status"] == "ok"' >/dev/null 2>&1; then break; fi; \
			if [ "$$i" -eq 30 ]; then docker compose logs api; exit 1; fi; \
			sleep 1; \
		done; \
		python3 -c 'import json, urllib.request; base="http://127.0.0.1:8000"; report=json.load(urllib.request.urlopen(base+"/v1/report?database=input.db&region=north&product_limit=2", timeout=10)); assert report["summary"]["completed_revenue"] == 200.0; metrics=urllib.request.urlopen(base+"/metrics", timeout=5).read().decode(); assert "data_query_http_requests_total" in metrics; assert "data_query_report_success_total 1" in metrics'
