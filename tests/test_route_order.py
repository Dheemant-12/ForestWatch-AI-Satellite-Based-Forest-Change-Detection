from backend.app.main import app


def test_static_detection_routes_are_before_dynamic_route():
    paths = [
        route.path
        for route in app.routes
        if hasattr(route, "path")
    ]

    dynamic_path = "/api/v1/detections/{detection_id}"

    static_paths = [
        "/api/v1/detections/filter",
        "/api/v1/detections/quality",
        "/api/v1/detections/timeline",
        "/api/v1/detections/summary",
        "/api/v1/detections/export/csv",
        "/api/v1/detections/export/geojson",
    ]

    assert dynamic_path in paths

    dynamic_index = paths.index(dynamic_path)

    for static_path in static_paths:
        assert static_path in paths
        assert paths.index(static_path) < dynamic_index, (
            f"{static_path} must be registered before {dynamic_path}"
        )
