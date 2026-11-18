from pathlib import Path

path = Path("backend/app/main.py")
source = path.read_text(encoding="utf-8")

start_marker = '@app.get("/api/v1/detections/{detection_id}")'
end_marker = "# FILTER DETECTIONS BY MINIMUM AREA"

start = source.find(start_marker)
end = source.find(end_marker, start)

if start == -1 or end == -1:
    raise SystemExit(
        "Could not find the individual detection route. "
        "No changes were made."
    )

route_block = source[start:end].strip()

# Remove the dynamic route from its current position.
source = source[:start] + source[end:]

# Register it after all static detection routes.
source = source.rstrip() + "\n\n\n# --------------------------------------------------\n"
source += "# GET INDIVIDUAL DETECTION — KEEP AFTER STATIC ROUTES\n"
source += "# --------------------------------------------------\n\n"
source += route_block + "\n"

path.write_text(source, encoding="utf-8")

print("Day 33: Individual detection route moved to the end.")
