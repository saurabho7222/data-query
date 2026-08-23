from __future__ import annotations

import json
import logging

from data_query.logging_utils import JsonLogFormatter, configure_logger


def test_json_formatter_emits_stable_structured_fields() -> None:
    formatter = JsonLogFormatter()
    record = logging.LogRecord(
        name="data_query",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg="database rejected",
        args=(),
        exc_info=None,
    )
    record.event = "validation_failed"
    record.error_type = "input"
    payload = json.loads(formatter.format(record))
    assert payload == {
        "error_type": "input",
        "event": "validation_failed",
        "level": "error",
        "logger": "data_query",
        "message": "database rejected",
    }


def test_configure_logger_replaces_handlers_and_disables_propagation() -> None:
    logger = logging.getLogger("data_query.test")
    logger.handlers[:] = [logging.NullHandler(), logging.NullHandler()]
    logger.propagate = True

    configure_logger(logger, level="INFO", log_format="json")

    assert logger.level == logging.INFO
    assert logger.propagate is False
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0].formatter, JsonLogFormatter)
