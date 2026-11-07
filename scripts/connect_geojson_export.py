from pathlib import Path
import re

path = Path("frontend/src/App.jsx")
raw = path.read_bytes()

try:
    source = raw.decode("utf-8-sig")
except UnicodeDecodeError:
    source = raw.decode("cp1252")

if "import GeoJSONExport from" not in source:
    analytics_import = re.search(
        r'^import\s+AnalyticsDashboard\s+from\s+["\']\./components/AnalyticsDashboard["\'];?\s*$',
        source,
        flags=re.MULTILINE
    )

    if not analytics_import:
        raise SystemExit(
            "Could not find AnalyticsDashboard import. "
            "App.jsx was not modified."
        )

    source = (
        source[:analytics_import.end()]
        + '\nimport GeoJSONExport from "./components/GeoJSONExport";'
        + source[analytics_import.end():]
    )

if "<GeoJSONExport" not in source:
    map_match = re.search(
        r'^(\s*)<MapContainer\b',
        source,
        flags=re.MULTILINE
    )

    if not map_match:
        raise SystemExit(
            "Could not find MapContainer. "
            "Check App.jsx before proceeding."
        )

    indent = map_match.group(1)

    source = (
        source[:map_match.start()]
        + indent + "<GeoJSONExport />\n"
        + source[map_match.start():]
    )

path.write_text(source, encoding="utf-8")

print("SUCCESS: App.jsx updated and saved as UTF-8.")
