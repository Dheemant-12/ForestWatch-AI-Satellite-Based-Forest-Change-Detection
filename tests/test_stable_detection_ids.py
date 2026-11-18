import geopandas as gpd
from shapely.geometry import Polygon

from backend.app.main import generate_detection_id


def test_detection_id_is_stable():
    geometry = Polygon([
        (78.4, 17.4),
        (78.5, 17.4),
        (78.5, 17.5),
        (78.4, 17.5),
        (78.4, 17.4)
    ])

    first = gpd.GeoSeries([geometry]).iloc[0]
    second = gpd.GeoSeries([geometry]).iloc[0]

    row_one = {
        "geometry": first,
        "area_ha": 2.5
    }

    row_two = {
        "geometry": second,
        "area_ha": 2.5
    }

    assert generate_detection_id(row_one) == generate_detection_id(row_two)


def test_different_detections_get_different_ids():
    geometry_one = Polygon([
        (78.4, 17.4),
        (78.5, 17.4),
        (78.5, 17.5),
        (78.4, 17.5),
        (78.4, 17.4)
    ])

    geometry_two = Polygon([
        (78.6, 17.4),
        (78.7, 17.4),
        (78.7, 17.5),
        (78.6, 17.5),
        (78.6, 17.4)
    ])

    row_one = {"geometry": geometry_one, "area_ha": 2.5}
    row_two = {"geometry": geometry_two, "area_ha": 2.5}

    assert generate_detection_id(row_one) != generate_detection_id(row_two)


def test_detection_id_has_expected_format():
    geometry = Polygon([
        (78.4, 17.4),
        (78.5, 17.4),
        (78.5, 17.5),
        (78.4, 17.5),
        (78.4, 17.4)
    ])

    detection_id = generate_detection_id({
        "geometry": geometry,
        "area_ha": 2.5
    })

    assert detection_id.startswith("FW-")
    assert len(detection_id) == 15
