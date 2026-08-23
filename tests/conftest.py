from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

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
                [
                    (101, 1, "2026-01-05", "completed"),
                    (102, 1, "2026-02-02", "completed"),
                    (103, 2, "2026-02-13", "cancelled"),
                    (104, 2, "2026-02-20", "completed"),
                    (105, 3, "2026-03-01", "pending"),
                ],
            )
            connection.executemany(
                "INSERT INTO order_items(order_id, product, quantity, unit_price) VALUES (?, ?, ?, ?)",
                [
                    (101, "adapter", 2, 25.00),
                    (101, "cable", 3, 10.00),
                    (102, "dock", 1, 120.00),
                    (103, "screen", 1, 300.00),
                    (104, "keyboard", 2, 45.50),
                    (104, "mouse", 1, 29.99),
                    (105, "stand", 1, 80.00),
                ],
            )
        connection.commit()
    finally:
        connection.close()


@pytest.fixture
def sales_db(tmp_path: Path) -> Path:
    path = tmp_path / "sales.db"
    create_database(path)
    return path
