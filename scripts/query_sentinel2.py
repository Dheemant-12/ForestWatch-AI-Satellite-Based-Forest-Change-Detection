
import os
from pathlib import Path

import ee
from dotenv import load_dotenv


# --------------------------------------------------
# PROJECT CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

ROI_BOUNDS = [80.0, 17.8, 80.6, 18.4]

START_DATE = "2025-01-01"
END_DATE = "2025-03-01"

MAX_CLOUD_PERCENT = 30

COLLECTION_ID = "COPERNICUS/S2_SR_HARMONIZED"

EXPORT_FOLDER = "ForestWatch_AI"

EXPORT_NAME = "telangana_cloud_masked_composite"


# --------------------------------------------------
# EARTH ENGINE INITIALIZATION
# --------------------------------------------------

def initialize_earth_engine() -> None:
    project_id = os.getenv("EARTH_ENGINE_PROJECT")

    if not project_id:
        raise RuntimeError(
            "EARTH_ENGINE_PROJECT is missing from .env"
        )

    ee.Initialize(project=project_id)


# --------------------------------------------------
# REGION OF INTEREST
# --------------------------------------------------

def get_region():
    return ee.Geometry.Rectangle(ROI_BOUNDS)


# --------------------------------------------------
# CLOUD AND SHADOW MASKING
# --------------------------------------------------

def mask_clouds(image):
    scl = image.select("SCL")

    # Exclude defective pixels, cloud shadows,
    # unclassified pixels, clouds, cirrus and snow.
    invalid_classes = (
        scl.eq(1)
        .Or(scl.eq(3))
        .Or(scl.eq(7))
        .Or(scl.eq(8))
        .Or(scl.eq(9))
        .Or(scl.eq(10))
        .Or(scl.eq(11))
    )

    valid_mask = invalid_classes.Not()

    return (
        image.updateMask(valid_mask)
        .copyProperties(
            image,
            ["system:time_start", "system:index"]
        )
    )


# --------------------------------------------------
# SATELLITE COLLECTION
# --------------------------------------------------

def get_satellite_collection(region):
    collection = (
        ee.ImageCollection(COLLECTION_ID)
        .filterBounds(region)
        .filterDate(START_DATE, END_DATE)
        .filter(
            ee.Filter.lte(
                "CLOUDY_PIXEL_PERCENTAGE",
                MAX_CLOUD_PERCENT
            )
        )
    )

    return collection


# --------------------------------------------------
# CREATE CLEAN COMPOSITE
# --------------------------------------------------

def create_composite(collection):
    cleaned_collection = collection.map(mask_clouds)

    composite = (
        cleaned_collection
        .median()
        .clip(get_region())
    )

    return composite


# --------------------------------------------------
# VALID PIXEL COVERAGE
# --------------------------------------------------

def calculate_valid_coverage(composite, region):
    valid_area = (
        ee.Image.pixelArea()
        .updateMask(composite.select("B8").mask())
        .rename("valid_area")
    )

    total_area = ee.Image.pixelArea().rename("total_area")

    area_image = valid_area.addBands(total_area)

    statistics = area_image.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=region,
        scale=20,
        maxPixels=1e10,
        bestEffort=True
    )

    values = statistics.getInfo()

    valid = values.get("valid_area") or 0
    total = values.get("total_area") or 0

    if total == 0:
        return 0.0

    return (valid / total) * 100


# --------------------------------------------------
# EXPORT COMPOSITE TO GOOGLE DRIVE
# --------------------------------------------------

def export_composite(composite, region):
    export_image = composite.select(
        ["B2", "B3", "B4", "B8"]
    )

    task = ee.batch.Export.image.toDrive(
        image=export_image,
        description=EXPORT_NAME,
        folder=EXPORT_FOLDER,
        fileNamePrefix=EXPORT_NAME,
        region=region,
        scale=10,
        maxPixels=1e10,
        fileFormat="GeoTIFF"
    )

    task.start()

    print("\nExport task submitted.")
    print(f"Task ID: {task.id}")
    print(f"Google Drive folder: {EXPORT_FOLDER}")


# --------------------------------------------------
# MAIN EXECUTION
# --------------------------------------------------

def main():
    print("=" * 55)
    print("FORESTWATCH AI - CLOUD MASKING PIPELINE")
    print("=" * 55)

    print("\nInitializing Earth Engine...")
    initialize_earth_engine()

    region = get_region()

    print("Retrieving Sentinel-2 collection...")

    collection = get_satellite_collection(region)

    image_count = collection.size().getInfo()

    print(f"Matching satellite images: {image_count}")

    if image_count == 0:
        print("No matching images. Check date and region filters.")
        return

    print("\nApplying cloud and shadow masks...")

    composite = create_composite(collection)

    print("Calculating valid-pixel coverage...")

    coverage = calculate_valid_coverage(
        composite,
        region
    )

    print(f"Valid pixel coverage: {coverage:.2f}%")

    print("\nSubmitting GeoTIFF export...")

    export_composite(composite, region)

    print("\nPipeline execution completed.")
    print("Check Earth Engine Tasks for export progress.")


if __name__ == "__main__":
    main()
