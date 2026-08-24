"""Declarative validation schemas for user-controlled report configuration."""

from __future__ import annotations

from datetime import date
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from .errors import InputError

MAX_REGION_LENGTH = 64
REGION_PATTERN = r"^[^\x00-\x1f\x7f]+$"


def _validation_message(exc: ValidationError) -> str:
    """Translate schema failures into stable public error messages."""

    first = exc.errors(include_url=False)[0]
    location = first.get("loc", ())
    field = str(location[0]) if location else ""
    kind = str(first.get("type", ""))
    message = str(first.get("msg", "invalid input")).removeprefix("Value error, ")

    if field == "region":
        return {
            "string_too_short": "region must not be empty",
            "string_too_long": f"region must be at most {MAX_REGION_LENGTH} characters",
            "string_pattern_mismatch": "region must not contain control characters",
            "string_type": "region must be text",
        }.get(kind, message)
    if field == "top_limit":
        if kind in {"int_parsing", "int_type"}:
            return "top limit must be an integer"
        if kind in {"greater_than_equal", "less_than_equal"}:
            return "top limit must be between 1 and 100"
    if field == "cohort_periods":
        if kind in {"int_parsing", "int_type"}:
            return "cohort periods must be an integer"
        if kind in {"greater_than_equal", "less_than_equal"}:
            return "cohort periods must be between 1 and 24"
    if field in {"start_date", "end_date"}:
        return "expected YYYY-MM-DD"
    return message


class ReportFilters(BaseModel):
    """Validated report filters shared by CLI and library callers."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    region: str | None = Field(
        default=None,
        min_length=1,
        max_length=MAX_REGION_LENGTH,
        pattern=REGION_PATTERN,
    )
    start_date: date | None = None
    end_date: date | None = None
    top_limit: int = Field(default=5, ge=1, le=100)
    cohort_periods: int = Field(default=6, ge=1, le=24)

    @field_validator("region", mode="before")
    @classmethod
    def _region_must_be_trimmed(cls, value: object) -> object:
        if isinstance(value, str) and value != value.strip():
            raise ValueError("region must not have leading or trailing whitespace")
        return value

    @model_validator(mode="after")
    def _date_range_must_be_ordered(self) -> Self:
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start date must not be after end date")
        return self

    def __init__(self, **data: object) -> None:
        try:
            super().__init__(**data)
        except ValidationError as exc:
            raise InputError(_validation_message(exc)) from exc
