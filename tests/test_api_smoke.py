from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health_endpoint_responds():
    response = client.get("/health")

    assert response.status_code == 200
    assert isinstance(response.json(), dict)


def test_openapi_document_is_available():
    response = client.get("/openapi.json")

    assert response.status_code == 200

    document = response.json()
    assert "paths" in document


def test_detection_endpoints_are_registered():
    response = client.get("/openapi.json")
    paths = response.json()["paths"]

    expected_endpoints = [
        "/api/v1/detections",
        "/api/v1/detections/summary",
        "/api/v1/detections/page",
        "/api/v1/detections/quality",
        "/api/v1/analytics",
    ]

    for endpoint in expected_endpoints:
        assert endpoint in paths, f"Missing API endpoint: {endpoint}"


def test_detection_export_endpoints_are_registered():
    response = client.get("/openapi.json")
    paths = response.json()["paths"]

    expected_endpoints = [
        "/api/v1/detections/export/csv",
        "/api/v1/detections/export/geojson",
        "/api/v1/detections/timeline",
    ]

    for endpoint in expected_endpoints:
        assert endpoint in paths, f"Missing API endpoint: {endpoint}"
