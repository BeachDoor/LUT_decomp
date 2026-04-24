"""
Apply each LUT to a reference image and save thumbnail JPEGs.

Supported input formats:
  - JPEG, PNG, TIFF, WebP … (Pillow)
  - RAW camera files: CR2, CR3, NEF, NRW, ARW, RAF, ORF, RW2, PEF, DNG,
    3FR, ERF, KDC, MEF, MOS, MRW, RWL, SRF, SR2, X3F … (rawpy / LibRaw)

Usage (from lut_features/ directory):
    uv run python ../lut-visualizer/scripts/generate_thumbnails.py \\
        --image path/to/reference.jpg \\
        --lut-dir ../lut-visualizer/public/data/sample_luts/ \\
        --out-dir ../lut-visualizer/public/thumbnails/

Options:
    --image       Reference image file (JPEG / PNG / RAW …)
    --luts        Individual .cube files (alternative to --lut-dir)
    --lut-dir     Directory of .cube files
    --out-dir     Output directory for thumbnail JPEGs (default: public/thumbnails/)
    --size        Long-edge pixel size of output thumbnail (default: 320)
    --quality     JPEG quality 1–95 (default: 85)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.interpolate import RegularGridInterpolator

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lut_features" / "src"))
from lut_features.parser import parse_cube

# RAW file extensions handled by rawpy/LibRaw
_RAW_SUFFIXES = {
    ".3fr", ".arw", ".cr2", ".cr3", ".crw", ".dcr", ".dng", ".erf",
    ".kdc", ".mef", ".mос", ".mrw", ".mos", ".nef", ".nrw", ".orf",
    ".pef", ".raf", ".raw", ".rwl", ".rw2", ".srf", ".sr2", ".x3f",
}


def load_image(path: Path) -> Image.Image:
    """Load any supported image (JPEG/PNG/TIFF/RAW …) and return an RGB PIL Image."""
    if path.suffix.lower() in _RAW_SUFFIXES:
        try:
            import rawpy  # type: ignore[import-untyped]
        except ImportError as e:
            raise RuntimeError(
                "rawpy is required for RAW files. Run: uv add rawpy"
            ) from e
        with rawpy.imread(str(path)) as raw:
            # postprocess returns uint8 RGB; use camera white balance
            rgb = raw.postprocess(
                use_camera_wb=True,
                output_bps=8,
                no_auto_bright=False,
            )
        return Image.fromarray(rgb)
    return Image.open(path).convert("RGB")


def apply_lut(img_array: np.ndarray, cube_path: Path) -> np.ndarray:
    """Apply a 3D LUT to an HxWx3 uint8 image array. Returns uint8 array."""
    cube = parse_cube(cube_path)
    n = cube.size
    vals = np.linspace(0.0, 1.0, n)
    rgi = RegularGridInterpolator(
        (vals, vals, vals),
        cube.data,
        method="linear",
        bounds_error=False,
        fill_value=None,
    )

    src = img_array.astype(np.float32) / 255.0   # (H, W, 3)
    pts = src.reshape(-1, 3)                       # (H*W, 3)
    out = rgi(pts)                                 # (H*W, 3)
    out = np.clip(out, 0.0, 1.0)
    return (out * 255.0).round().astype(np.uint8).reshape(src.shape)


def fit_thumbnail(img: Image.Image, long_edge: int) -> Image.Image:
    """Resize image so its long edge equals `long_edge`, preserving aspect ratio."""
    w, h = img.size
    if w >= h:
        new_w, new_h = long_edge, max(1, round(h * long_edge / w))
    else:
        new_w, new_h = max(1, round(w * long_edge / h)), long_edge
    return img.resize((new_w, new_h), Image.LANCZOS)


def slug(path: Path) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", path.stem)


def generate(
    image_path: Path,
    cube_paths: list[Path],
    out_dir: Path,
    long_edge: int = 320,
    quality: int = 85,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading: {image_path.name} … ", end="", flush=True)
    ref = load_image(image_path)
    ref_thumb = fit_thumbnail(ref, long_edge)
    ref_array = np.array(ref_thumb)
    print(f"{ref.size[0]}×{ref.size[1]} → {ref_thumb.size[0]}×{ref_thumb.size[1]}")
    print(f"Output dir: {out_dir}\n")

    for cube_path in cube_paths:
        name = slug(cube_path)
        out_path = out_dir / f"{name}.jpg"
        print(f"  {cube_path.name} … ", end="", flush=True)
        try:
            result = apply_lut(ref_array, cube_path)
            Image.fromarray(result).save(out_path, "JPEG", quality=quality)
            print(f"OK  → {out_path.name}")
        except Exception as e:
            print(f"ERROR: {e}")

    print(f"\nGenerated {len(list(out_dir.glob('*.jpg')))} thumbnails in {out_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate LUT preview thumbnails")
    parser.add_argument("--image", required=True, metavar="FILE",
                        help="Reference image (JPEG/PNG/RAW …)")
    parser.add_argument("--luts", nargs="*", default=[], metavar="FILE",
                        help="Individual .cube files")
    parser.add_argument("--lut-dir", metavar="DIR",
                        help="Directory of .cube files")
    parser.add_argument("--out-dir",
                        default=str(Path(__file__).parent.parent / "public" / "thumbnails"),
                        metavar="DIR", help="Output directory (default: public/thumbnails/)")
    parser.add_argument("--size", type=int, default=320, metavar="PX",
                        help="Long-edge pixel size (default: 320)")
    parser.add_argument("--quality", type=int, default=85, metavar="Q",
                        help="JPEG quality 1-95 (default: 85)")
    args = parser.parse_args()

    paths: list[Path] = [Path(p) for p in args.luts]
    if args.lut_dir:
        paths += sorted(Path(args.lut_dir).glob("*.cube"))
    if not paths:
        parser.error("Provide --luts or --lut-dir")

    generate(
        image_path=Path(args.image),
        cube_paths=paths,
        out_dir=Path(args.out_dir),
        long_edge=args.size,
        quality=args.quality,
    )


if __name__ == "__main__":
    main()
