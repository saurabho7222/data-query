from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from data_query.api import create_app


def test_health_endpoint_reports_service_identity(tmp_path: Path) -> None:
    client = TestClient(create_app(data_root=tmp_path))

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "data-query",
        "version": "0.4.0",
    }


def test_report_endpoint_runs_existing_analytics_engine(sales_db: Path, tmp_path: Path) -> None:
    api_root = tmp_path / "api-data"
    api_root.mkdir()
    target = api_root / "sales.db"
    target.write_bytes(sales_db.read_bytes())
    client = TestClient(create_app(data_root=api_root))

    response = client.get(
        "/v1/report",
        params={
            "database": "sales.db",
            "region": "north",
            "cohort_periods": 12,
            "product_limit": 2,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == 4
    assert payload["filters"]["region"] == "north"
    assert payload["filters"]["cohort_periods"] == 12
    assert payload["filters"]["product_limit"] == 2
    assert payload["summary"]["completed_revenue"] == 200.0
    assert len(payload["product_concentration"]["products"]) == 2


def test_report_endpoint_maps_invalid_database_to_422(tmp_path: Path) -> None:
    client = TestClient(create_app(data_root=tmp_path))

    response = client.get("/v1/report", params={"database": "missing.db"})

    assert response.status_code == 422
    assert response.json() == {
        "error": "input_error",
        "message": f"input database does not exist: {tmp_path / 'missing.db'}",
    }


def test_report_endpoint_rejects_paths_outside_sandbox(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    data_root.mkdir()
    outside = tmp_path / "outside.db"
    outside.touch()
    client = TestClient(create_app(data_root=data_root))

    response = client.get("/v1/report", params={"database": "../outside.db"})

    assert response.status_code == 422
    assert response.json()["error"] == "input_error"
    assert "outside configured data root" in response.json()["message"]


def test_report_endpoint_validates_query_bounds(tmp_path: Path) -> None:
    client = TestClient(create_app(data_root=tmp_path))

    response = client.get(
        "/v1/report",
        params={"database": "missing.db", "product_limit": 101},
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail[0]["loc"][-1] == "product_limit"


def test_metrics_track_requests_and_failures(tmp_path: Path) -> None:
    client = TestClient(create_app(data_root=tmp_path))

    assert client.get("/healthz").status_code == 200
    assert client.get("/v1/report", params={"database": "missing.db"}).status_code == 422
    metrics = client.get("/metrics")

    assert metrics.status_code == 200
    assert "data_query_http_requests_total 3" in metrics.text
    assert "data_query_report_requests_total 1" in metrics.text
    assert "data_query_input_errors_total 1" in metrics.text
    assert "data_query_report_success_total 0" in metrics.text
