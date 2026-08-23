.PHONY: install test coverage lint typecheck quality security docker-build docker-test

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
	python3 -m mypy src/data_query task/solution task/examples

quality: lint typecheck coverage

security:
	python3 -m pip_audit -r requirements-dev.txt

docker-build:
	docker build -t data-query .

docker-test: docker-build
	docker run --rm data-query sh task/tests/test.sh
