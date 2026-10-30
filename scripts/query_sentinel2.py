
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import ee
from dotenv import load_dotenv


# Resolve paths from the repository root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "sentinel2_query_results.json"

# Initial study area: a rectangular sample region in Telangana.
# Coordinates are [west, south, east, north].
ROI_BOUNDS = [80.0, 17.8, 80.6, 18.4]

START_DATE = "2025-01-01"
END_DATE = "2025-03-01"  # Earth Engine end date is exclusive.
MAX_CLOUD_PERCENT = 30

COLLECTION_ID = "COPERNICUS/S2_SR_HARMONIZED"


def initialize_earth_engine() -> None:
    """Initialize Earth Engine using the configured Cloud project."""
    project_id = os.getenv("EARTH_ENGINE_PROJECT")

    if not project_id:
        raise RuntimeError(
            "EARTH_ENGINE_PROJECT is missing. "
            "Set it in the project-root .env file."
        )

    ee.Initialize(project=project_id)


def query_satellite_imagery() -> dict:
    """Query Sentinel-2 images and return acquisition metadata."""
    roi = ee.Geometry.Rectangle(ROI_BOUNDS)

    collection = (
        ee.ImageCollection(COLLECTION_ID)
        .filterBounds(roi)
        .filterDate(START_DATE, END_DATE)
        .filter(
            ee.Filter.lte(
                "CLOUDY_PIXEL_PERCENTAGE",
                MAX_CLOUD_PERCENT,
            )
        )
        .sort("system:time_start")
    )

    image_count = collection.size().getInfo()

    results = {
        "dataset": COLLECTION_ID,
        "region": "Telangana, India (initial sample ROI)",
        "roi_bounds": ROI_BOUNDS,
        "start_date": START_DATE,
        "end_date_exclusive": END_DATE,
        "max_scene_cloud_percent": MAX_CLOUD_PERCENT,
        "image_count": image_count,
        "images": [],
    }

    if image_count == 0:
        print("No images matched the current filters.")
        return results

    timestamps = (
        collection.aggregate_array("system:time_start").getInfo()
    )
    cloud_percentages = (
        collection.aggregate_array(
            "CLOUDY_PIXEL_PERCENTAGE"
        ).getInfo()
    )
    image_ids = (
        collection.aggregate_array("system:index").getInfo()
    )

    for image_id, timestamp, cloud_percent in zip(
        image_ids, timestamps, cloud_percentages
    ):
        acquired_at = datetime.fromtimestamp(
            timestamp / 1000,
            tz=timezone.utc,
        )

        results["images"].append(
            {
                "image_id": image_id,
                "acquired_at_utc": acquired_at.isoformat(),
                "scene_cloud_percent": cloud_percent,
            }
        )

    return results


def main() -> None:
    print("Initializing Google Earth Engine...")
    initialize_earth_engine()

    print("Querying Sentinel-2 imagery...")
    results = query_satellite_imagery()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )

    print(f"\nDataset: {results['dataset']}")
    print(f"Date range: {START_DATE} to {END_DATE}")
    print(f"Matching images: {results['image_count']}")

    for image in results["images"]:
        print(
            f"{image['acquired_at_utc']} | "
            f"Cloud: {image['scene_cloud_percent']}% | "
            f"ID: {image['image_id']}"
        )

    print(f"\nResults saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
