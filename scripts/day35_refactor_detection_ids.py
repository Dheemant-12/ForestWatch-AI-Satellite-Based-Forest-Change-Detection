from pathlib import Path

path = Path("backend/app/main.py")
source = path.read_text(encoding="utf-8")

start = source.find("def load_detections():")
end = source.find("# HEALTH CHECK", start)

if start == -1 or end == -1:
    raise SystemExit("Could not locate load_detections(). No changes made.")

replacement = '''def generate_detection_id(geometry):
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


'''

source = source[:start] + replacement + source[end:]

if "import hashlib" not in source:
    source = source.replace("import json", "import json\\nimport hashlib", 1)

path.write_text(source, encoding="utf-8")

print("Day 35: Detection ID helper moved to module level.")
