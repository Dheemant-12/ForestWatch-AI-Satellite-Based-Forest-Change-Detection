import pandas as pd



from fastapi.responses import Response

from fastapi import Query

from pathlib import Path

import json\nimport hashlib



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



def generate_detection_id(geometry):
    """
    Generate a deterministic ID from detection geometry.

    IDs remain unchanged when records are reordered or non-geometric
    properties are updated.
    """
    if geometry is None or geometry.is_empty:
        raise ValueError("Cannot generate an ID for an empty geometry.")

    digest = hashlib.sha256(geometry.wkb).hexdigest()[:12].upper()

    return f"FW-{digest}"


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

    # Standardize the area field used by analytics and filters.
    if "area_ha" not in gdf.columns and "area_hectares" in gdf.columns:
        gdf["area_ha"] = pd.to_numeric(
            gdf["area_hectares"], errors="coerce"
        )

    # Remove missing, empty, and invalid geometries.
    gdf = gdf[
        gdf.geometry.notna()
        & ~gdf.geometry.is_empty
        & gdf.geometry.is_valid
    ].copy()

    # Generate deterministic IDs independent of row order.
    gdf["detection_id"] = gdf.geometry.apply(
        generate_detection_id
    )

    # Add candidate status.
    gdf["status"] = "Potential vegetation loss"

    return gdf


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





@app.get("/api/v1/detections/export/geojson")

def export_detections_geojson(

    min_area_ha: float = Query(default=0.0, ge=0.0)

):

    """Download detection candidates as a GeoJSON file."""

    from fastapi.responses import Response



    gdf = load_detections()



    if min_area_ha > 0:

        if "area_ha" not in gdf.columns:

            raise HTTPException(

                status_code=400,

                detail="Area filtering is unavailable because area_ha is missing."

            )



        gdf = gdf[

            gdf["area_ha"].fillna(0) >= min_area_ha

        ].copy()



    geojson_content = gdf.to_json()



    return Response(

        content=geojson_content,

        media_type="application/geo+json",

        headers={

            "Content-Disposition": 'attachment; filename="forestwatch_detections.geojson"'

        }

    )






@app.get("/api/v1/detections/timeline")
def get_detection_timeline():
    """Return detection counts grouped by available observation dates."""
    import pandas as pd

    gdf = load_detections()

    date_fields = [
        "observation_date",
        "acquired_at",
        "detection_date",
        "date",
        "timestamp",
        "before_date",
        "after_date",
    ]

    available_fields = [
        field for field in date_fields if field in gdf.columns
    ]

    if gdf.empty or not available_fields:
        return {
            "timeline": [],
            "date_fields_found": available_fields,
            "total_detections": len(gdf),
            "message": (
                "No usable observation-date fields were found in the "
                "detection dataset."
            ),
        }

    timeline = []

    for field in available_fields:
        parsed_dates = pd.to_datetime(
            gdf[field],
            errors="coerce",
            utc=True
        ).dropna()

        if parsed_dates.empty:
            continue

        counts = (
            parsed_dates.dt.strftime("%Y-%m-%d")
            .value_counts()
            .sort_index()
        )

        for date_value, count in counts.items():
            timeline.append({
                "date": date_value,
                "date_field": field,
                "detections": int(count),
            })

    timeline.sort(key=lambda item: (item["date"], item["date_field"]))

    return {
        "timeline": timeline,
        "date_fields_found": available_fields,
        "total_detections": len(gdf),
        "message": (
            "Timeline generated from available detection date fields."
            if timeline
            else "Date fields exist, but no valid dates could be parsed."
        ),
    }


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



# --------------------------------------------------
# DETECTION DATA QUALITY
# --------------------------------------------------

