
from pathlib import Path

import geopandas as gpd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DETECTIONS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "forest_loss"
    / "forest_loss_polygons.geojson"
)


# --------------------------------------------------
# FASTAPI APPLICATION
# --------------------------------------------------

app = FastAPI(
    title="ForestWatch AI API",
    description=(
        "API for retrieving satellite-based "
        "potential forest-loss detections in Telangana."
    ),
    version="1.0.0",
)


# --------------------------------------------------
# CORS CONFIGURATION
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this for production.
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


# --------------------------------------------------
# LOAD AND PREPARE GEOJSON
# --------------------------------------------------

def load_detections():

    if not DETECTIONS_FILE.exists():
        raise FileNotFoundError(
            f"Detection file not found: {DETECTIONS_FILE}"
        )

    gdf = gpd.read_file(DETECTIONS_FILE)

    if gdf.empty:
        return gdf

    if gdf.crs is None:
        raise ValueError(
            "The detection GeoJSON has no CRS information. "
            "Its original coordinate system must be identified "
            "before conversion."
        )

    # Convert coordinates to standard web-map coordinates.
    gdf = gdf.to_crs(epsg=4326)

    # Remove invalid or empty geometries.
    gdf = gdf[
        gdf.geometry.notna()
        & ~gdf.geometry.is_empty
    ].copy()

    gdf = gdf[gdf.geometry.is_valid].copy()

    return gdf


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "project": "ForestWatch AI",
        "version": "1.0.0",
    }


# --------------------------------------------------
# GET ALL FOREST-LOSS DETECTIONS
# --------------------------------------------------

@app.get("/api/v1/detections")
def get_detections():

    try:
        gdf = load_detections()

        geojson = gdf.to_json(
            drop_id=True
        )

        import json

        return json.loads(geojson)

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load detections: {error}",
        )


# --------------------------------------------------
# GET DETECTION SUMMARY
# --------------------------------------------------

@app.get("/api/v1/detections/summary")
def get_detection_summary():

    try:
        gdf = load_detections()

        total_detections = len(gdf)

        summary = {
            "region": "Telangana, India",
            "total_detections": total_detections,
            "coordinate_system": "EPSG:4326",
            "data_source": "Sentinel-2",
            "detection_type": "Potential vegetation loss",
        }

        # Include area statistics when the source
        # GeoJSON contains an area_ha property.
        if "area_ha" in gdf.columns:
            summary["total_candidate_area_ha"] = round(
                float(gdf["area_ha"].fillna(0).sum()),
                3,
            )

        return summary

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to calculate summary: {error}",
        )
