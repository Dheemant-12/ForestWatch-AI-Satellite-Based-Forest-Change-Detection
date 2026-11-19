from pathlib import Path

path = Path("backend/app/main.py")
source = path.read_text(encoding="utf-8")

anchor = '@app.get("/api/v1/detections/{detection_id}")'

if anchor not in source:
    raise SystemExit(
        "Dynamic detection route not found. "
        "Check backend/app/main.py before applying this patch."
    )

if '@app.get("/api/v1/detections/page")' in source:
    raise SystemExit("Pagination endpoint already exists. No changes made.")

endpoint = '''@app.get("/api/v1/detections/page")
def get_paginated_detections(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    """Return detection records in pages."""

    try:
        gdf = load_detections()

        total = len(gdf)
        page = gdf.iloc[offset:offset + limit].copy()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_next": offset + len(page) < total,
            "records_returned": len(page),
            "data": json.loads(page.to_json(drop_id=True)),
        }

    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve paginated detections: {error}",
        )


'''

source = source.replace(anchor, endpoint + anchor, 1)
path.write_text(source, encoding="utf-8")

print("Day 36: Paginated detections endpoint added.")
