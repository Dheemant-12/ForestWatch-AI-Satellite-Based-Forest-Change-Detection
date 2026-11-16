from pathlib import Path

path = Path("backend/app/main.py")
source = path.read_text(encoding="utf-8-sig")

marker = '@app.get("/api/v1/analytics")'

if "def get_detection_quality():" in source:
    print("Detection quality endpoint already exists.")
    raise SystemExit(0)

if marker not in source:
    raise SystemExit("Could not find analytics endpoint. No changes made.")

endpoint = '''

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


'''

source = source.replace(marker, endpoint + marker, 1)
path.write_text(source, encoding="utf-8")

print("SUCCESS: Detection Data Quality API added.")
print("Endpoint: GET /api/v1/detections/quality")
