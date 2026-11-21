import argparse
import csv
import statistics
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from backend.app.main import app

REPORT_DIR = BASE_DIR / "data" / "reports"

ENDPOINTS = [
    ("health", "/health"),
    ("detections", "/api/v1/detections"),
    ("summary", "/api/v1/detections/summary"),
    ("pagination", "/api/v1/detections/page?limit=100&offset=0"),
    ("quality", "/api/v1/detections/quality"),
    ("analytics", "/api/v1/analytics"),
]


def benchmark_endpoint(client, name, path, warmup, request_count):
    timings = []
    statuses = []

    for _ in range(warmup):
        client.get(path)

    for _ in range(request_count):
        start = time.perf_counter()
        response = client.get(path)
        elapsed = (time.perf_counter() - start) * 1000

        timings.append(elapsed)
        statuses.append(response.status_code)

    return {
        "endpoint": name,
        "path": path,
        "requests": request_count,
        "average_ms": round(statistics.mean(timings), 2),
        "median_ms": round(statistics.median(timings), 2),
        "minimum_ms": round(min(timings), 2),
        "maximum_ms": round(max(timings), 2),
        "successful_responses": sum(200 <= status < 300 for status in statuses),
        "failed_responses": sum(status >= 400 for status in statuses),
        "status_codes": ",".join(
            str(status) for status in sorted(set(statuses))
        ),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark ForestWatch AI API endpoints."
    )
    parser.add_argument("--requests", type=int, default=20)
    parser.add_argument("--warmup", type=int, default=3)
    args = parser.parse_args()

    if args.requests < 1 or args.warmup < 0:
        parser.error("Requests must be positive and warmup cannot be negative.")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / "api_performance.csv"

    registered_paths = {
        route.path for route in app.routes if hasattr(route, "path")
    }

    results = []

    with TestClient(app) as client:
        for name, path in ENDPOINTS:
            route_path = path.split("?")[0]

            if route_path not in registered_paths:
                print(f"SKIPPED: {name} - endpoint not registered")
                continue

            try:
                result = benchmark_endpoint(
                    client, name, path, args.warmup, args.requests
                )
                results.append(result)

                print(
                    f"{name:12} "
                    f"average={result['average_ms']:8.2f} ms | "
                    f"median={result['median_ms']:8.2f} ms | "
                    f"status={result['status_codes']}"
                )

            except Exception as exc:
                print(f"ERROR: {name}: {exc}")

    if not results:
        raise SystemExit("No endpoints were successfully benchmarked.")

    with report_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print(f"\nReport saved: {report_path}")


if __name__ == "__main__":
    main()
