from pathlib import Path
import re

path = Path("frontend/src/App.jsx")
raw = path.read_bytes()

try:
    source = raw.decode("utf-8-sig")
except UnicodeDecodeError:
    source = raw.decode("cp1252")

if "import DetectionTimeline from" not in source:
    analytics_import = re.search(
        r'^import\s+AnalyticsDashboard\s+from\s+["\']\./components/AnalyticsDashboard["\'];?\s*$',
        source,
        flags=re.MULTILINE
    )

    if not analytics_import:
        raise SystemExit(
            "AnalyticsDashboard import not found. App.jsx was not changed."
        )

    source = (
        source[:analytics_import.end()]
        + '\nimport DetectionTimeline from "./components/DetectionTimeline";'
        + source[analytics_import.end():]
    )

if "<DetectionTimeline />" not in source:
    map_match = re.search(
        r'^(\s*)<MapContainer\b',
        source,
        flags=re.MULTILINE
    )

    if not map_match:
        raise SystemExit(
            "MapContainer not found. App.jsx was not changed further."
        )

    indent = map_match.group(1)

    # Place timeline immediately before the map.
    source = (
        source[:map_match.start()]
        + indent + "<DetectionTimeline />\n"
        + source[map_match.start():]
    )

path.write_text(source, encoding="utf-8")
print("SUCCESS: DetectionTimeline connected to App.jsx.")
