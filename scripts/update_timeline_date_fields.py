from pathlib import Path
import re

path = Path("backend/app/main.py")
raw = path.read_bytes()

try:
    source = raw.decode("utf-8-sig")
except UnicodeDecodeError:
    source = raw.decode("cp1252")

if "/api/v1/detections/timeline" not in source:
    raise SystemExit("Timeline endpoint not found. No changes made.")

if '"after_period_end"' in source:
    print("Timeline already recognizes after_period_end.")
    raise SystemExit(0)

pattern = r'(^[ \t]*"after_date",[ \t]*$)'
match = re.search(pattern, source, flags=re.MULTILINE)

if not match:
    raise SystemExit(
        'Could not find the "after_date" entry in the timeline date_fields list. '
        "No changes made."
    )

replacement = match.group(1) + '\n        "after_period_end",'
source = source[:match.start()] + replacement + source[match.end():]

path.write_text(source, encoding="utf-8")
print("SUCCESS: Timeline API now recognizes after_period_end.")
