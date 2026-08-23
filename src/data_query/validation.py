"""SQLite connection, schema validation, and data-integrity checks."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import InputError

REQUIRED_SCHEMA: dict[str, set[str]] = {
    "customers": {"id", "name", "region"},
    "orders": {"id", "customer_id", "order_date", "status"},
    "order_items": {"order_id", "product", "quantity", "unit_price"},
}
BUSY_TIMEOUT_MS = 5000


def connect_read_only(path: Path) -> sqlite3.Connection:
    """Open and integrity-check a SQLite database in hardened read-only mode."""

    if not path.exists():
        raise InputError(f"input database does not exist: {path}")
    if not path.is_file():
        raise InputError(f"input path is not a file: {path}")

    connection: sqlite3.Connection | None = None
    try:
        uri = path.resolve().as_uri() + "?mode=ro"
        connection = sqlite3.connect(uri, uri=True)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        connection.execute("PRAGMA trusted_schema = OFF")
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        quick_check = connection.execute("PRAGMA quick_check").fetchone()
        if quick_check is None or str(quick_check[0]).lower() != "ok":
            raise InputError("input SQLite database failed integrity check")
        return connection
    except InputError:
        if connection is not None:
            connection.close()
        raise
    except sqlite3.Error as exc:
        if connection is not None:
            connection.close()
        raise InputError(f"input is not a readable SQLite database: {path}") from exc


def validate_schema(connection: sqlite3.Connection) -> None:
    """Verify that all tables and columns required by the report are present."""

    missing: list[str] = []
    for table, required_columns in REQUIRED_SCHEMA.items():
        rows = connection.execute("SELECT name FROM pragma_table_info(?)", (table,)).fetchall()
        if not rows:
            missing.append(f"table {table}")
            continue
        actual_columns = {str(row["name"]) for row in rows}
        absent_columns = sorted(required_columns - actual_columns)
        if absent_columns:
            missing.append(f"{table} columns: {', '.join(absent_columns)}")

    if missing:
        raise InputError("invalid database schema; missing " + "; ".join(missing))


def validate_data(connection: sqlite3.Connection) -> None:
    """Reject malformed rows that would make monetary/date aggregates unreliable."""

    invalid_item = connection.execute(
        """
        SELECT rowid, quantity, unit_price
        FROM order_items
        WHERE typeof(quantity) NOT IN ('integer', 'real')
           OR typeof(unit_price) NOT IN ('integer', 'real')
           OR quantity < 0
           OR unit_price < 0
        LIMIT 1
        """
    ).fetchone()
    if invalid_item is not None:
        raise InputError("invalid order_items data; quantity and unit_price must be non-negative numbers")

    invalid_date = connection.execute(
        """
        SELECT id, order_date
        FROM orders
        WHERE order_date IS NULL
           OR length(order_date) != 10
           OR date(order_date) IS NULL
           OR strftime('%Y-%m-%d', order_date) != order_date
        LIMIT 1
        """
    ).fetchone()
    if invalid_date is not None:
        raise InputError("invalid orders data; order_date must use YYYY-MM-DD")

    orphan_order = connection.execute(
        """
        SELECT o.id
        FROM orders o
        LEFT JOIN customers c ON c.id = o.customer_id
        WHERE c.id IS NULL
        LIMIT 1
        """
    ).fetchone()
    if orphan_order is not None:
        raise InputError("invalid relational data; every order must reference an existing customer")

    orphan_item = connection.execute(
        """
        SELECT oi.rowid
        FROM order_items oi
        LEFT JOIN orders o ON o.id = oi.order_id
        WHERE o.id IS NULL
        LIMIT 1
        """
    ).fetchone()
    if orphan_item is not None:
        raise InputError("invalid relational data; every order item must reference an existing order")
