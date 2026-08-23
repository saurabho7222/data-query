from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOLVER = REPO_ROOT / "task" / "solution" / "solve.py"


def run_cli(*args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SOLVER), *(str(value) for value in args)], cwd=REPO_ROOT, capture_output=True, text=True, check=False)


def test_missing_input_fails_without_output(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    result = run_cli("--input", tmp_path / "missing.db", "--output", output)
    assert result.returncode == 2
    assert "input database does not exist" in result.stderr
    assert not output.exists()


def test_non_sqlite_input_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "bad.db"
    source.write_text("not sqlite", encoding="utf-8")
    result = run_cli("--input", source, "--output", tmp_path / "report.json")
    assert result.returncode == 2
    assert "not a readable SQLite database" in result.stderr


def test_invalid_date_is_rejected_by_argument_parser(tmp_path: Path) -> None:
    result = run_cli("--input", tmp_path / "x.db", "--start-date", "02/01/2026")
    assert result.returncode == 2
    assert "expected YYYY-MM-DD" in result.stderr


def test_optional_csv_exports_match_json(sales_db: Path, tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    customers = tmp_path / "customers.csv"
    monthly = tmp_path / "monthly.csv"
    result = run_cli("--input", sales_db, "--output", output, "--customers-csv", customers, "--monthly-csv", monthly)
    assert result.returncode == 0, result.stderr
    report = json.loads(output.read_text(encoding="utf-8"))
    with customers.open(newline="", encoding="utf-8") as handle:
        customer_rows = list(csv.DictReader(handle))
    with monthly.open(newline="", encoding="utf-8") as handle:
        monthly_rows = list(csv.DictReader(handle))
    assert customer_rows[0]["name"] == report["top_customers"][0]["name"]
    assert float(customer_rows[0]["revenue"]) == report["top_customers"][0]["revenue"]
    assert [row["month"] for row in monthly_rows] == [row["month"] for row in report["monthly_revenue"]]
