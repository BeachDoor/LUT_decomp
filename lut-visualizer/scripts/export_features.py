"""
Export LUT feature vectors to features.json (visualizer schema v1.0).

Usage:
    cd lut_features
    uv run python ../lut-visualizer/scripts/export_features.py \\
        --luts path/to/lut1.cube path/to/lut2.cube ... \\
        --out ../lut-visualizer/public/data/features.json

Or pass a directory of .cube files:
    uv run python ../lut-visualizer/scripts/export_features.py \\
        --lut-dir path/to/luts/ \\
        --out ../lut-visualizer/public/data/features.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Allow running from lut_features/ directory
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lut_features" / "src"))

from lut_features import LUTFeatureExtractor, InputColorSpace

# ── Feature metadata: label, unit, neutral_value, typical_range ─────────────

_BANDS = ["R", "Y", "G", "C", "B", "M"]
_BAND_LABELS = {"R": "赤", "Y": "黄", "G": "緑", "C": "シアン", "B": "青", "M": "マゼンタ"}
_TONES = ["shadow", "midtone", "highlight"]
_TONE_LABELS = {"shadow": "シャドウ", "midtone": "ミッドトーン", "highlight": "ハイライト"}

FEATURE_METADATA: dict[str, dict[str, Any]] = {}

for b in _BANDS:
    bl = _BAND_LABELS[b]
    FEATURE_METADATA[f"hue_band_{b}_hue_shift"] = {
        "label": f"{bl} hueシフト", "unit": "度",
        "neutral_value": 0.0, "typical_range": [-30.0, 30.0],
    }
    FEATURE_METADATA[f"hue_band_{b}_chroma_change"] = {
        "label": f"{bl} 彩度変化", "unit": "比率",
        "neutral_value": 1.0, "typical_range": [0.5, 1.5],
    }
    FEATURE_METADATA[f"hue_band_{b}_lightness_change"] = {
        "label": f"{bl} 明度変化", "unit": "L*",
        "neutral_value": 0.0, "typical_range": [-20.0, 20.0],
    }

for t in _TONES:
    tl = _TONE_LABELS[t]
    FEATURE_METADATA[f"tone_{t}_L_change"] = {
        "label": f"{tl} ΔL*", "unit": "L*",
        "neutral_value": 0.0, "typical_range": [-15.0, 15.0],
    }
    FEATURE_METADATA[f"tone_{t}_a_change"] = {
        "label": f"{tl} Δa*", "unit": "a*",
        "neutral_value": 0.0, "typical_range": [-10.0, 10.0],
    }
    FEATURE_METADATA[f"tone_{t}_b_change"] = {
        "label": f"{tl} Δb*", "unit": "b*",
        "neutral_value": 0.0, "typical_range": [-10.0, 10.0],
    }

FEATURE_METADATA.update({
    "global_temperature_shift": {
        "label": "色温度シフト", "unit": "uv",
        "neutral_value": 0.0, "typical_range": [-0.015, 0.015],
    },
    "global_tint_shift": {
        "label": "ティントシフト", "unit": "uv",
        "neutral_value": 0.0, "typical_range": [-0.010, 0.010],
    },
    "overall_chroma_multiplier": {
        "label": "全体彩度倍率", "unit": "比率",
        "neutral_value": 1.0, "typical_range": [0.5, 1.5],
    },
    "overall_contrast": {
        "label": "全体コントラスト", "unit": "比率",
        "neutral_value": 1.0, "typical_range": [0.7, 1.3],
    },
})

for b in _BANDS:
    FEATURE_METADATA[f"lum_dep_hue_shift_{b}"] = {
        "label": f"{_BAND_LABELS[b]} 輝度依存hueシフト", "unit": "度",
        "neutral_value": 0.0, "typical_range": [-20.0, 20.0],
    }

FEATURE_METADATA.update({
    "tone_curve_nonlinearity": {
        "label": "トーンカーブ非線形度", "unit": "L*",
        "neutral_value": 0.0, "typical_range": [0.0, 10.0],
    },
    "hue_rotation_variance": {
        "label": "hue回転分散", "unit": "deg²",
        "neutral_value": 0.0, "typical_range": [0.0, 50.0],
    },
    "chroma_response_nonlinearity": {
        "label": "彩度応答非線形度", "unit": "C*",
        "neutral_value": 0.0, "typical_range": [0.0, 10.0],
    },
})

# ── Category definitions ─────────────────────────────────────────────────────

CATEGORIES = [
    {
        "id": "hue_bands",
        "label": "色相帯別挙動",
        "feature_ids": [f"hue_band_{b}_{m}" for b in _BANDS
                        for m in ["hue_shift", "chroma_change", "lightness_change"]],
    },
    {
        "id": "tone",
        "label": "トーン挙動",
        "feature_ids": [f"tone_{t}_{c}_change" for t in _TONES for c in ["L", "a", "b"]],
    },
    {
        "id": "global_tone",
        "label": "グローバル色調",
        "feature_ids": [
            "global_temperature_shift", "global_tint_shift",
            "overall_chroma_multiplier", "overall_contrast",
        ],
    },
    {
        "id": "luminance_dependent",
        "label": "輝度依存hueシフト",
        "feature_ids": [f"lum_dep_hue_shift_{b}" for b in _BANDS],
    },
    {
        "id": "nonlinearity",
        "label": "非線形性指標",
        "feature_ids": [
            "tone_curve_nonlinearity", "hue_rotation_variance",
            "chroma_response_nonlinearity",
        ],
    },
]


def _slug(path: Path) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", path.stem)


def export(
    cube_paths: list[Path],
    out_path: Path,
    colorspace: InputColorSpace = InputColorSpace.SRGB,
    thumbnail_dir: str = "thumbnails",
) -> None:
    extractor = LUTFeatureExtractor(input_colorspace=colorspace)

    features_list = []
    for idx, (name, fid) in enumerate(FEATURE_METADATA.items()):
        features_list.append({
            "id": name,
            "label": fid["label"],
            "unit": fid["unit"],
            "category": next(
                c["id"] for c in CATEGORIES if name in c["feature_ids"]
            ),
            "neutral_value": fid["neutral_value"],
            "typical_range": fid["typical_range"],
        })

    luts_out = []
    for path in cube_paths:
        lut_id = _slug(path)
        print(f"  processing {path.name} …", end=" ", flush=True)
        try:
            fv = extractor.extract(path)
        except Exception as exc:
            print(f"ERROR: {exc}")
            continue

        feature_dict = {
            name: float(fv.vector[fv.feature_names.index(name)])
            for name in FEATURE_METADATA
        }
        luts_out.append({
            "id": lut_id,
            "name": path.stem.replace("_", " "),
            "source_path": str(path),
            "features": feature_dict,
            "thumbnail_path": f"{thumbnail_dir}/{lut_id}.jpg",
        })
        print("OK")

    payload = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "feature_schema": {
            "categories": CATEGORIES,
            "features": features_list,
        },
        "luts": luts_out,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote {len(luts_out)} LUTs → {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export LUT features to features.json")
    parser.add_argument("--luts", nargs="*", default=[], metavar="FILE")
    parser.add_argument("--lut-dir", metavar="DIR")
    parser.add_argument("--out", required=True, metavar="OUTPUT.json")
    parser.add_argument(
        "--colorspace", default="sRGB",
        choices=[cs.value for cs in InputColorSpace],
    )
    args = parser.parse_args()

    paths: list[Path] = [Path(p) for p in args.luts]
    if args.lut_dir:
        paths += sorted(Path(args.lut_dir).glob("*.cube"))

    if not paths:
        parser.error("Provide --luts or --lut-dir")

    cs = InputColorSpace(args.colorspace)
    export(paths, Path(args.out), colorspace=cs)


if __name__ == "__main__":
    main()
