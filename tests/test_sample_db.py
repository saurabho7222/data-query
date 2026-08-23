from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATOR = REPO_ROOT / "task" / "examples" / "create_sample_db.py"


def test_sample_generator_creates_expected_schema_and_rows(tmp_path: Path) -> None:
    database = tmp_path / "sample.db"
    result = subprocess.run([sys.executable, str(GENERATOR), str(database)], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr

    connection = sqlite3.connect(database)
    try:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {"customers", "orders", "order_items"} <= tables
        assert connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 3
        assert connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 5
        assert connection.execute("SELECT COUNT(*) FROM order_items").fetchone()[0] == 7
    finally:
        connection.close()


def test_sample_generator_replaces_existing_database(tmp_path: Path) -> None:
    database = tmp_path / "sample.db"
    database.write_text("stale", encoding="utf-8")
    result = subprocess.run([sys.executable, str(GENERATOR), str(database)], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    connection = sqlite3.connect(database)
    try:
        assert connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 3
    finally:
        connection.close()
