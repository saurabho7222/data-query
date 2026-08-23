from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from data_query.core import InputError, ReportOptions, write_report
from data_query.path_safety import find_output_path_collision


def test_write_report_rejects_input_database_overwrite(sales_db: Path) -> None:
    original = sales_db.read_bytes()

    with pytest.raises(InputError, match="output_json must not overwrite input database"):
        write_report(sales_db, ReportOptions(output_json=sales_db))

    assert sales_db.read_bytes() == original
    connection = sqlite3.connect(sales_db)
    try:
        assert connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 5
    finally:
        connection.close()


def test_write_report_rejects_duplicate_output_destinations(sales_db: Path, tmp_path: Path) -> None:
    shared = tmp_path / "shared.out"

    with pytest.raises(InputError, match="output paths must be distinct: output_json and customers_csv"):
        write_report(
            sales_db,
            ReportOptions(output_json=shared, customers_csv=shared),
        )

    assert not shared.exists()


def test_collision_detection_normalizes_relative_aliases(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    input_path = tmp_path / "sales.db"
    input_path.touch()

    message = find_output_path_collision(
        input_path,
        {"output_json": Path("./sales.db"), "customers_csv": None},
    )

    assert message == "output_json must not overwrite input database"
