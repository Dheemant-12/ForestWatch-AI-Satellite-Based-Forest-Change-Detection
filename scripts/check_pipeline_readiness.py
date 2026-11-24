import importlib.util
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def check_file(label: str, relative_path: str) -> bool:
    exists = (ROOT / relative_path).is_file()
    print(f"[{'OK' if exists else 'MISSING'}] {label}: {relative_path}")
    return exists


def check_directory(label: str, relative_path: str) -> bool:
    exists = (ROOT / relative_path).is_dir()
    print(f"[{'OK' if exists else 'MISSING'}] {label}: {relative_path}")
    return exists


def check_package(label: str, module_name: str) -> bool:
    installed = importlib.util.find_spec(module_name) is not None
    print(f"[{'OK' if installed else 'MISSING'}] Package: {label}")
    return installed


def main() -> None:
    print("=" * 60)
    print("FORESTWATCH AI - PIPELINE READINESS CHECK")
    print("=" * 60)

    results = []

    print("\n1. PROCESSING SCRIPTS")
    results.append(check_file("Detection script", "scripts/detect_forest_loss.py"))
    results.append(check_file("Filtering script", "scripts/filter_forest_loss.py"))
    results.append(check_file("NDVI script", "scripts/calculate_ndvi.py"))
    results.append(check_file("Raster alignment script", "scripts/align_rasters.py"))

    print("\n2. DATA DIRECTORIES")
    results.append(check_directory("Raw data directory", "data/raw"))
    results.append(check_directory("Export directory", "data/exports"))
    results.append(check_directory("Processed data directory", "data/processed"))
    results.append(check_directory("Reports directory", "data/reports"))

    print("\n3. EXPECTED DATA FILES")
    results.append(check_file(
        "Analytical GeoTIFF",
        "data/exports/telangana_forest_change_2024_2025.tif"
    ))
    results.append(check_file(
        "Processed detection GeoJSON",
        "data/processed/forest_loss/forest_loss_polygons.geojson"
    ))
    results.append(check_file(
        "API benchmark report",
        "data/reports/api_performance.csv"
    ))

    print("\n4. PYTHON DEPENDENCIES")
    packages = {
        "Earth Engine": "ee",
        "Rasterio": "rasterio",
        "NumPy": "numpy",
        "SciPy": "scipy",
        "GeoPandas": "geopandas",
        "Shapely": "shapely",
        "FastAPI": "fastapi",
        "Uvicorn": "uvicorn",
        "Python dotenv": "dotenv",
    }

    for label, module in packages.items():
        results.append(check_package(label, module))

    print("\n5. EARTH ENGINE CONFIGURATION")
    configured = bool(os.getenv("EARTH_ENGINE_PROJECT", "").strip())
    print(
        "[OK] Project ID configured in environment"
        if configured
        else "[PENDING] Earth Engine project ID not configured"
    )

    passed = sum(results)
    total = len(results)

    print("\n" + "=" * 60)
    print(f"CHECKS PASSED: {passed}/{total}")
    print(f"CHECKS NEEDING ATTENTION: {total - passed}")
    print("=" * 60)
    print("Readiness report completed. Missing data is not fabricated.")


if __name__ == "__main__":
    main()
