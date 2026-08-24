# Contributing

## Project scope

This repository is a Python data-processing application with a primary CLI and an optional HTTP API. It intentionally contains no Terraform, Kubernetes, Helm, Pulumi, Ansible, CloudFormation, or remote infrastructure state, and infrastructure provisioning is not planned for this project. Docker, Compose, the Dev Container, and GitHub Actions package, run, and verify the application; the localhost API service is application runtime, not IaC. See [CLASSIFICATION.md](CLASSIFICATION.md#why-this-is-not-infrastructure).

## Development setup

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m pip install -r requirements-dev.txt
uv lock --check
```

## Required checks

Run the relevant checks before opening a pull request:

```bash
ruff check .
mypy src/data_query examples scripts
pytest --cov=data_query --cov-fail-under=90
uv lock --check
uv sync --frozen
python scripts/check_dependency_freshness.py
make compose-api-smoke
```

Features and fixes should be focused and include the tests that demonstrate the behavior. Avoid mixing unrelated formatting, refactors, documentation, and functional changes in one commit.

## Interface changes

The CLI and HTTP API share the same analytics core. New API behavior should not duplicate SQL/report construction in `api.py`; route handlers should validate transport concerns and delegate to the existing validation/reporting layers. Database selections exposed over HTTP must remain inside the configured data-root sandbox.

Changes to public report fields, CLI options, HTTP query parameters, health/metrics contracts, or JSON log schema require behavioral tests and documentation updates.

## Dependency changes

Runtime dependencies belong in `pyproject.toml` with exact pins and must be mirrored in `requirements.txt` and `project-metadata.json`. After changing runtime dependencies, regenerate `uv.lock` with `uv lock` and verify it with `uv lock --check`. Development/security tools remain exactly pinned in `requirements-dev.txt`.

## Commit guidance

Use focused conventional-style messages where useful, for example:

- `test: define API sandbox contract`
- `feat: add healthchecked API service`
- `fix: preserve Python 3.11 response typing`
- `docs: document API security boundary`

Authorship and timestamps must reflect the people and sessions that actually produced the changes. Maintenance history should grow through normal development rather than history rewriting.
