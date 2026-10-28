
import os

import ee


def main() -> None:
    project_id = os.getenv("EARTH_ENGINE_PROJECT")

    if not project_id:
        raise RuntimeError(
            "Set EARTH_ENGINE_PROJECT in your environment "
            "or .env before running this script."
        )

    ee.Initialize(project=project_id)

    message = ee.String(
        "ForestWatch AI Earth Engine connection successful"
    )

    print(message.getInfo())


if __name__ == "__main__":
    main()
