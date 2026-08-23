from __future__ import annotations

import tomllib
from pathlib import Path

import data_query

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_package_version_matches_pyproject_metadata() -> None:
    config = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data_query.__version__ == config["project"]["version"]


def test_console_script_points_to_cli_main() -> None:
    config = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert config["project"]["scripts"]["data-query"] == "data_query.cli:main"
