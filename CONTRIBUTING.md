# Contributing

## Project scope

This repository is a Python CLI application for local SQLite analytics. It intentionally contains no Terraform, Kubernetes, Helm, Pulumi, Ansible, CloudFormation, or remote infrastructure state, and infrastructure provisioning is not planned for this project. Docker, Compose, the Dev Container, and GitHub Actions are development and verification tooling for the application. See [CLASSIFICATION.md](CLASSIFICATION.md#why-this-is-not-infrastructure) for the canonical classification rationale.

## Development setup

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m pip install -r requirements-dev.txt
uv lock --check
```

## Required checks

Run all checks before opening a pull request:

```bash
ruff check .
mypy src/data_query examples scripts
pytest --cov=data_query --cov-fail-under=90
uv lock --check
uv sync --frozen
python scripts/check_dependency_freshness.py
```

Each feature or bug fix should be a focused commit with the tests that prove the behavior. Avoid mixing unrelated formatting, refactors, and functional changes.

## Dependency changes

Runtime dependencies belong in `pyproject.toml` with exact pins. After changing runtime dependencies, regenerate `uv.lock` with `uv lock` and verify it with `uv lock --check`. Development and security tools remain exactly pinned in `requirements-dev.txt`.

## Commit guidance

Use descriptive imperative commit messages, for example:

- `Add region filter with aggregate tests`
- `Reject orphan order items`
- `Export monthly revenue to CSV`

Authorship and timestamps must reflect the people and sessions that actually produced the changes. Maintenance history should grow through normal development rather than history rewriting.
