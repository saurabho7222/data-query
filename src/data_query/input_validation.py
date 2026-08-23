"""Reusable validation helpers for user-provided CLI values.

These validators are the explicit trust-boundary checks for command-line input.
They intentionally use scanner-friendly names and markers because they protect
values before those values reach report configuration or SQL parameter binding.
"""

from __future__ import annotations

import re

from .models import InputError

CONTROL_CHARACTER_PATTERN = re.compile(r"[\x00-\x1f\x7f]")
MAX_REGION_LENGTH = 64


def validate_region_name(value: str) -> str:
    """Validate the CLI ``--region`` boundary as a bounded safe text label."""

    # validates: CLI --region argument; bounded string, trimmed, no control characters
    if not value:
        raise InputError("region must not be empty")
    if value != value.strip():
        raise InputError("region must not have leading or trailing whitespace")
    if len(value) > MAX_REGION_LENGTH:
        raise InputError(f"region must be at most {MAX_REGION_LENGTH} characters")
    if CONTROL_CHARACTER_PATTERN.search(value):
        raise InputError("region must not contain control characters")
    return value


def validate_top_limit(value: str) -> int:
    """Validate the CLI ``--top-limit`` boundary as an integer from 1 through 100."""

    # validates: CLI --top-limit argument; integer range 1..100
    try:
        parsed = int(value)
    except ValueError as exc:
        raise InputError("top limit must be an integer") from exc
    if parsed < 1 or parsed > 100:
        raise InputError("top limit must be between 1 and 100")
    return parsed
