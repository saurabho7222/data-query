from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from data_query import cli


def test_main_success_writes_report(sales_db: Path, tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    result = cli.main(["--input", str(sales_db), "--output", str(output), "--verbose"])
    assert result == 0
    assert output.exists()


def test_validate_only_checks_database_without_output(sales_db: Path, tmp_path: Path) -> None:
    output = tmp_path / "should-not-exist.json"
    result = cli.main(["--input", str(sales_db), "--output", str(output), "--validate-only", "--verbose"])
    assert result == 0
    assert not output.exists()


def test_main_returns_input_error_code(tmp_path: Path) -> None:
    result = cli.main(["--input", str(tmp_path / "missing.db"), "--output", str(tmp_path / "out.json")])
    assert result == 2


def test_main_returns_sqlite_error_code(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise sqlite3.OperationalError("query broke")

    monkeypatch.setattr(cli, "write_report", fail)
    result = cli.main(["--input", str(tmp_path / "ignored.db"), "--output", str(tmp_path / "out.json")])
    assert result == 3


def test_parser_rejects_bad_date() -> None:
    parser = cli.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--start-date", "02/01/2026"])
