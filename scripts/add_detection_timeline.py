from pathlib import Path

path = Path("backend/app/main.py")
raw = path.read_bytes()

try:
    source = raw.decode("utf-8-sig")
except UnicodeDecodeError:
    source = raw.decode("cp1252")

marker = '@app.get("/api/v1/detections/{detection_id}")'

if "/api/v1/detections/timeline" in source:
    print("Timeline endpoint already exists. No changes made.")
    raise SystemExit(0)

if marker not in source:
    print("Could not find the detection detail route. No changes made.")
    raise SystemExit(1)

endpoint = '''
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


'''

path.write_text(
    source.replace(marker, endpoint + marker, 1),
    encoding="utf-8"
)

print("SUCCESS: Detection timeline endpoint added.")
