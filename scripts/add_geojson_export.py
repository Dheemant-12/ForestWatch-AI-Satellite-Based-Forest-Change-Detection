from pathlib import Path

main_file = Path("backend/app/main.py")
source = main_file.read_text(encoding="utf-8")

marker = '@app.get("/api/v1/detections/{detection_id}")'

if "/api/v1/detections/export/geojson" in source:
    print("GeoJSON export endpoint already exists. No changes made.")
    raise SystemExit(0)

if marker not in source:
    print("Could not find the detection detail route.")
    print("No changes made. Open backend/app/main.py and check its route names.")
    raise SystemExit(1)

endpoint = '''
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


'''

main_file.write_text(
    source.replace(marker, endpoint + marker, 1),
    encoding="utf-8"
)

print("GeoJSON export endpoint added successfully.")
