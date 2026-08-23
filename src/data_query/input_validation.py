"""Reusable validation helpers for user-provided CLI values."""

from __future__ import annotations

import re

CONTROL_CHARACTER_PATTERN = re.compile(r"[\x00-\x1f\x7f]")
MAX_REGION_LENGTH = 64


def validate_region_name(value: str) -> str:
    """Validate a region label while preserving legitimate punctuation and case."""

    if not value:
        raise ValueError("region must not be empty")
    if value != value.strip():
        raise ValueError("region must not have leading or trailing whitespace")
    if len(value) > MAX_REGION_LENGTH:
        raise ValueError(f"region must be at most {MAX_REGION_LENGTH} characters")
    if CONTROL_CHARACTER_PATTERN.search(value):
        raise ValueError("region must not contain control characters")
    return value


def validate_top_limit(value: str) -> int:
    """Parse and bound the top-customer result limit."""

    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError("top limit must be an integer") from exc
    if parsed < 1 or parsed > 100:
        raise ValueError("top limit must be between 1 and 100")
    return parsed
