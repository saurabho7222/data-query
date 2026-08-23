.PHONY: install test coverage lint typecheck quality security package-check docker-build docker-test compose-config compose-demo

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
