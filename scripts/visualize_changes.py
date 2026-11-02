
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

BASELINE_THRESHOLD = 0.40
LOSS_THRESHOLD = -0.15

EXPORT_FOLDER = "ForestWatch_AI"

OUTPUT_DIR = PROJECT_ROOT / "data" / "exports"


# --------------------------------------------------
# EARTH ENGINE INITIALIZATION
# --------------------------------------------------

def initialize_earth_engine():

    project_id = os.getenv("EARTH_ENGINE_PROJECT")

    if not project_id:
        raise RuntimeError(
            "EARTH_ENGINE_PROJECT missing from .env"
        )

    ee.Initialize(project=project_id)


# --------------------------------------------------
# REGION
# --------------------------------------------------

def get_region():

    return ee.Geometry.Rectangle(ROI_BOUNDS)


# --------------------------------------------------
# CLOUD MASKING
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

    return image.updateMask(
        invalid.Not()
    )


# --------------------------------------------------
# CREATE NDVI COMPOSITE
# --------------------------------------------------

def create_ndvi(
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

    count = collection.size().getInfo()

    print(
        f"{start_date} to {end_date}: "
        f"{count} images"
    )

    if count == 0:
        raise RuntimeError(
            f"No imagery available for {start_date}"
        )

    composite = collection.median().clip(region)

    return (
        composite
        .normalizedDifference(["B8", "B4"])
        .rename("NDVI")
    )


# --------------------------------------------------
# VISUALIZATION CONFIGURATION
# --------------------------------------------------

def visualize_ndvi(image):

    return image.visualize(
        min=0.0,
        max=0.8,
        palette=[
            "8c510a",
            "d8b365",
            "f6e8c3",
            "a6d96a",
            "1a9850",
            "006837"
        ]
    )


def visualize_difference(image):

    return image.visualize(
        min=-0.3,
        max=0.3,
        palette=[
            "d7191c",
            "fdae61",
            "ffffbf",
            "a6d96a",
            "1a9641"
        ]
    )


def visualize_loss(image):

    return image.visualize(
        min=0,
        max=1,
        palette=["ff0000"]
    )


# --------------------------------------------------
# EXPORT VISUALIZATION
# --------------------------------------------------

def export_visualization(
    image,
    region,
    filename
):

    task = ee.batch.Export.image.toDrive(
        image=image,
        description=filename,
        folder=EXPORT_FOLDER,
        fileNamePrefix=filename,
        region=region,
        scale=10,
        maxPixels=1e10,
        fileFormat="GeoTIFF"
    )

    task.start()

    print(f"Export submitted: {filename}")
    print(f"Task ID: {task.id}")


# --------------------------------------------------
# MAIN PIPELINE
# --------------------------------------------------

def main():

    print("=" * 60)
    print("FORESTWATCH AI - CHANGE VISUALIZATION")
    print("=" * 60)

    initialize_earth_engine()

    region = get_region()

    print("\nGenerating 2024 NDVI...")

    before = create_ndvi(
        region,
        BEFORE_START,
        BEFORE_END
    )

    print("\nGenerating 2025 NDVI...")

    after = create_ndvi(
        region,
        AFTER_START,
        AFTER_END
    )

    # Use only pixels valid in both periods.
    valid_mask = before.mask().And(after.mask())

    before = before.updateMask(valid_mask)
    after = after.updateMask(valid_mask)

    print("\nCalculating NDVI difference...")

    difference = (
        after.subtract(before)
        .rename("NDVI_CHANGE")
    )

    print("\nDetecting potential vegetation loss...")

    loss = (
        before.gte(BASELINE_THRESHOLD)
        .And(difference.lte(LOSS_THRESHOLD))
        .rename("POTENTIAL_LOSS")
        .selfMask()
    )

    # Visualization images.
    before_visual = visualize_ndvi(before)

    after_visual = visualize_ndvi(after)

    difference_visual = visualize_difference(
        difference
    )

    loss_visual = visualize_loss(loss)

    # Create output directory.
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print("\nSubmitting visualization exports...")

    exports = [
        (
            before_visual,
            "ndvi_before_2024"
        ),
        (
            after_visual,
            "ndvi_after_2025"
        ),
        (
            difference_visual,
            "ndvi_change_2024_2025"
        ),
        (
            loss_visual,
            "potential_forest_loss_2025"
        )
    ]

    for image, filename in exports:

        export_visualization(
            image,
            region,
            filename
        )

    print("\n" + "=" * 60)
    print("VISUALIZATION EXPORTS SUBMITTED")
    print("=" * 60)

    print(f"Google Drive folder: {EXPORT_FOLDER}")
    print(f"Local output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
