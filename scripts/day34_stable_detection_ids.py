from pathlib import Path

path = Path("backend/app/main.py")
source = path.read_text(encoding="utf-8")

if "import hashlib" not in source:
    source = source.replace(
        "import json",
        "import json\nimport hashlib",
        1
    )

old = '''    # Generate detection IDs.
    # These are temporary IDs based on row order.

    gdf = gdf.reset_index(drop=True)

    gdf["detection_id"] = [
        f"FW-{i + 1:04d}"
        for i in range(len(gdf))
    ]
'''

new = '''    # Generate deterministic detection IDs.
    # IDs remain stable when the source records are reordered.
    def generate_detection_id(row):
        geometry = row.geometry

        properties = {
            str(key): str(value)
            for key, value in row.items()
            if key != "geometry"
        }

        payload = (
            geometry.wkb_hex
            + json.dumps(
                properties,
                sort_keys=True,
                separators=(",", ":")
            )
        )

        digest = hashlib.sha256(
            payload.encode("utf-8")
        ).hexdigest()[:12].upper()

        return f"FW-{digest}"

    gdf["detection_id"] = gdf.apply(
        generate_detection_id,
        axis=1
    )
'''

if old not in source:
    raise SystemExit(
        "Could not find the original row-based ID block. "
        "No changes were made. Check your current main.py."
    )

source = source.replace(old, new, 1)
path.write_text(source, encoding="utf-8")

print("Day 34: Stable detection IDs implemented.")
