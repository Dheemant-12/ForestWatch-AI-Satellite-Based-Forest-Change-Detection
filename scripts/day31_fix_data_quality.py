from pathlib import Path

path = Path("backend/app/main.py")
source = path.read_text(encoding="utf-8")

# Fix 1: Normalize area_hectares to area_ha during data loading.
old = '''    gdf = gpd.read_file(DETECTIONS_FILE)



    if gdf.empty:'''

new = '''    gdf = gpd.read_file(DETECTIONS_FILE)

    # Standardize the area property used by analytics and filters.
    # The filtering script exports area_hectares.
    if "area_ha" not in gdf.columns and "area_hectares" in gdf.columns:
        gdf["area_ha"] = pd.to_numeric(
            gdf["area_hectares"], errors="coerce"
        )

    if gdf.empty:'''

if old not in source:
    raise SystemExit("Could not find the area-normalization insertion point.")

source = source.replace(old, new, 1)

# Fix 2: Audit the original GeoJSON, before invalid geometries are removed.
start = source.find('@app.get("/api/v1/detections/quality")')
end = source.find('\\n\\n\\n@app.get("/api/v1/analytics")', start)

if start == -1 or end == -1:
    raise SystemExit("Could not locate the quality endpoint.")

quality_endpoint = '''@app.get("/api/v1/detections/quality")
def get_detection_quality():
    """Audit the original GeoJSON before invalid records are filtered."""

    try:
        if not DETECTIONS_FILE.exists():
            raise FileNotFoundError(
                f"Detection file not found: {DETECTIONS_FILE}"
            )

        # Read the source directly, not through load_detections().
        raw = gpd.read_file(DETECTIONS_FILE)
        total = len(raw)

        area_field = next(
            (
                field for field in ["area_ha", "area_hectares"]
                if field in raw.columns
            ),
            None
        )

        valid_area_count = 0
        area_coverage = 0.0

        if area_field:
            import numpy as np

            areas = pd.to_numeric(raw[area_field], errors="coerce")
            valid_areas = (
                areas.notna()
                & np.isfinite(areas)
                & (areas >= 0)
            )
            valid_area_count = int(valid_areas.sum())

            if total:
                area_coverage = round(
                    valid_area_count / total * 100, 2
                )

        geometry_present = raw.geometry.notna()
        geometry_nonempty = geometry_present & ~raw.geometry.is_empty
        geometry_valid = geometry_nonempty & raw.geometry.is_valid

        valid_geometry_count = int(geometry_valid.sum())
        invalid_geometry_count = total - valid_geometry_count

        date_fields = [
            "observation_date", "acquired_at", "detection_date",
            "date", "timestamp", "before_date", "after_date",
            "before_period_start", "before_period_end",
            "after_period_start", "after_period_end",
        ]

        available_date_fields = [
            field for field in date_fields if field in raw.columns
        ]

        checks = {
            "has_records": total > 0,
            "has_area_information": area_field is not None,
            "all_records_have_valid_area": (
                valid_area_count == total if total else False
            ),
            "all_source_geometries_valid": (
                valid_geometry_count == total if total else False
            ),
            "has_coordinate_reference_system": raw.crs is not None,
        }

        return {
            "quality_status": (
                "good" if all(checks.values()) else "needs_attention"
            ),
            "total_source_records": total,
            "valid_geometries": valid_geometry_count,
            "invalid_or_missing_geometries": invalid_geometry_count,
            "area_field_found": area_field,
            "records_with_valid_area": valid_area_count,
            "area_coverage_percent": area_coverage,
            "date_fields_found": available_date_fields,
            "source_coordinate_system": (
                raw.crs.to_string() if raw.crs else None
            ),
            "checks_passed": sum(checks.values()),
            "checks_total": len(checks),
            "checks": checks,
            "note": (
                "Geometry counts are measured from the original GeoJSON, "
                "before API loading removes invalid or empty geometries."
            ),
        }

    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to inspect detection quality: {error}"
        )
'''

source = source[:start] + quality_endpoint + source[end:]
path.write_text(source, encoding="utf-8")

print("Day 31 changes applied successfully.")
