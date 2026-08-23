"""Application exception hierarchy."""

from __future__ import annotations


class DataQueryError(Exception):
    """Base class for expected application failures."""


class InputError(DataQueryError, ValueError):
    """Raised when input data or user-provided configuration is invalid."""
