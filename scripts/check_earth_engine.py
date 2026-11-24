import os
from pathlib import Path

import ee
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def main() -> None:
    project_id = os.getenv("EARTH_ENGINE_PROJECT", "").strip()

    placeholders = {
        "YOUR_GOOGLE_CLOUD_PROJECT_ID",
        "YOUR_PROJECT_ID",
        "your-project-id",
    }

    if not project_id or project_id in placeholders:
        raise RuntimeError(
            "A valid Earth Engine project ID is required. "
            "Set EARTH_ENGINE_PROJECT in your .env file."
        )

    try:
        ee.Initialize(project=project_id)

        message = ee.String(
            "ForestWatch AI Earth Engine connection successful"
        )

        print(message.getInfo())

    except Exception as exc:
        raise RuntimeError(
            f"Earth Engine connection failed for project '{project_id}'. "
            "Check that the project exists, Earth Engine API is enabled, "
            "and your Google account has access."
        ) from exc


if __name__ == "__main__":
    main()
