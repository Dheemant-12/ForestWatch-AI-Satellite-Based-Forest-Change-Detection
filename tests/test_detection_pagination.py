import geopandas as gpd
from shapely.geometry import Polygon

from backend.app import main as api


def sample_detections():
    geometries = [
        Polygon([
            (78.4, 17.4), (78.5, 17.4),
            (78.5, 17.5), (78.4, 17.5),
            (78.4, 17.4)
        ]),
        Polygon([
            (78.6, 17.4), (78.7, 17.4),
            (78.7, 17.5), (78.6, 17.5),
            (78.6, 17.4)
        ]),
        Polygon([
            (78.8, 17.4), (78.9, 17.4),
            (78.9, 17.5), (78.8, 17.5),
            (78.8, 17.4)
        ])
    ]

    return gpd.GeoDataFrame(
        {"area_ha": [2.0, 3.0, 4.0]},
        geometry=geometries,
        crs="EPSG:4326"
    )


def test_pagination_returns_requested_number(monkeypatch):
    monkeypatch.setattr(
        api, "load_detections", sample_detections
    )

    result = api.get_paginated_detections(limit=2, offset=0)

    assert result["total"] == 3
    assert result["records_returned"] == 2
    assert result["has_next"] is True
    assert len(result["data"]["features"]) == 2


def test_pagination_returns_second_page(monkeypatch):
    monkeypatch.setattr(
        api, "load_detections", sample_detections
    )

    result = api.get_paginated_detections(limit=2, offset=2)

    assert result["total"] == 3
    assert result["records_returned"] == 1
    assert result["has_next"] is False
    assert len(result["data"]["features"]) == 1


def test_pagination_handles_empty_page(monkeypatch):
    monkeypatch.setattr(
        api, "load_detections", sample_detections
    )

    result = api.get_paginated_detections(limit=2, offset=10)

    assert result["total"] == 3
    assert result["records_returned"] == 0
    assert result["has_next"] is False
    assert result["data"]["features"] == []


def test_pagination_preserves_geojson_format(monkeypatch):
    monkeypatch.setattr(
        api, "load_detections", sample_detections
    )

    result = api.get_paginated_detections(limit=1, offset=0)

    assert result["data"]["type"] == "FeatureCollection"
