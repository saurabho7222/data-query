# Repository Classification

## Project Type

**Primary classification: application — Python data-processing application with a primary CLI and an optional HTTP API.**

The canonical machine-readable classification is stored in `pyproject.toml` under `[tool.data-query]` and mirrored in `project-metadata.json`:

```toml
project_type = "application"
category = "application"
domain = "data-processing"
primary_interface = "command-line"
interfaces = ["command-line", "http-api"]
infrastructure_as_code = false
service = true
self_contained = true
```

The CLI validates local SQLite databases and writes deterministic JSON/CSV analytics. Version 0.4.0 also exposes the same validated analytics engine through an optional FastAPI service with `/healthz`, `/metrics`, and `/v1/report`. The HTTP service is an application interface, not infrastructure provisioning.

## Why this is not infrastructure

Infrastructure-as-code is intentionally absent. The repository does not create cloud resources, clusters, networks, remote state, databases-as-a-service, or deployment infrastructure. SQLite remains embedded and the optional API reads databases from a caller-configured local data root.

Expected IaC indicators are deliberately zero/false:

- Terraform files: 0
- Kubernetes manifests: 0
- Helm charts: none
- Pulumi programs: none
- Ansible playbooks: none
- CloudFormation templates: none
- remote infrastructure state: none

The `Dockerfile`, `docker-compose.yml`, Dev Container, Makefile, and GitHub Actions workflows package and verify the application. Compose can start the optional API on `127.0.0.1:8000` for local verification, but it does not provision infrastructure or represent an IaC deployment model.

## Classifier disambiguation

Automated classifiers should prefer explicit application/runtime signals over generic repository-tooling signals:

- Python package metadata exposes two application entry points: `data-query` and `data-query-api`;
- `[tool.data-query]` declares `project_type = "application"` and `infrastructure_as_code = false`;
- `project-metadata.json` declares a primary command-line interface plus an optional HTTP API;
- the API exposes application health and metrics endpoints and serves analytics from embedded SQLite data;
- Compose binds the optional API to localhost for reproducible smoke testing;
- the repository contains no Terraform, Kubernetes, Helm, Pulumi, Ansible, CloudFormation, or remote-state artifacts.

An `infra` classification conflicts with the repository's runtime behavior and canonical metadata. The project may reasonably be classified as an application, data-processing service, backend utility, or CLI/API analytics application, but not as infrastructure-as-code.

Contributors should preserve this boundary unless the product itself changes. `tests/test_repository_contract.py` verifies the machine-readable application classification, API-service evidence, dependency manifests, and absence of IaC artifacts.
