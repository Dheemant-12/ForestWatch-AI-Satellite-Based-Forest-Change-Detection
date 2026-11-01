
import os
from pathlib import Path

import ee
from dotenv import load_dotenv


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env")

ROI_BOUNDS = [80.0, 17.8, 80.6, 18.4]

COLLECTION_ID = "COPERNICUS/S2_SR_HARMONIZED"

MAX_CLOUD_PERCENT = 30

BEFORE_START = "2024-01-01"
BEFORE_END = "2024-04-01"

AFTER_START = "2025-01-01"
AFTER_END = "2025-04-01"

BASELINE_NDVI_THRESHOLD = 0.40
NDVI_DROP_THRESHOLD = -0.15

EXPORT_FOLDER = "ForestWatch_AI"
EXPORT_NAME = "telangana_forest_change_2024_2025"


# --------------------------------------------------
# EARTH ENGINE INITIALIZATION
# --------------------------------------------------

def initialize_earth_engine():

    project_id = os.getenv("EARTH_ENGINE_PROJECT")

    if not project_id:
        raise RuntimeError(
            "EARTH_ENGINE_PROJECT is missing from .env"
        )

    ee.Initialize(project=project_id)


# --------------------------------------------------
# STUDY REGION
# --------------------------------------------------

def get_region():

    return ee.Geometry.Rectangle(ROI_BOUNDS)


# --------------------------------------------------
# CLOUD AND SHADOW MASKING
# --------------------------------------------------

def mask_clouds(image):

    scl = image.select("SCL")

    invalid = (
        scl.eq(1)
        .Or(scl.eq(3))
        .Or(scl.eq(7))
        .Or(scl.eq(8))
        .Or(scl.eq(9))
        .Or(scl.eq(10))
        .Or(scl.eq(11))
    )

    return (
        image.updateMask(invalid.Not())
        .copyProperties(
            image,
            ["system:time_start"]
        )
    )


# --------------------------------------------------
# CREATE NDVI COMPOSITE
# --------------------------------------------------

def create_ndvi_composite(
    region,
    start_date,
    end_date
):

    collection = (
        ee.ImageCollection(COLLECTION_ID)
        .filterBounds(region)
        .filterDate(start_date, end_date)
        .filter(
            ee.Filter.lte(
                "CLOUDY_PIXEL_PERCENTAGE",
                MAX_CLOUD_PERCENT
            )
        )
        .map(mask_clouds)
    )

    image_count = collection.size().getInfo()

    print(
        f"Images between {start_date} and "
        f"{end_date}: {image_count}"
    )

    if image_count == 0:
        raise RuntimeError(
            f"No Sentinel-2 images found for {start_date}"
        )

    composite = (
        collection
        .median()
        .clip(region)
    )

    ndvi = (
        composite
        .normalizedDifference(["B8", "B4"])
        .rename("NDVI")
    )

    return ndvi, image_count


# --------------------------------------------------
# CALCULATE NDVI DIFFERENCE
# --------------------------------------------------

def calculate_ndvi_difference(
    before_ndvi,
    after_ndvi
):

    valid_pixels = (
        before_ndvi.mask()
        .And(after_ndvi.mask())
    )

    before_valid = before_ndvi.updateMask(valid_pixels)
    after_valid = after_ndvi.updateMask(valid_pixels)

    difference = (
        after_valid
        .subtract(before_valid)
        .rename("NDVI_CHANGE")
    )

    return (
        before_valid,
        after_valid,
        difference
    )


# --------------------------------------------------
# DETECT POTENTIAL VEGETATION LOSS
# --------------------------------------------------

def detect_vegetation_loss(
    before_ndvi,
    difference
):

    previously_vegetated = (
        before_ndvi.gte(BASELINE_NDVI_THRESHOLD)
    )

    significant_decline = (
        difference.lte(NDVI_DROP_THRESHOLD)
    )

    loss_mask = (
        previously_vegetated
        .And(significant_decline)
    )

    loss_map = (
        loss_mask
        .rename("POTENTIAL_LOSS")
        .selfMask()
    )

    return loss_map


# --------------------------------------------------
# CALCULATE POTENTIAL LOSS AREA
# --------------------------------------------------

def calculate_loss_statistics(
    loss_map,
    region
):

    pixel_area = (
        ee.Image.pixelArea()
        .updateMask(loss_map)
        .rename("loss_area")
    )

    result = pixel_area.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=region,
        scale=10,
        maxPixels=1e10,
        tileScale=4,
        bestEffort=True
    )

    area_m2 = result.get("loss_area").getInfo()

    if area_m2 is None:
        area_m2 = 0

    return {
        "potential_loss_area_m2": area_m2,
        "potential_loss_area_hectares": area_m2 / 10000,
        "potential_loss_area_km2": area_m2 / 1000000
    }


# --------------------------------------------------
# EXPORT CHANGE-DETECTION RASTER
# --------------------------------------------------

def export_results(
    before_ndvi,
    after_ndvi,
    difference,
    loss_map,
    region
):

    export_image = (
        before_ndvi
        .addBands(after_ndvi)
        .addBands(difference)
        .addBands(
            loss_map.unmask(0).toByte()
        )
    )

    task = ee.batch.Export.image.toDrive(
        image=export_image.toFloat(),
        description=EXPORT_NAME,
        folder=EXPORT_FOLDER,
        fileNamePrefix=EXPORT_NAME,
        region=region,
        scale=10,
        maxPixels=1e10,
        fileFormat="GeoTIFF"
    )

    task.start()

    print("\nExport submitted successfully.")
    print(f"Task ID: {task.id}")


# --------------------------------------------------
# MAIN EXECUTION
# --------------------------------------------------

def main():

    print("=" * 60)
    print("FORESTWATCH AI - FOREST CHANGE DETECTION")
    print("=" * 60)

    initialize_earth_engine()

    region = get_region()

    print("\nSTEP 1: Processing BEFORE imagery")

    before_ndvi, before_count = create_ndvi_composite(
        region,
        BEFORE_START,
        BEFORE_END
    )

    print("\nSTEP 2: Processing AFTER imagery")

    after_ndvi, after_count = create_ndvi_composite(
        region,
        AFTER_START,
        AFTER_END
    )

    print("\nSTEP 3: Calculating NDVI difference")

    before_valid, after_valid, difference = (
        calculate_ndvi_difference(
            before_ndvi,
            after_ndvi
        )
    )

    print("\nSTEP 4: Detecting potential vegetation loss")

    loss_map = detect_vegetation_loss(
        before_valid,
        difference
    )

    print("\nSTEP 5: Calculating potential loss area")

    statistics = calculate_loss_statistics(
        loss_map,
        region
    )

    print("\nCHANGE DETECTION RESULTS")
    print("-" * 45)

    print(f"Before images: {before_count}")
    print(f"After images: {after_count}")

    for key, value in statistics.items():
        print(f"{key}: {value:.4f}")

    print("\nSTEP 6: Exporting results")

    export_results(
        before_valid,
        after_valid,
        difference,
        loss_map,
        region
    )

    print("\nCHANGE DETECTION COMPLETED")


if __name__ == "__main__":
    main()
