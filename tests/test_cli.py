from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOLVER = REPO_ROOT / "task" / "solution" / "solve.py"


def run_cli(*args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SOLVER), *(str(value) for value in args)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


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
