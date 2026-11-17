import json

import pytest
from fastapi import HTTPException

from backend.app import main as api


@pytest.fixture
def detection_file(tmp_path, monkeypatch):
    """Create a small sample GeoJSON detection dataset."""

    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "area_hectares": 2.5,
                    "observation_date": "2025-03-15"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [78.4, 17.4],
                        [78.5, 17.4],
                        [78.5, 17.5],
                        [78.4, 17.5],
                        [78.4, 17.4]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {
                    "area_hectares": 4.0,
                    "observation_date": "2025-03-20"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [78.6, 17.4],
                        [78.7, 17.4],
                        [78.7, 17.5],
                        [78.6, 17.5],
                        [78.6, 17.4]
                    ]]
                }
            }
        ]
    }

    file_path = tmp_path / "detections.geojson"
    file_path.write_text(json.dumps(geojson), encoding="utf-8")

    monkeypatch.setattr(api, "DETECTIONS_FILE", file_path)

    return file_path


def test_load_detections_normalizes_area(detection_file):
    gdf = api.load_detections()

    assert len(gdf) == 2
    assert "area_ha" in gdf.columns
    assert list(gdf["area_ha"]) == [2.5, 4.0]


def test_load_detections_generates_ids(detection_file):
    gdf = api.load_detections()

    assert list(gdf["detection_id"]) == ["FW-0001", "FW-0002"]


def test_load_detections_assigns_status(detection_file):
    gdf = api.load_detections()

    assert all(
        gdf["status"] == "Potential vegetation loss"
    )


def test_quality_endpoint_reports_valid_data(detection_file):
    result = api.get_detection_quality()

    assert result["total_source_records"] == 2
    assert result["valid_geometries"] == 2
    assert result["invalid_or_missing_geometries"] == 0
    assert result["area_field_found"] == "area_hectares"
    assert result["records_with_valid_area"] == 2
    assert result["area_coverage_percent"] == 100.0
    assert result["quality_status"] == "good"


def test_quality_endpoint_finds_date_fields(detection_file):
    result = api.get_detection_quality()

    assert "observation_date" in result["date_fields_found"]


def test_detection_summary_calculates_area(detection_file):
    result = api.get_detection_summary()

    assert result["total_detections"] == 2
    assert result["total_candidate_area_ha"] == 6.5
    assert result["coordinate_system"] == "EPSG:4326"


def test_missing_file_raises_http_404(tmp_path, monkeypatch):
    missing_file = tmp_path / "missing.geojson"
    monkeypatch.setattr(api, "DETECTIONS_FILE", missing_file)

    with pytest.raises(HTTPException) as error:
        api.load_detections()

    assert error.value.status_code == 404 or error.value.status_code == 500
