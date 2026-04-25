#!/usr/bin/env python3
"""Extract and display feature vector for a single .cube LUT file.

Usage:
    uv run python examples/extract_single.py path/to/look.cube
    uv run python examples/extract_single.py path/to/look.cube --colorspace Rec.709
    uv run python examples/extract_single.py path/to/look.cube --method tetrahedral
"""

from __future__ import annotations

import argparse
import sys

import numpy as np

from lut_features import InputColorSpace, LUTFeatureExtractor


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract features from a .cube LUT file.")
    parser.add_argument("lut", help="Path to .cube LUT file")
    parser.add_argument(
        "--colorspace",
        choices=[cs.value for cs in InputColorSpace],
        default=InputColorSpace.SRGB.value,
        help="Input colorspace of the LUT (default: sRGB)",
    )
    parser.add_argument(
        "--method",
        choices=["trilinear", "tetrahedral"],
        default="trilinear",
        help="Interpolation method (default: trilinear)",
    )
    parser.add_argument(
        "--json",
        metavar="OUTPUT",
        help="Save feature vector to a JSON file",
    )
    args = parser.parse_args()

    cs = InputColorSpace(args.colorspace)
    extractor = LUTFeatureExtractor(input_colorspace=cs, interpolation=args.method)

    print(f"Processing: {args.lut}")
    features = extractor.extract(args.lut)

    print(f"\nFeature vector shape: {features.vector.shape}")
    print(f"LUT size: {features.metadata['lut_size']}³")
    print(f"Colorspace: {features.metadata['colorspace']}")
    print(f"Interpolation: {features.metadata['interpolation']}")

    # Print by category
    prev_cat = None
    for i, (name, cat, val) in enumerate(
        zip(features.feature_names, features.feature_categories, features.vector)
    ):
        if cat != prev_cat:
            print(f"\n── {cat} ──")
            prev_cat = cat
        print(f"  {name:<45s}  {val:+.4f}")

    if args.json:
        LUTFeatureExtractor.save_json(features, args.json)
        print(f"\nSaved to {args.json}")


if __name__ == "__main__":
    main()
