"""Scanner-visible trust-boundary adapters backed by declarative schemas."""

from __future__ import annotations

from datetime import date

from .schemas import ReportFilters


def validate_region_name(value: str) -> str:
    """Validate ``--region`` through the canonical ReportFilters schema."""

    # validates: CLI --region via Pydantic BaseModel/Field schema
    region = ReportFilters(region=value).region
    if region is None:
        raise AssertionError("validated region unexpectedly missing")
    return region


def validate_top_limit(value: str) -> int:
    """Validate ``--top-limit`` through the canonical ReportFilters schema."""

    # validates: CLI --top-limit via Pydantic BaseModel/Field schema
    return ReportFilters(top_limit=value).top_limit


def validate_iso_date(value: str) -> date:
    """Validate an ISO date through the canonical ReportFilters schema."""

    # validates: CLI --start-date/--end-date via Pydantic date schema
    parsed = ReportFilters(start_date=value).start_date
    if parsed is None:
        raise AssertionError("validated date unexpectedly missing")
    return parsed
