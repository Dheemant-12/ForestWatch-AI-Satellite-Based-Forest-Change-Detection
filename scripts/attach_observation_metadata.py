from pathlib import Path
import argparse
import shutil
import geopandas as gpd

parser = argparse.ArgumentParser(
    description="Attach satellite analysis-period metadata to detection polygons."
)
parser.add_argument(
    "--input",
    default="data/processed/forest_loss/forest_loss_polygons.geojson"
)
parser.add_argument("--before-start", default="2024-01-01")
parser.add_argument("--before-end", default="2024-03-31")
parser.add_argument("--after-start", default="2025-01-01")
parser.add_argument("--after-end", default="2025-03-31")
args = parser.parse_args()

input_path = Path(args.input)

if not input_path.exists():
    raise SystemExit(
        f"GeoJSON not found: {input_path}\n"
        "Run the Day 9 polygon-filtering step first, or provide the correct --input path."
    )

# Validate date strings before changing the source file.
from datetime import date

for value in [
    args.before_start,
    args.before_end,
    args.after_start,
    args.after_end,
]:
    try:
        date.fromisoformat(value)
    except ValueError:
        raise SystemExit(f"Invalid date: {value}. Use YYYY-MM-DD.")

if args.before_start > args.before_end:
    raise SystemExit("Before-period start must not be after its end.")

if args.after_start > args.after_end:
    raise SystemExit("After-period start must not be after its end.")

backup_path = input_path.with_name(
    input_path.stem + ".before_metadata_backup" + input_path.suffix
)

if not backup_path.exists():
    shutil.copy2(input_path, backup_path)
    print(f"Backup created: {backup_path}")
else:
    print(f"Existing backup preserved: {backup_path}")

gdf = gpd.read_file(input_path)

if gdf.empty:
    print("The GeoJSON contains zero features. No metadata was added.")
    raise SystemExit(0)

gdf["before_period_start"] = args.before_start
gdf["before_period_end"] = args.before_end
gdf["after_period_start"] = args.after_start
gdf["after_period_end"] = args.after_end
gdf["analysis_method"] = "seasonal_composite_ndvi_change"
gdf["detection_status"] = "Potential vegetation loss"

gdf.to_file(input_path, driver="GeoJSON", index=False)

print(f"Updated {len(gdf)} detection features.")
print(f"Output: {input_path}")
print("Added fields:")
print("  before_period_start")
print("  before_period_end")
print("  after_period_start")
print("  after_period_end")
print("  analysis_method")
print("  detection_status")
