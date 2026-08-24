from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path

import pytest

from conftest import create_database
from data_query.core import (
    InputError,
    ReportFilters,
    ReportOptions,
    connect_read_only,
    validate_data,
    validate_schema,
    write_report,
)


def test_generates_expected_report(sales_db: Path, tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    report = write_report(sales_db, ReportOptions(output))

    assert report["schema_version"] == 3
    assert report["filters"] == {
        "region": None,
        "start_date": None,
        "end_date": None,
        "top_limit": 5,
        "cohort_periods": 6,
    }
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


def test_region_filter_scopes_every_aggregate(sales_db: Path, tmp_path: Path) -> None:
    report = write_report(
        sales_db,
        ReportOptions(tmp_path / "north.json"),
        ReportFilters(region="north"),
    )
    assert report["summary"] == {
        "total_customers": 2,
        "total_orders": 3,
        "completed_orders": 2,
        "completed_revenue": 200.0,
    }
    assert [row["name"] for row in report["top_customers"]] == ["Aster Labs"]
    assert report["monthly_revenue"] == [
        {"month": "2026-01", "orders": 1, "revenue": 80.0},
        {"month": "2026-02", "orders": 1, "revenue": 120.0},
    ]


def test_date_range_filter_is_inclusive(sales_db: Path, tmp_path: Path) -> None:
    report = write_report(
        sales_db,
        ReportOptions(tmp_path / "feb.json"),
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
    report = write_report(sales_db, ReportOptions(tmp_path / "top.json"), ReportFilters(top_limit=1))
    assert len(report["top_customers"]) == 1
    assert report["top_customers"][0]["name"] == "Aster Labs"


def test_empty_database_returns_zero_summary(tmp_path: Path) -> None:
    database = tmp_path / "empty.db"
    create_database(database, with_rows=False)
    report = write_report(database, ReportOptions(tmp_path / "report.json"))
    assert report["summary"] == {
        "total_customers": 0,
        "total_orders": 0,
        "completed_orders": 0,
        "completed_revenue": 0.0,
    }
    assert report["top_customers"] == []
    assert report["monthly_revenue"] == []
    assert report["cohort_retention"] == []


def test_rejects_negative_money_inputs(sales_db: Path) -> None:
    connection = sqlite3.connect(sales_db)
    try:
        connection.execute("UPDATE order_items SET unit_price = -1 WHERE rowid = 1")
        connection.commit()
    finally:
        connection.close()

    readonly = connect_read_only(sales_db)
    try:
        validate_schema(readonly)
        with pytest.raises(InputError, match="non-negative"):
            validate_data(readonly)
    finally:
        readonly.close()


def test_rejects_orphan_relations(sales_db: Path, tmp_path: Path) -> None:
    connection = sqlite3.connect(sales_db)
    try:
        connection.execute("UPDATE orders SET customer_id = 999 WHERE id = 101")
        connection.commit()
    finally:
        connection.close()
    with pytest.raises(InputError, match="existing customer"):
        write_report(sales_db, ReportOptions(tmp_path / "report.json"))


def test_invalid_filter_range_is_rejected() -> None:
    with pytest.raises(InputError, match="start date"):
        ReportFilters(start_date=date(2026, 3, 1), end_date=date(2026, 2, 1))
    with pytest.raises(InputError, match="top limit"):
        ReportFilters(top_limit=0)


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


def test_invalid_order_date_is_rejected(sales_db: Path, tmp_path: Path) -> None:
    connection = sqlite3.connect(sales_db)
    try:
        connection.execute("UPDATE orders SET order_date = 'Feb 20' WHERE id = 104")
        connection.commit()
    finally:
        connection.close()
    with pytest.raises(InputError, match="YYYY-MM-DD"):
        write_report(sales_db, ReportOptions(tmp_path / "report.json"))


def test_orphan_order_item_is_rejected(sales_db: Path, tmp_path: Path) -> None:
    connection = sqlite3.connect(sales_db)
    try:
        connection.execute("UPDATE order_items SET order_id = 999 WHERE rowid = 1")
        connection.commit()
    finally:
        connection.close()
    with pytest.raises(InputError, match="existing order"):
        write_report(sales_db, ReportOptions(tmp_path / "report.json"))


def test_direct_csv_exports_are_written(sales_db: Path, tmp_path: Path) -> None:
    customers = tmp_path / "exports" / "customers.csv"
    monthly = tmp_path / "exports" / "monthly.csv"
    write_report(
        sales_db,
        ReportOptions(tmp_path / "report.json", customers_csv=customers, monthly_csv=monthly),
    )
    customer_text = customers.read_text(encoding="utf-8")
    monthly_text = monthly.read_text(encoding="utf-8")
    assert customer_text.startswith("customer_id,name,region,orders,revenue")
    assert "Aster Labs" in customer_text
    assert monthly_text.startswith("month,orders,revenue")
    assert "2026-02" in monthly_text
