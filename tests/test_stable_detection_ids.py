import pytest
from shapely.geometry import Polygon

from backend.app.main import generate_detection_id


@pytest.fixture
def sample_geometry():
    return Polygon([
        (78.4, 17.4),
        (78.5, 17.4),
        (78.5, 17.5),
        (78.4, 17.5),
        (78.4, 17.4)
    ])


def test_detection_id_is_deterministic(sample_geometry):
    first_id = generate_detection_id(sample_geometry)
    second_id = generate_detection_id(sample_geometry)

    assert first_id == second_id


def test_different_geometries_get_different_ids():
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

    assert (
        generate_detection_id(geometry_one)
        != generate_detection_id(geometry_two)
    )


def test_detection_id_format(sample_geometry):
    detection_id = generate_detection_id(sample_geometry)

    assert detection_id.startswith("FW-")
    assert len(detection_id) == 15


def test_empty_geometry_is_rejected():
    from shapely.geometry import Polygon

    with pytest.raises(ValueError):
        generate_detection_id(Polygon())


def test_id_does_not_depend_on_record_order():
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
        ])
    ]

    original_ids = {
        generate_detection_id(geometry)
        for geometry in geometries
    }

    reordered_ids = {
        generate_detection_id(geometry)
        for geometry in reversed(geometries)
    }

    assert original_ids == reordered_ids
