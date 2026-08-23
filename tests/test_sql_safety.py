from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from conftest import create_database
from data_query.core import ReportFilters, ReportOptions, connect_read_only, validate_schema, write_report


def test_read_only_connection_enforces_hardened_pragmas(sales_db: Path) -> None:
    connection = connect_read_only(sales_db)
    try:
        assert connection.execute("PRAGMA query_only").fetchone()[0] == 1
        assert connection.execute("PRAGMA trusted_schema").fetchone()[0] == 0
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA busy_timeout").fetchone()[0] == 5000
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            connection.execute("CREATE TABLE should_fail(id INTEGER)")
    finally:
        connection.close()


def test_read_only_connection_handles_uri_reserved_filename_characters(tmp_path: Path) -> None:
    database = tmp_path / "sales?archive#1.db"
    create_database(database)

    connection = connect_read_only(database)
    try:
        validate_schema(connection)
    finally:
        connection.close()


def test_region_filter_sql_metacharacters_are_treated_as_literal_data(sales_db: Path, tmp_path: Path) -> None:
    report = write_report(
        sales_db,
        ReportOptions(tmp_path / "literal-region.json"),
        ReportFilters(region="north' OR 1=1 --"),
    )

    assert report["summary"] == {
        "total_customers": 0,
        "total_orders": 0,
        "completed_orders": 0,
        "completed_revenue": 0.0,
    }
    assert report["top_customers"] == []
    assert report["monthly_revenue"] == []
