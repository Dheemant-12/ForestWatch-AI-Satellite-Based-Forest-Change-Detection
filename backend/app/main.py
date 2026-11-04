import pandas as pd

from fastapi.responses import Response
from fastapi import Query
from pathlib import Path
import json

import geopandas as gpd
from fastapi import FastAPI, HTTPException, Query
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
        "API for retrieving and analyzing "
        "satellite-based potential vegetation-loss "
        "detections in Telangana."
    ),
    version="1.1.0",
)


# --------------------------------------------------
# CORS CONFIGURATION
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
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
            "Detection GeoJSON has no CRS information. "
            "Identify its original coordinate system "
            "before converting it."
        )

    # Convert coordinates to web-map standard.
    gdf = gdf.to_crs(epsg=4326)

    # Remove missing and empty geometries.
    gdf = gdf[
        gdf.geometry.notna()
        & ~gdf.geometry.is_empty
    ].copy()

    # Remove invalid geometries.
    gdf = gdf[gdf.geometry.is_valid].copy()

    # Generate detection IDs.
    # These are temporary IDs based on row order.
    gdf = gdf.reset_index(drop=True)

    gdf["detection_id"] = [
        f"FW-{i + 1:04d}"
        for i in range(len(gdf))
    ]

    # Add candidate status.
    gdf["status"] = "Potential vegetation loss"

    return gdf


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "project": "ForestWatch AI",
        "version": "1.1.0",
    }


# --------------------------------------------------
# GET ALL DETECTIONS
# --------------------------------------------------

@app.get("/api/v1/detections")
def get_detections():

    try:

        gdf = load_detections()

        return json.loads(
            gdf.to_json(drop_id=True)
        )

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

        summary = {
            "region": "Telangana, India",
            "total_detections": len(gdf),
            "coordinate_system": "EPSG:4326",
            "data_source": "Sentinel-2",
            "detection_type": "Potential vegetation loss",
        }

        if "area_ha" in gdf.columns:

            total_area = gdf["area_ha"].fillna(0).sum()

            summary["total_candidate_area_ha"] = round(
                float(total_area),
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


# --------------------------------------------------
# GET INDIVIDUAL DETECTION
# --------------------------------------------------
@app.get("/api/v1/detections/export/csv")
def export_detections_csv(
    min_area_ha: float = Query(default=0, ge=0)
):
    """
    Export detection records as a downloadable CSV file.
    """

    gdf = load_detections()

    if gdf.empty:
        raise HTTPException(
            status_code=404,
            detail="No detection records available for export."
        )

    # Apply minimum-area filtering when area_ha exists.
    if min_area_ha > 0:
        if "area_ha" not in gdf.columns:
            raise HTTPException(
                status_code=400,
                detail="Area information is unavailable."
            )

        gdf = gdf[gdf["area_ha"] >= min_area_ha]

    if gdf.empty:
        raise HTTPException(
            status_code=404,
            detail="No detections match the selected area filter."
        )

    # Preserve spatial information as WKT text.
    export_df = pd.DataFrame(gdf.drop(columns="geometry"))

    export_df["geometry_wkt"] = gdf.geometry.to_wkt()

    csv_content = export_df.to_csv(index=False)

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                "attachment; filename=forestwatch_detections.csv"
            )
        }
    )

@app.get("/api/v1/detections/{detection_id}")
def get_detection(detection_id: str):

    try:

        gdf = load_detections()

        if gdf.empty:
            raise HTTPException(
                status_code=404,
                detail="No detections available.",
            )

        result = gdf[
            gdf["detection_id"] == detection_id
        ]

        if result.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Detection {detection_id} not found.",
            )

        return json.loads(
            result.to_json(drop_id=True)
        )

    except FileNotFoundError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve detection: {error}",
        )


# --------------------------------------------------
# FILTER DETECTIONS BY MINIMUM AREA
# --------------------------------------------------

@app.get("/api/v1/detections/filter")
def filter_detections(
    min_area_ha: float = Query(
        default=0.0,
        ge=0.0,
        description="Minimum candidate polygon area in hectares.",
    )
):

    try:

        gdf = load_detections()

        if "area_ha" not in gdf.columns:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Area filtering is unavailable because "
                    "the GeoJSON has no area_ha property."
                ),
            )

        filtered = gdf[
            gdf["area_ha"].fillna(0) >= min_area_ha
        ]

        return json.loads(
            filtered.to_json(drop_id=True)
        )

    except FileNotFoundError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Unable to filter detections: {error}",
        )
