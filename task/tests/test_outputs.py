"""Behavioral tests for the SQLite analytics report generator."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOLVER = REPO_ROOT / "task" / "solution" / "solve.py"

SCHEMA = """
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    region TEXT NOT NULL
);
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    status TEXT NOT NULL
);
CREATE TABLE order_items (
    order_id INTEGER NOT NULL,
    product TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL
);
"""


def create_database(path: Path, *, with_rows: bool = True) -> None:
    connection = sqlite3.connect(path)
    try:
        connection.executescript(SCHEMA)
        if with_rows:
            connection.executemany(
                "INSERT INTO customers(id, name, region) VALUES (?, ?, ?)",
                [(1, "Aster Labs", "north"), (2, "Blue Harbor", "west"), (3, "Cedar Works", "north")],
            )
            connection.executemany(
                "INSERT INTO orders(id, customer_id, order_date, status) VALUES (?, ?, ?, ?)",
                [(101, 1, "2026-01-05", "completed"), (102, 1, "2026-02-02", "completed"), (103, 2, "2026-02-13", "cancelled"), (104, 2, "2026-02-20", "completed"), (105, 3, "2026-03-01", "pending")],
            )
            connection.executemany(
                "INSERT INTO order_items(order_id, product, quantity, unit_price) VALUES (?, ?, ?, ?)",
                [(101, "adapter", 2, 25.00), (101, "cable", 3, 10.00), (102, "dock", 1, 120.00), (103, "screen", 1, 300.00), (104, "keyboard", 2, 45.50), (104, "mouse", 1, 29.99), (105, "stand", 1, 80.00)],
            )
        connection.commit()
    finally:
        connection.close()


def run_solver(input_db: Path, output_json: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SOLVER), "--input", str(input_db), "--output", str(output_json)], cwd=REPO_ROOT, capture_output=True, text=True, check=False)


def test_generates_expected_report(tmp_path: Path) -> None:
    """The report contains deterministic summary, customer, and monthly aggregates."""
    database = tmp_path / "sales.db"
    output = tmp_path / "report.json"
    create_database(database)
    result = run_solver(database, output)
    assert result.returncode == 0, result.stderr
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["schema_version"] == 1
    assert report["summary"] == {"total_customers": 3, "total_orders": 5, "completed_orders": 3, "completed_revenue": 320.99}
    assert report["top_customers"] == [
        {"customer_id": 1, "name": "Aster Labs", "region": "north", "orders": 2, "revenue": 200.0},
        {"customer_id": 2, "name": "Blue Harbor", "region": "west", "orders": 1, "revenue": 120.99},
    ]
    assert report["monthly_revenue"] == [
        {"month": "2026-01", "orders": 1, "revenue": 80.0},
        {"month": "2026-02", "orders": 2, "revenue": 240.99},
    ]


def test_empty_database_returns_zero_summary(tmp_path: Path) -> None:
    """A valid but empty schema is accepted and produces empty aggregate lists."""
    database = tmp_path / "empty.db"
    output = tmp_path / "report.json"
    create_database(database, with_rows=False)
    result = run_solver(database, output)
    assert result.returncode == 0, result.stderr
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["summary"] == {"total_customers": 0, "total_orders": 0, "completed_orders": 0, "completed_revenue": 0.0}
    assert report["top_customers"] == []
    assert report["monthly_revenue"] == []


def test_missing_input_fails_without_creating_output(tmp_path: Path) -> None:
    """A missing database fails fast with a clear message and no stale output."""
    database = tmp_path / "missing.db"
    output = tmp_path / "report.json"
    result = run_solver(database, output)
    assert result.returncode == 2
    assert "input database does not exist" in result.stderr
    assert not output.exists()


def test_malformed_schema_is_rejected(tmp_path: Path) -> None:
    """A SQLite file missing required tables/columns is rejected before querying."""
    database = tmp_path / "bad.db"
    output = tmp_path / "report.json"
    connection = sqlite3.connect(database)
    try:
        connection.execute("CREATE TABLE customers(id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
        connection.commit()
    finally:
        connection.close()
    result = run_solver(database, output)
    assert result.returncode == 2
    assert "invalid database schema" in result.stderr
    assert "orders" in result.stderr
    assert "order_items" in result.stderr
    assert not output.exists()


def test_non_sqlite_input_is_rejected(tmp_path: Path) -> None:
    """A malformed input file is rejected as non-SQLite data."""
    database = tmp_path / "not-a-db.txt"
    output = tmp_path / "report.json"
    database.write_text("not sqlite", encoding="utf-8")
    result = run_solver(database, output)
    assert result.returncode == 2
    assert "not a readable SQLite database" in result.stderr
    assert not output.exists()


def test_sample_database_script_is_runnable(tmp_path: Path) -> None:
    """The documented sample generator creates input that the solver can process."""
    database = tmp_path / "sample.db"
    output = tmp_path / "report.json"
    generator = REPO_ROOT / "task" / "examples" / "create_sample_db.py"
    created = subprocess.run([sys.executable, str(generator), str(database)], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    assert created.returncode == 0, created.stderr
    assert database.exists()
    result = run_solver(database, output)
    assert result.returncode == 0, result.stderr
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["summary"]["completed_revenue"] == 320.99
