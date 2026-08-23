# Repository Classification

**Primary classification: CLI application / Python data-processing utility.**

The canonical machine-readable classification is stored in `pyproject.toml` under `[tool.data-query]`:

```toml
project_type = "cli-application"
category = "application"
domain = "data-processing"
infrastructure_as_code = false
service = false
self_contained = true
```

This repository implements a local SQLite analytics command-line application. It validates a database, executes read-only analytics queries, and writes deterministic JSON/CSV reports. Docker and GitHub Actions are application packaging and verification tools only.

## Why this is not infrastructure

Infrastructure-as-code is intentionally absent because the application has no infrastructure to provision. SQLite is embedded and there are no network services, cloud resources, clusters, or remote state.

Expected IaC indicators are therefore deliberately zero/false:

- Terraform files: 0
- Kubernetes manifests: 0
- Helm charts: none
- Pulumi programs: none
- Ansible playbooks: none
- CloudFormation templates: none
- remote infrastructure state: none

A `Dockerfile`, `compose.yaml`, `Makefile`, and GitHub Actions workflows do **not** make this repository an infrastructure project; they build, exercise, package, and verify the CLI application. Quality should be evaluated using application/data-processing criteria: correctness, test coverage, packaging, reproducibility, security checks, documentation, and maintainability.

If an automated classifier labels this repository as `infra` based only on Docker/CI artifacts, that classification conflicts with both the executable product and the explicit project metadata.
