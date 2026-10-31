
import json
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

YEAR = 2025

MONTHS = range(1, 7)

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

OUTPUT_FILE = OUTPUT_DIR / "historical_ndvi.json"


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
# MONTHLY NDVI CALCULATION
# --------------------------------------------------

def calculate_monthly_ndvi(
    region,
    year,
    month
):
    start_date = f"{year}-{month:02d}-01"

    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"

    print(f"\nProcessing {year}-{month:02d}")

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
    )

    image_count = collection.size().getInfo()

    if image_count == 0:
        print("No matching images found.")

        return {
            "year": year,
            "month": month,
            "image_count": 0,
            "mean_ndvi": None,
            "min_ndvi": None,
            "max_ndvi": None
        }

    cleaned_collection = collection.map(mask_clouds)

    composite = (
        cleaned_collection
        .median()
        .clip(region)
    )

    ndvi = composite.normalizedDifference(
        ["B8", "B4"]
    ).rename("NDVI")

    statistics = ndvi.reduceRegion(
        reducer=(
            ee.Reducer.mean()
            .combine(
                reducer2=ee.Reducer.minMax(),
                sharedInputs=True
            )
        ),
        geometry=region,
        scale=20,
        maxPixels=1e10,
        bestEffort=True,
        tileScale=4
    ).getInfo()

    result = {
        "year": year,
        "month": month,
        "start_date": start_date,
        "end_date_exclusive": end_date,
        "image_count": image_count,
        "mean_ndvi": statistics.get("NDVI_mean"),
        "min_ndvi": statistics.get("NDVI_min"),
        "max_ndvi": statistics.get("NDVI_max")
    }

    print(f"Images: {image_count}")
    print(f"Mean NDVI: {result['mean_ndvi']}")

    return result


# --------------------------------------------------
# MAIN EXECUTION
# --------------------------------------------------

def main():

    print("=" * 55)
    print("FORESTWATCH AI - HISTORICAL NDVI ANALYSIS")
    print("=" * 55)

    initialize_earth_engine()

    region = get_region()

    monthly_results = []

    for month in MONTHS:

        result = calculate_monthly_ndvi(
            region,
            YEAR,
            month
        )

        monthly_results.append(result)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output = {
        "project": "ForestWatch AI",
        "region": "Telangana, India",
        "year": YEAR,
        "dataset": COLLECTION_ID,
        "monthly_observations": monthly_results
    }

    OUTPUT_FILE.write_text(
        json.dumps(output, indent=4),
        encoding="utf-8"
    )

    print("\n" + "=" * 55)
    print("HISTORICAL ANALYSIS COMPLETED")
    print("=" * 55)

    print(f"Results saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
