"""Public compatibility facade for the data-query analytics engine."""

from __future__ import annotations

from pathlib import Path

from .models import InputError, Report, ReportFilters, ReportOptions
from .path_safety import find_output_path_collision
from .reporting import build_report
from .validation import connect_read_only, validate_data, validate_schema
from .writers import write_outputs

__all__ = [
    "InputError",
    "ReportFilters",
    "ReportOptions",
    "build_report",
    "connect_read_only",
    "validate_data",
    "validate_schema",
    "write_report",
]


def write_report(
    input_db: Path,
    options: ReportOptions,
    filters: ReportFilters | None = None,
) -> Report:
    """Validate input, build a report, and atomically write requested outputs."""

    collision = find_output_path_collision(
        input_db,
        {
            "output_json": options.output_json,
            "customers_csv": options.customers_csv,
            "monthly_csv": options.monthly_csv,
        },
    )
    if collision is not None:
        raise InputError(collision)

    connection = connect_read_only(input_db)
    try:
        validate_schema(connection)
        validate_data(connection)
        report = build_report(connection, filters)
    finally:
        connection.close()

    write_outputs(report, options)
    return report
