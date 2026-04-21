#!/usr/bin/env python3
"""Batch-extract features from all .cube files in a directory.

Usage:
    uv run python examples/batch_extract.py /path/to/luts/
    uv run python examples/batch_extract.py /path/to/luts/ --out features.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from lut_features import InputColorSpace, LUTFeatureExtractor


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch-extract features from .cube LUTs.")
    parser.add_argument("directory", help="Directory containing .cube files")
    parser.add_argument(
        "--colorspace",
        choices=[cs.value for cs in InputColorSpace],
        default=InputColorSpace.SRGB.value,
    )
    parser.add_argument(
        "--method",
        choices=["trilinear", "tetrahedral"],
        default="trilinear",
    )
    parser.add_argument("--out", metavar="OUTPUT.json", help="Save matrix to JSON")
    args = parser.parse_args()

    lut_dir = Path(args.directory)
    cube_files = sorted(lut_dir.glob("*.cube"))
    if not cube_files:
        print(f"No .cube files found in {lut_dir}")
        return

    cs = InputColorSpace(args.colorspace)
    extractor = LUTFeatureExtractor(input_colorspace=cs, interpolation=args.method)

    print(f"Found {len(cube_files)} LUT(s) in {lut_dir}")
    results = []
    for path in cube_files:
        try:
            fv = extractor.extract(path)
            results.append(fv)
            print(f"  {path.name}: OK")
        except Exception as exc:
            print(f"  {path.name}: ERROR – {exc}")

    if not results:
        return

    matrix = np.stack([r.vector for r in results])
    print(f"\nFeature matrix shape: {matrix.shape}  (n_luts × n_features)")
    print(f"Feature names: {results[0].feature_names}")

    if args.out:
        payload = {
            "lut_paths": [str(p) for p in cube_files[: len(results)]],
            "feature_names": results[0].feature_names,
            "feature_categories": results[0].feature_categories,
            "matrix": matrix.tolist(),
        }
        Path(args.out).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Saved to {args.out}")


if __name__ == "__main__":
    main()
