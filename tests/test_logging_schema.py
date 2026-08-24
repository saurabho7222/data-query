from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from data_query import cli
from data_query.logging_utils import JSON_LOG_SCHEMA


def _json_lines(stderr: str) -> list[dict[str, object]]:
    return [json.loads(line) for line in stderr.splitlines() if line.strip()]


def _assert_schema(payload: dict[str, object]) -> None:
    common = JSON_LOG_SCHEMA["common_required"]
    events = JSON_LOG_SCHEMA["event_required"]
    assert isinstance(common, tuple)
    assert isinstance(events, dict)
    assert set(common).issubset(payload)
    assert payload["schema_version"] == JSON_LOG_SCHEMA["schema_version"]

    event = payload["event"]
    assert isinstance(event, str)
    required = events[event]
    assert isinstance(required, tuple)
    assert set(required).issubset(payload)


def test_validation_failure_json_log_matches_schema(tmp_path: Path, capsys: object) -> None:
    missing = tmp_path / "missing.db"
    code = cli.main(
        [
            "--input",
            str(missing),
            "--output",
            str(tmp_path / "report.json"),
            "--log-format",
            "json",
        ]
    )

    assert code == 2
    captured = capsys.readouterr()  # type: ignore[attr-defined]
    payloads = _json_lines(captured.err)
    assert len(payloads) == 1
    _assert_schema(payloads[0])
    assert payloads[0]["event"] == "validation_failed"
    assert payloads[0]["error_type"] == "input"
    assert payloads[0]["input_path"] == str(missing)


def test_report_success_json_log_matches_schema(sales_db: Path, tmp_path: Path, capsys: object) -> None:
    output = tmp_path / "report.json"
    code = cli.main(
        [
            "--input",
            str(sales_db),
            "--output",
            str(output),
            "--log-level",
            "INFO",
            "--log-format",
            "json",
        ]
    )

    assert code == 0
    captured = capsys.readouterr()  # type: ignore[attr-defined]
    payloads = _json_lines(captured.err)
    written = next(payload for payload in payloads if payload["event"] == "report_written")
    _assert_schema(written)
    assert written["output_path"] == str(output)


def test_validate_only_json_log_matches_schema(sales_db: Path, capsys: object) -> None:
    code = cli.main(
        [
            "--input",
            str(sales_db),
            "--validate-only",
            "--log-level",
            "INFO",
            "--log-format",
            "json",
        ]
    )

    assert code == 0
    captured = capsys.readouterr()  # type: ignore[attr-defined]
    payloads = _json_lines(captured.err)
    validated = next(payload for payload in payloads if payload["event"] == "database_valid")
    _assert_schema(validated)
    assert validated["input_path"] == str(sales_db)


def test_query_failure_json_log_matches_schema(tmp_path: Path, capsys: object, monkeypatch: object) -> None:
    def raise_sqlite_error(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise sqlite3.OperationalError("forced failure")

    monkeypatch.setattr(cli, "write_report", raise_sqlite_error)  # type: ignore[attr-defined]
    input_path = tmp_path / "input.db"
    code = cli.main(
        [
            "--input",
            str(input_path),
            "--output",
            str(tmp_path / "report.json"),
            "--log-format",
            "json",
        ]
    )

    assert code == 3
    captured = capsys.readouterr()  # type: ignore[attr-defined]
    payloads = _json_lines(captured.err)
    assert len(payloads) == 1
    _assert_schema(payloads[0])
    assert payloads[0]["event"] == "query_failed"
    assert payloads[0]["error_type"] == "sqlite"
    assert payloads[0]["input_path"] == str(input_path)
