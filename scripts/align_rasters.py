
import argparse
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling


# --------------------------------------------------
# RASTER METADATA
# --------------------------------------------------

def inspect_raster(path):
    """Read important geospatial raster properties."""

    with rasterio.open(path) as src:
        return {
            "file": str(path),
            "crs": str(src.crs),
            "width": src.width,
            "height": src.height,
            "bands": src.count,
            "resolution": list(src.res),
            "bounds": list(src.bounds),
            "nodata": src.nodata,
            "transform": list(src.transform)[:6]
        }


# --------------------------------------------------
# RASTER VALIDATION
# --------------------------------------------------

def validate_raster(path):
    """Check whether a raster has usable geospatial metadata."""

    with rasterio.open(path) as src:

        if src.crs is None:
            raise ValueError(f"Missing CRS: {path}")

        if src.width <= 0 or src.height <= 0:
            raise ValueError(f"Invalid dimensions: {path}")

        if src.count <= 0:
            raise ValueError(f"No raster bands: {path}")

        if src.res[0] <= 0 or src.res[1] <= 0:
            raise ValueError(f"Invalid resolution: {path}")

        if not np.isfinite(src.transform).all():
            raise ValueError(f"Invalid affine transform: {path}")

    return True


# --------------------------------------------------
# GRID COMPARISON
# --------------------------------------------------

def compare_grids(source, reference):

    with rasterio.open(source) as src, \
            rasterio.open(reference) as ref:

        return {
            "same_crs": src.crs == ref.crs,
            "same_dimensions": (
                src.width == ref.width
                and src.height == ref.height
            ),
            "same_transform": (
                src.transform == ref.transform
            ),
            "same_grid": (
                src.crs == ref.crs
                and src.width == ref.width
                and src.height == ref.height
                and src.transform == ref.transform
            )
        }


# --------------------------------------------------
# RASTER ALIGNMENT
# --------------------------------------------------

def align_raster(
    source_path,
    reference_path,
    output_path,
    resampling_method="bilinear"
):

    validate_raster(source_path)
    validate_raster(reference_path)

    resampling_options = {
        "nearest": Resampling.nearest,
        "bilinear": Resampling.bilinear,
        "cubic": Resampling.cubic
    }

    if resampling_method not in resampling_options:
        raise ValueError("Unsupported resampling method.")

    resampling = resampling_options[resampling_method]

    with rasterio.open(source_path) as src, \
            rasterio.open(reference_path) as ref:

        profile = src.profile.copy()

        # Target grid comes from the reference raster.
        profile.update({
            "crs": ref.crs,
            "transform": ref.transform,
            "width": ref.width,
            "height": ref.height,
            "compress": "deflate"
        })

        output_path = Path(output_path)
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with rasterio.open(output_path, "w", **profile) as dst:

            for band in range(1, src.count + 1):

                reproject(
                    source=rasterio.band(src, band),
                    destination=rasterio.band(dst, band),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    src_nodata=src.nodata,
                    dst_transform=ref.transform,
                    dst_crs=ref.crs,
                    dst_nodata=src.nodata,
                    resampling=resampling,
                    init_dest_nodata=True
                )

            dst.update_tags(
                source_file=Path(source_path).name,
                reference_file=Path(reference_path).name,
                resampling=resampling_method
            )

    print(f"Aligned raster saved: {output_path}")


# --------------------------------------------------
# DIRECTORY PROCESSING
# --------------------------------------------------

def process_directory(
    input_dir,
    reference_path,
    output_dir,
    resampling_method
):

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    reference_path = Path(reference_path)

    if not input_dir.exists():
        raise FileNotFoundError(input_dir)

    if not reference_path.exists():
        raise FileNotFoundError(reference_path)

    raster_files = [
        path for path in input_dir.glob("*.tif")
        if path.resolve() != reference_path.resolve()
    ]

    if not raster_files:
        print("No input GeoTIFF files found.")
        return []

    reports = []

    for raster_path in raster_files:

        print(f"\nProcessing: {raster_path.name}")

        before = compare_grids(
            raster_path,
            reference_path
        )

        output_path = (
            output_dir / f"{raster_path.stem}_aligned.tif"
        )

        align_raster(
            raster_path,
            reference_path,
            output_path,
            resampling_method
        )

        after = compare_grids(
            output_path,
            reference_path
        )

        report = {
            "source": str(raster_path),
            "output": str(output_path),
            "before_alignment": before,
            "after_alignment": after,
            "success": after["same_grid"]
        }

        reports.append(report)

        print(f"Before: {before}")
        print(f"After: {after}")

        if not report["success"]:
            raise RuntimeError(
                f"Grid alignment failed: {raster_path}"
            )

    return reports


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    parser = argparse.ArgumentParser(
        description="ForestWatch AI Raster Alignment"
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Directory containing source GeoTIFF files"
    )

    parser.add_argument(
        "--reference",
        required=True,
        help="Reference GeoTIFF defining target grid"
    )

    parser.add_argument(
        "--output",
        default="data/processed/aligned",
        help="Output directory"
    )

    parser.add_argument(
        "--resampling",
        choices=["nearest", "bilinear", "cubic"],
        default="bilinear"
    )

    args = parser.parse_args()

    print("=" * 55)
    print("FORESTWATCH AI - RASTER ALIGNMENT")
    print("=" * 55)

    reference = Path(args.reference)

    print("\nReference raster metadata:")
    print(
        json.dumps(
            inspect_raster(reference),
            indent=4
        )
    )

    reports = process_directory(
        args.input,
        reference,
        args.output,
        args.resampling
    )

    report_path = (
        Path(args.output) / "alignment_report.json"
    )

    report_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    report_path.write_text(
        json.dumps(reports, indent=4),
        encoding="utf-8"
    )

    print("\nAlignment processing completed.")
    print(f"Report saved: {report_path}")


if __name__ == "__main__":
    main()