@app.get("/api/v1/detections/quality")
def get_detection_quality():
    """Inspect detection data quality before analytics and mapping."""

    try:
        gdf = load_detections()

        total = len(gdf)

        area_field = next(
            (
                field for field in ["area_ha", "area_hectares"]
                if field in gdf.columns
            ),
            None
        )

        valid_area_count = 0
        area_coverage = 0.0

        if area_field:
            areas = pd.to_numeric(
                gdf[area_field],
                errors="coerce"
            )

            valid_areas = areas.notna() & (areas >= 0)
            valid_area_count = int(valid_areas.sum())

            if total:
                area_coverage = round(
                    valid_area_count / total * 100,
                    2
                )

        valid_geometry_count = int(
            (
                gdf.geometry.notna()
                & ~gdf.geometry.is_empty
                & gdf.geometry.is_valid
            ).sum()
        )

        date_fields = [
            "observation_date",
            "acquired_at",
            "detection_date",
            "date",
            "timestamp",
            "before_date",
            "after_date",
            "before_period_start",
            "before_period_end",
            "after_period_start",
            "after_period_end",
        ]

        available_date_fields = [
            field for field in date_fields
            if field in gdf.columns
        ]

        checks = {
            "has_records": total > 0,
            "has_area_information": area_field is not None,
            "all_records_have_area": (
                valid_area_count == total if total else False
            ),
            "all_geometries_valid": (
                valid_geometry_count == total if total else False
            ),
        }

        passed = sum(checks.values())
        quality_status = (
            "good" if all(checks.values())
            else "needs_attention"
        )

        return {
            "quality_status": quality_status,
            "total_records": total,
            "valid_geometries": valid_geometry_count,
            "invalid_geometries": total - valid_geometry_count,
            "area_field_used": area_field,
            "records_with_valid_area": valid_area_count,
            "area_coverage_percent": area_coverage,
            "date_fields_found": available_date_fields,
            "coordinate_system": (
                gdf.crs.to_string() if gdf.crs else None
            ),
            "checks_passed": passed,
            "checks_total": len(checks),
            "checks": checks,
        }

    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to inspect detection quality: {error}"
        )


@app.get("/api/v1/analytics")

def get_analytics():

    """

    Return statistical information about candidate detections.

    """



    gdf = load_detections()



    if gdf.empty:

        return {

            "total_detections": 0,

            "total_candidate_area_ha": 0,

            "average_area_ha": 0,

            "largest_detection_ha": 0,

            "smallest_detection_ha": 0,

            "area_distribution": {

                "under_1_ha": 0,

                "1_to_5_ha": 0,

                "5_to_10_ha": 0,

                "over_10_ha": 0

            },

            "message": "No detection records available."

        }



    if "area_ha" not in gdf.columns:

        raise HTTPException(

            status_code=400,

            detail="Area information is unavailable. "

                   "Regenerate the detection GeoJSON with area_ha."

        )



    # Ignore missing, infinite, and negative area values.

    import numpy as np



    areas = pd.to_numeric(gdf["area_ha"], errors="coerce")

    areas = areas.replace([np.inf, -np.inf], np.nan).dropna()

    areas = areas[areas >= 0]



    if areas.empty:

        raise HTTPException(

            status_code=400,

            detail="No valid area measurements are available."

        )



    return {

        "total_detections": int(len(gdf)),

        "detections_with_valid_area": int(len(areas)),

        "total_candidate_area_ha": round(float(areas.sum()), 2),

        "average_area_ha": round(float(areas.mean()), 2),

        "largest_detection_ha": round(float(areas.max()), 2),

        "smallest_detection_ha": round(float(areas.min()), 2),

        "area_distribution": {

            "under_1_ha": int((areas < 1).sum()),

            "1_to_5_ha": int(((areas >= 1) & (areas < 5)).sum()),

            "5_to_10_ha": int(((areas >= 5) & (areas < 10)).sum()),

            "over_10_ha": int((areas >= 10).sum())

        }

    }


# --------------------------------------------------
# GET INDIVIDUAL DETECTION — KEEP AFTER STATIC ROUTES
# --------------------------------------------------

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
