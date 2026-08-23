from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from data_query import cli


def test_main_success_writes_report(sales_db: Path, tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    result = cli.main(["--input", str(sales_db), "--output", str(output), "--verbose"])
    assert result == 0
    assert output.exists()


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


def test_json_logging_reports_validation_failure(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    missing = tmp_path / "missing.db"
    result = cli.main(
        [
            "--input",
            str(missing),
            "--output",
            str(tmp_path / "out.json"),
            "--log-format",
            "json",
            "--log-level",
            "ERROR",
        ]
    )
    assert result == 2
    payload = json.loads(capsys.readouterr().err.strip())
    assert payload["level"] == "error"
    assert payload["event"] == "validation_failed"
    assert payload["error_type"] == "input"
    assert payload["input_path"] == str(missing)


def test_json_logging_reports_success(capsys: pytest.CaptureFixture[str], sales_db: Path, tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    result = cli.main(
        [
            "--input",
            str(sales_db),
            "--output",
            str(output),
            "--log-format",
            "json",
            "--log-level",
            "INFO",
        ]
    )
    assert result == 0
    payload = json.loads(capsys.readouterr().err.strip())
    assert payload["level"] == "info"
    assert payload["event"] == "report_written"
    assert payload["output_path"] == str(output)


def test_validate_only_checks_database_without_writing_report(
    capsys: pytest.CaptureFixture[str], sales_db: Path, tmp_path: Path
) -> None:
    output = tmp_path / "should-not-exist.json"
    result = cli.main(
        [
            "--input",
            str(sales_db),
            "--output",
            str(output),
            "--validate-only",
            "--log-format",
            "json",
            "--log-level",
            "INFO",
        ]
    )
    assert result == 0
    assert not output.exists()
    payload = json.loads(capsys.readouterr().err.strip())
    assert payload["event"] == "database_valid"
    assert payload["input_path"] == str(sales_db)


def test_validate_only_rejects_bad_rows(sales_db: Path, tmp_path: Path) -> None:
    connection = sqlite3.connect(sales_db)
    try:
        connection.execute("UPDATE order_items SET quantity = -1 WHERE rowid = 1")
        connection.commit()
    finally:
        connection.close()

    output = tmp_path / "should-not-exist.json"
    result = cli.main(["--input", str(sales_db), "--output", str(output), "--validate-only"])
    assert result == 2
    assert not output.exists()
