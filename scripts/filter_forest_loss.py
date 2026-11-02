
import argparse
import json
from pathlib import Path

import numpy as np
import rasterio

from scipy import ndimage
from rasterio.features import shapes
from shapely.geometry import shape, mapping


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_MIN_AREA_HECTARES = 1.0

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

CONNECTIVITY = 8


# --------------------------------------------------
# LOAD DETECTION RASTER
# --------------------------------------------------

def load_detection_raster(path, band):

    with rasterio.open(path) as src:

        if band < 1 or band > src.count:
            raise ValueError(
                f"Band {band} does not exist. "
                f"Available bands: {src.count}"
            )

        if src.crs is None or not src.crs.is_projected:
            raise ValueError(
                "Raster must use a projected CRS. "
                "Reproject it to a suitable metric CRS first."
            )

        unit_factor = (
            src.crs.axis_info[0].unit_conversion_factor
        )

        if unit_factor is None:
            raise ValueError("Unknown CRS linear units.")

        pixel_area_m2 = (
            abs(
                src.transform.a * src.transform.e
                - src.transform.b * src.transform.d
            )
            * unit_factor ** 2
        )

        if pixel_area_m2 <= 0:
            raise ValueError("Invalid raster pixel area.")

        data = src.read(band, masked=True)

        valid = ~np.ma.getmaskarray(data)

        detection = (
            (np.asarray(data.filled(0)) > 0)
            & valid
        )

        metadata = src.profile.copy()
        transform = src.transform
        crs = src.crs

    return (
        detection,
        valid,
        metadata,
        transform,
        crs,
        pixel_area_m2
    )


# --------------------------------------------------
# CONNECTED COMPONENT ANALYSIS
# --------------------------------------------------

def identify_components(detection):

    if CONNECTIVITY == 8:
        structure = np.ones((3, 3), dtype=np.uint8)
    else:
        structure = ndimage.generate_binary_structure(
            2, 1
        )

    labels, component_count = ndimage.label(
        detection,
        structure=structure
    )

    print(f"Connected regions found: {component_count}")

    return labels, component_count


# --------------------------------------------------
# FILTER SMALL REGIONS
# --------------------------------------------------

def filter_components(
    labels,
    component_count,
    pixel_area_m2,
    minimum_area_hectares
):

    minimum_pixels = int(
        np.ceil(
            minimum_area_hectares
            * 10000
            / pixel_area_m2
        )
    )

    component_sizes = np.bincount(
        labels.ravel(),
        minlength=component_count + 1
    )

    keep = component_sizes >= minimum_pixels
    keep[0] = False

    filtered = keep[labels]

    retained_count = int(
        np.count_nonzero(keep)
    )

    removed_count = component_count - retained_count

    print(f"Minimum required pixels: {minimum_pixels}")
    print(f"Regions retained: {retained_count}")
    print(f"Regions removed: {removed_count}")

    return filtered, retained_count


# --------------------------------------------------
# SAVE FILTERED RASTER
# --------------------------------------------------

def save_filtered_raster(
    filtered,
    valid,
    metadata,
    output_path
):

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output = np.where(
        valid,
        filtered.astype(np.uint8),
        255
    )

    metadata.update({
        "count": 1,
        "dtype": "uint8",
        "nodata": 255,
        "compress": "deflate"
    })

    with rasterio.open(
        output_path,
        "w",
        **metadata
    ) as dst:

        dst.write(output, 1)

        dst.set_band_description(
            1,
            "FILTERED_POTENTIAL_FOREST_LOSS"
        )

    print(f"Filtered raster saved: {output_path}")


# --------------------------------------------------
# CONVERT RASTER TO GEOJSON
# --------------------------------------------------

def export_geojson(
    filtered,
    valid,
    transform,
    crs,
    output_path,
    pixel_area_m2
):

    features_list = []

    for geometry, value in shapes(
        filtered.astype(np.uint8),
        mask=filtered & valid,
        transform=transform,
        connectivity=CONNECTIVITY
    ):

        if value != 1:
            continue

        polygon = shape(geometry)

        area_hectares = (
            polygon.area
            * crs.axis_info[0].unit_conversion_factor ** 2
            / 10000
        )

        features_list.append({
            "type": "Feature",
            "geometry": mapping(polygon),
            "properties": {
                "area_hectares": round(
                    area_hectares, 4
                ),
                "detection_type": "potential_vegetation_loss"
            }
        })

    geojson = {
        "type": "FeatureCollection",
        "name": "ForestWatch_AI_Detections",
        "crs": {
            "type": "name",
            "properties": {
                "name": crs.to_string()
            }
        },
        "features": features_list
    }

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path.write_text(
        json.dumps(geojson, indent=4),
        encoding="utf-8"
    )

    print(f"GeoJSON saved: {output_path}")
    print(f"Polygon count: {len(features_list)}")

    total_area = sum(
        feature["properties"]["area_hectares"]
        for feature in features_list
    )

    print(f"Total candidate area: {total_area:.4f} hectares")

    return total_area


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    parser = argparse.ArgumentParser(
        description="ForestWatch AI Spatial Filtering"
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Input analytical forest-loss GeoTIFF"
    )

    parser.add_argument(
        "--band",
        type=int,
        default=4,
        help="Detection band number (Day 7 export: band 4)"
    )

    parser.add_argument(
        "--min-area",
        type=float,
        default=DEFAULT_MIN_AREA_HECTARES,
        help="Minimum component area in hectares"
    )

    args = parser.parse_args()

    if args.min_area <= 0:
        parser.error("--min-area must be positive")

    input_path = Path(args.input)

    if not input_path.exists():
        raise FileNotFoundError(input_path)

    print("=" * 60)
    print("FORESTWATCH AI - SPATIAL FILTERING")
    print("=" * 60)

    (
        detection,
        valid,
        metadata,
        transform,
        crs,
        pixel_area_m2
    ) = load_detection_raster(
        input_path,
        args.band
    )

    print(f"Input: {input_path}")
    print(f"CRS: {crs}")
    print(f"Pixel area: {pixel_area_m2:.2f} m2")

    print("\nIdentifying connected regions...")

    labels, component_count = identify_components(
        detection
    )

    print("\nRemoving small regions...")

    filtered, retained_count = filter_components(
        labels,
        component_count,
        pixel_area_m2,
        args.min_area
    )

    output_dir = OUTPUT_DIR / "forest_loss"

    raster_output = (
        output_dir / "filtered_forest_loss.tif"
    )

    geojson_output = (
        output_dir / "forest_loss_polygons.geojson"
    )

    print("\nSaving filtered raster...")

    save_filtered_raster(
        filtered,
        valid,
        metadata,
        raster_output
    )

    print("\nGenerating GeoJSON polygons...")

    total_area = export_geojson(
        filtered,
        valid,
        transform,
        crs,
        geojson_output,
        pixel_area_m2
    )

    print("\n" + "=" * 60)
    print("SPATIAL FILTERING COMPLETED")
    print("=" * 60)

    print(f"Original regions: {component_count}")
    print(f"Retained regions: {retained_count}")
    print(f"Candidate area: {total_area:.4f} hectares")


if __name__ == "__main__":
    main()
