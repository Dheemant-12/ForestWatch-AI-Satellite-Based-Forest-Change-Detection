# ForestWatch AI 🌳

**Satellite-Based Forest Change Monitoring for Telangana, India**

ForestWatch AI is a geospatial application designed to identify potential vegetation loss by comparing satellite observations across different time periods.

## Project Objectives

- Retrieve Sentinel-2 surface-reflectance imagery.
- Filter observations by region, date, and image quality.
- Calculate NDVI composites and identify significant vegetation changes.
- Convert candidate change regions into geospatial features.
- Visualize historical changes using an interactive web map.
- Provide a documented REST API for analysis and results.

## Technology Stack

- Python 3.11
- Google Earth Engine and Sentinel-2
- FastAPI
- GeoPandas, Rasterio, NumPy, and Pandas
- PostgreSQL with PostGIS
- React, Vite, TypeScript, and Leaflet
- Pytest and Docker Compose

## Study Region

Initial scope: Telangana, India.

The first prototype will use a manageable study area within Telangana before expanding to user-defined regions.

## Detection Approach

NDVI is calculated as:

NDVI = (NIR - Red) / (NIR + Red)

For Sentinel-2, the initial implementation uses B8 (near-infrared) and B4 (red).

The difference between later and baseline observations is used to identify candidate vegetation-loss areas.

Detections are indicative only. Seasonal variation, cloud contamination, agriculture, fire, and other land-cover changes can produce false positives. The system does not independently determine whether an activity is illegal.

## Satellite Data Source

Google Earth Engine dataset:

`COPERNICUS/S2_SR_HARMONIZED`

Dataset documentation:
https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED

## Repository Structure

```text
ForestWatch-AI/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   └── main.py
│   ├── tests/
│   └── requirements.txt
├── frontend/
├── data/
│   ├── raw/
│   ├── processed/
│   └── exports/
├── docs/
├── scripts/
│   └── check_earth_engine.py
├── .env.example
├── .gitignore
└── README.md
```

## Local Setup

Create and activate a virtual environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
```

Configure Earth Engine authentication:

```powershell
earthengine authenticate
```

Set the Google Cloud project ID in your terminal:

```powershell
$env:EARTH_ENGINE_PROJECT = "your-google-cloud-project-id"
python scripts/check_earth_engine.py
```

Start the API from the repository root:

```powershell
uvicorn app.main:app --app-dir backend --reload
```

API documentation: http://127.0.0.1:8000/docs

Health check: http://127.0.0.1:8000/health

Run tests:

```powershell
$env:PYTHONPATH = "backend"
pytest backend/tests -v
```

## Development Roadmap

- Week 1: Satellite data pipeline and quality filtering.
- Week 2: NDVI change detection and validation.
- Week 3: FastAPI backend and React map interface.
- Week 4: Testing, deployment, and documentation.

## Limitations

- Cloud and cloud-shadow masking is essential.
- Seasonal comparisons must be handled carefully.
- A vegetation decline is not proof of deforestation or illegal encroachment.
- Findings require validation against independent evidence.

## Project Status

Day 1 — Repository foundation and environment setup.

## License and Data Attribution

Choose a project license before public distribution. Review the applicable Copernicus Sentinel data terms and Google Earth Engine usage terms before publishing data products or deploying the service.
