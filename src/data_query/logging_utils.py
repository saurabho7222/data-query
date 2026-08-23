"""Logging helpers for human-readable and machine-readable CLI diagnostics."""

from __future__ import annotations

import json
import logging
from typing import Final

STRUCTURED_FIELDS: Final[tuple[str, ...]] = (
    "event",
    "error_type",
    "input_path",
    "output_path",
)


class JsonLogFormatter(logging.Formatter):
    """Render stable one-line JSON logs for automation and troubleshooting."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in STRUCTURED_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        return json.dumps(payload, sort_keys=True)


def configure_logger(logger: logging.Logger, *, level: str, log_format: str) -> None:
    """Configure a dedicated logger without mutating global logging state."""

    handler = logging.StreamHandler()
    if log_format == "json":
        handler.setFormatter(JsonLogFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))

    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper()))
    logger.propagate = False
