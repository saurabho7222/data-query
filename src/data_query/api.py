"""Optional FastAPI service exposing the validated analytics engine over HTTP."""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Awaitable, Callable
from datetime import date
from pathlib import Path
from threading import Lock
from typing import Annotated, Final

import uvicorn
from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.responses import Response

from . import __version__
from .core import InputError, ReportFilters, build_report, connect_read_only, validate_data, validate_schema
from .models import Report

SERVICE_NAME: Final = "data-query"
DEFAULT_DATA_ROOT: Final = Path("/data")
DEFAULT_HOST: Final = "0.0.0.0"
DEFAULT_PORT: Final = 8000


class ServiceMetrics:
    """Small thread-safe in-process counters exposed in Prometheus text format."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._values: dict[str, int] = {
            "data_query_http_requests_total": 0,
            "data_query_report_requests_total": 0,
            "data_query_report_success_total": 0,
            "data_query_input_errors_total": 0,
            "data_query_sqlite_errors_total": 0,
        }

    def increment(self, name: str) -> None:
        with self._lock:
            self._values[name] += 1

    def render(self) -> str:
        with self._lock:
            snapshot = dict(self._values)
        lines: list[str] = []
        for name in sorted(snapshot):
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {snapshot[name]}")
        return "\n".join(lines) + "\n"


def _resolve_database(data_root: Path, database: str) -> Path:
    """Resolve a caller-selected database without allowing traversal outside ``data_root``."""

    root = data_root.resolve()
    candidate = (root / database).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise InputError(f"database path is outside configured data root: {database}") from exc
    return candidate


def create_app(*, data_root: Path) -> FastAPI:
    """Create an isolated application instance rooted at ``data_root``."""

    root = data_root.resolve()
    metrics = ServiceMetrics()
    app = FastAPI(
        title="Data Query API",
        summary="Validated SQLite analytics over HTTP",
        version=__version__,
    )

    @app.middleware("http")
    async def count_requests(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        metrics.increment("data_query_http_requests_total")
        return await call_next(request)

    @app.exception_handler(InputError)
    async def handle_input_error(request: Request, exc: InputError) -> JSONResponse:
        del request
        metrics.increment("data_query_input_errors_total")
        return JSONResponse(
            status_code=422,
            content={"error": "input_error", "message": str(exc)},
        )

    @app.exception_handler(sqlite3.Error)
    async def handle_sqlite_error(request: Request, exc: sqlite3.Error) -> JSONResponse:
        del request, exc
        metrics.increment("data_query_sqlite_errors_total")
        return JSONResponse(
            status_code=500,
            content={"error": "sqlite_error", "message": "database query failed"},
        )

    @app.get("/healthz")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": SERVICE_NAME, "version": __version__}

    @app.get("/metrics", response_class=PlainTextResponse)
    def prometheus_metrics() -> str:
        return metrics.render()

    @app.get("/v1/report")
    def report(
        database: Annotated[str, Query(min_length=1, max_length=255)],
        region: Annotated[str | None, Query(min_length=1, max_length=64)] = None,
        start_date: date | None = None,
        end_date: date | None = None,
        top_limit: Annotated[int, Query(ge=1, le=100)] = 5,
        cohort_periods: Annotated[int, Query(ge=1, le=24)] = 6,
        product_limit: Annotated[int, Query(ge=1, le=100)] = 10,
        compare_period: bool = False,
    ) -> Report:
        metrics.increment("data_query_report_requests_total")
        input_db = _resolve_database(root, database)
        filters = ReportFilters(
            region=region,
            start_date=start_date,
            end_date=end_date,
            top_limit=top_limit,
            cohort_periods=cohort_periods,
            product_limit=product_limit,
            compare_period=compare_period,
        )
        connection = connect_read_only(input_db)
        try:
            validate_schema(connection)
            validate_data(connection)
            payload = build_report(connection, filters)
        finally:
            connection.close()
        metrics.increment("data_query_report_success_total")
        return payload

    return app


app = create_app(data_root=Path(os.environ.get("DATA_QUERY_DATA_ROOT", DEFAULT_DATA_ROOT)))


def main() -> None:
    """Run the optional HTTP service using environment-configured bind settings."""

    host = os.environ.get("DATA_QUERY_HOST", DEFAULT_HOST)
    port_text = os.environ.get("DATA_QUERY_PORT", str(DEFAULT_PORT))
    try:
        port = int(port_text)
    except ValueError as exc:
        raise SystemExit("DATA_QUERY_PORT must be an integer") from exc
    if not 1 <= port <= 65535:
        raise SystemExit("DATA_QUERY_PORT must be between 1 and 65535")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
