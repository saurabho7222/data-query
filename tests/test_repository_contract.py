from __future__ import annotations

import json
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_declares_cli_application_contract() -> None:
    payload = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    metadata = payload["tool"]["data-query"]

    assert metadata["project_type"] == "cli-application"
    assert metadata["category"] == "application"
    assert metadata["domain"] == "data-processing"
    assert metadata["database"] == "embedded-sqlite"
    assert metadata["infrastructure_as_code"] is False
    assert metadata["service"] is False
    assert metadata["self_contained"] is True


def test_json_metadata_mirrors_project_type_contract() -> None:
    payload = json.loads((REPO_ROOT / "project-metadata.json").read_text(encoding="utf-8"))

    assert payload["project_type"] == "cli-application"
    assert payload["interface"] == "command-line"
    assert payload["infrastructure_as_code"] is False
    assert payload["self_contained"] is True


def test_repository_contains_no_infrastructure_as_code_artifacts() -> None:
    assert not list(REPO_ROOT.rglob("*.tf"))
    assert not list(REPO_ROOT.rglob("Chart.yaml"))
    assert not list(REPO_ROOT.rglob("Pulumi.yaml"))
    assert not list(REPO_ROOT.rglob("*.tfstate"))


def test_conventional_compose_contract_is_discoverable() -> None:
    compose = REPO_ROOT / "docker-compose.yml"
    assert compose.is_file()
    content = compose.read_text(encoding="utf-8")
    assert "sample-db:" in content
    assert "report:" in content
    assert "service_completed_successfully" in content
