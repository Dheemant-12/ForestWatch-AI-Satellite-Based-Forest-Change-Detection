
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

START_DATE = "2025-01-01"
END_DATE = "2025-03-01"

MAX_CLOUD_PERCENT = 30

COLLECTION_ID = "COPERNICUS/S2_SR_HARMONIZED"

EXPORT_FOLDER = "ForestWatch_AI"
EXPORT_NAME = "telangana_ndvi_2025"


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
# REGION OF INTEREST
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
# RETRIEVE SATELLITE IMAGES
# --------------------------------------------------

def get_collection(region):
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
        .map(mask_clouds)
    )

    return collection


# --------------------------------------------------
# CREATE MEDIAN COMPOSITE
# --------------------------------------------------

def create_composite(collection, region):
    return collection.median().clip(region)


# --------------------------------------------------
# CALCULATE NDVI
# --------------------------------------------------

def calculate_ndvi(composite):
    ndvi = composite.normalizedDifference(
        ["B8", "B4"]
    ).rename("NDVI")

    return ndvi


# --------------------------------------------------
# NDVI STATISTICS
# --------------------------------------------------

def calculate_statistics(ndvi, region):
    statistics = ndvi.reduceRegion(
        reducer=(
            ee.Reducer.mean()
            .combine(
                reducer2=ee.Reducer.minMax(),
                sharedInputs=True
            )
        ),
        geometry=region,
        scale=10,
        maxPixels=1e10,
        bestEffort=True,
        tileScale=4
    )

    return statistics.getInfo()


# --------------------------------------------------
# EXPORT NDVI RASTER
# --------------------------------------------------

def export_ndvi(ndvi, region):
    task = ee.batch.Export.image.toDrive(
        image=ndvi.toFloat(),
        description=EXPORT_NAME,
        folder=EXPORT_FOLDER,
        fileNamePrefix=EXPORT_NAME,
        region=region,
        scale=10,
        maxPixels=1e10,
        fileFormat="GeoTIFF"
    )

    task.start()

    print("\nNDVI export submitted successfully.")
    print(f"Task ID: {task.id}")
    print(f"Drive folder: {EXPORT_FOLDER}")


# --------------------------------------------------
# MAIN EXECUTION
# --------------------------------------------------

def main():
    print("=" * 55)
    print("FORESTWATCH AI - NDVI ANALYSIS")
    print("=" * 55)

    print("\nInitializing Earth Engine...")
    initialize_earth_engine()

    region = get_region()

    print("Retrieving Sentinel-2 imagery...")

    collection = get_collection(region)

    image_count = collection.size().getInfo()

    print(f"Images retrieved: {image_count}")

    if image_count == 0:
        raise RuntimeError(
            "No matching satellite images found."
        )

    print("\nCreating cloud-masked median composite...")

    composite = create_composite(
        collection,
        region
    )

    print("Calculating NDVI...")

    ndvi = calculate_ndvi(composite)

    print("\nCalculating NDVI statistics...")

    statistics = calculate_statistics(
        ndvi,
        region
    )

    print("\nNDVI RESULTS")
    print("-" * 40)

    for key, value in statistics.items():
        print(f"{key}: {value}")

    if statistics.get("NDVI_mean") is None:
        raise RuntimeError(
            "NDVI statistics are empty. "
            "Check valid-pixel coverage."
        )

    print("\nExporting NDVI raster...")

    export_ndvi(ndvi, region)

    print("\nNDVI ANALYSIS COMPLETED")


if __name__ == "__main__":
    main()
