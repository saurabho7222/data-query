from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path

import pytest

from data_query.core import InputError, ReportFilters, connect_read_only, validate_schema, write_report
from conftest import create_database


def test_generates_expected_report(sales_db: Path, tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    report = write_report(sales_db, output)
    assert report["schema_version"] == 2
    assert report["filters"] == {"region": None, "start_date": None, "end_date": None, "top_limit": 5}
    assert report["summary"] == {
        "total_customers": 3,
        "total_orders": 5,
        "completed_orders": 3,
        "completed_revenue": 320.99,
    }
    assert json.loads(output.read_text()) == report


def test_region_filter_scopes_every_aggregate(sales_db: Path, tmp_path: Path) -> None:
    report = write_report(sales_db, tmp_path / "north.json", ReportFilters(region="north"))
    assert report["summary"] == {
        "total_customers": 2,
        "total_orders": 3,
        "completed_orders": 2,
        "completed_revenue": 200.0,
    }
    assert [row["name"] for row in report["top_customers"]] == ["Aster Labs"]


def test_date_range_filter_is_inclusive(sales_db: Path, tmp_path: Path) -> None:
    report = write_report(
        sales_db,
        tmp_path / "feb.json",
        ReportFilters(start_date=date(2026, 2, 1), end_date=date(2026, 2, 28)),
    )
    assert report["summary"] == {
        "total_customers": 2,
        "total_orders": 3,
        "completed_orders": 2,
        "completed_revenue": 240.99,
    }
    assert report["monthly_revenue"] == [{"month": "2026-02", "orders": 2, "revenue": 240.99}]


def test_top_limit_controls_customer_count(sales_db: Path, tmp_path: Path) -> None:
    report = write_report(sales_db, tmp_path / "top.json", ReportFilters(top_limit=1))
    assert len(report["top_customers"]) == 1
    assert report["top_customers"][0]["name"] == "Aster Labs"


def test_invalid_filter_range_is_rejected() -> None:
    with pytest.raises(InputError, match="start date"):
        ReportFilters(start_date=date(2026, 3, 1), end_date=date(2026, 2, 1))
    with pytest.raises(InputError, match="top limit"):
        ReportFilters(top_limit=0)


def test_empty_database_returns_zero_summary(tmp_path: Path) -> None:
    database = tmp_path / "empty.db"
    create_database(database, with_rows=False)
    report = write_report(database, tmp_path / "report.json")
    assert report["summary"]["completed_revenue"] == 0.0
    assert report["top_customers"] == []


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
