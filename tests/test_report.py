from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from data_query.core import InputError, connect_read_only, validate_schema, write_report
from conftest import create_database


def test_generates_expected_report(sales_db: Path, tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    report = write_report(sales_db, output)
    assert report["schema_version"] == 1
    assert report["summary"] == {
        "total_customers": 3,
        "total_orders": 5,
        "completed_orders": 3,
        "completed_revenue": 320.99,
    }
    assert report["top_customers"][:2] == [
        {"customer_id": 1, "name": "Aster Labs", "region": "north", "orders": 2, "revenue": 200.0},
        {"customer_id": 2, "name": "Blue Harbor", "region": "west", "orders": 1, "revenue": 120.99},
    ]
    assert json.loads(output.read_text()) == report


def test_empty_database_returns_zero_summary(tmp_path: Path) -> None:
    database = tmp_path / "empty.db"
    create_database(database, with_rows=False)
    report = write_report(database, tmp_path / "report.json")
    assert report["summary"] == {
        "total_customers": 0,
        "total_orders": 0,
        "completed_orders": 0,
        "completed_revenue": 0.0,
    }
    assert report["top_customers"] == []
    assert report["monthly_revenue"] == []


def test_directory_input_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(InputError, match="not a file"):
        connect_read_only(tmp_path)


def test_missing_schema_is_rejected(tmp_path: Path) -> None:
    database = tmp_path / "bad-schema.db"
    connection = sqlite3.connect(database)
    try:
        connection.execute("CREATE TABLE customers(id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
        connection.commit()
    finally:
        connection.close()
    readonly = connect_read_only(database)
    try:
        with pytest.raises(InputError, match="invalid database schema"):
            validate_schema(readonly)
    finally:
        readonly.close()
