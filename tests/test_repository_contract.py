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


def test_runtime_dependency_metadata_matches_pyproject_and_lock() -> None:
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    metadata = json.loads((REPO_ROOT / "project-metadata.json").read_text(encoding="utf-8"))
    runtime_dependencies = project["project"]["dependencies"]

    assert runtime_dependencies == metadata["runtime_dependencies"]
    assert metadata["runtime_dependency_count"] == len(runtime_dependencies) == 1
    assert metadata["lockfile"] == "uv.lock"

    lock_text = (REPO_ROOT / "uv.lock").read_text(encoding="utf-8")
    assert 'name = "pydantic"' in lock_text
    assert 'name = "pydantic-core"' in lock_text


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


def test_devcontainer_is_valid_and_runs_quality_setup() -> None:
    config_path = REPO_ROOT / ".devcontainer" / "devcontainer.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))

    assert payload["build"] == {"dockerfile": "../Dockerfile", "context": ".."}
    assert payload["workspaceFolder"] == "/workspaces/data-query"
    assert payload["overrideCommand"] is True
    assert "pip install -e ." in payload["postCreateCommand"]
    assert "pytest" in payload["postCreateCommand"]
    assert "--cov-fail-under=90" in payload["postCreateCommand"]


def test_release_workflow_verifies_and_tags_versioned_releases() -> None:
    release = (REPO_ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")

    assert "refs/heads/main" in release
    assert "git tag -a" in release
    assert "python -m pip install dist/*.whl" in release
    assert "gh release create" in release
    assert "--verify-tag" in release
