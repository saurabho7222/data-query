"""Reusable database validation entry point for CLI and automation."""

from __future__ import annotations

from pathlib import Path

from .core import connect_read_only, validate_data, validate_schema


def validate_database(path: Path) -> None:
    """Validate database readability, required schema, and row integrity."""

    connection = connect_read_only(path)
    try:
        validate_schema(connection)
        validate_data(connection)
    finally:
        connection.close()
