# Contributing

## Development setup

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m pip install -r requirements-dev.txt
```

## Required checks

Run all checks before opening a pull request:

```bash
python -m ruff check .
python -m mypy src/data_query examples
PYTHONPATH=src python -m pytest --cov=data_query --cov-fail-under=90
```

Each feature or bug fix should be a focused commit with the tests that prove the behavior. Avoid mixing unrelated formatting, refactors, and functional changes.

## Commit guidance

Use descriptive imperative commit messages, for example:

- `Add region filter with aggregate tests`
- `Reject orphan order items`
- `Export monthly revenue to CSV`

Do not rewrite authorship or timestamps to simulate project history. Maintenance history should reflect real development sessions and real contributors.
