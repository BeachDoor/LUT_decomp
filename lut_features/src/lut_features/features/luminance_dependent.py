"""Category 4 – Luminance-dependent hue shift (6 dimensions).

For each hue band we compare the hue shift in a darkened version of the
band colour vs a lightened version.  A non-zero difference reveals the 3D
LUT behaviour that changes hue rotation depending on luminance
(e.g. "dark reds shift cool, bright reds shift warm").

Feature = highlight_hue_shift − shadow_hue_shift  (degrees)
"""

from __future__ import annotations

import numpy as np

from ..colorspace import (
    InputColorSpace,
    hue_angle_delta,
    lab_to_lch,
    lab_to_rgb,
    lch_to_lab,
    rgb_to_lab,
)
from ..lut import LUT3D, InterpolationMethod
from .base import FeatureExtractor
from .hue_bands import HUE_BAND_CENTERS, _CHROMA_MIN, _make_samples

# Lightness offsets for shadow and highlight variants
_L_OFFSET = 20.0
_L_MIN = 15.0
_L_MAX = 85.0


def _hue_shift_at_lightness(
    L: float,
    C: float,
    h: float,
    lut: LUT3D,
    cs: InputColorSpace,
    interp: InterpolationMethod,
) -> float:
    """Mean hue shift for samples at a specific lightness."""
    try:
        rgb_in, lab_in = _make_samples(L, C, h, cs)
    except ValueError:
        return 0.0

    lch_in = lab_to_lch(lab_in)
    valid = lch_in[:, 1] > _CHROMA_MIN
    if not valid.any():
        return 0.0

    rgb_out = lut.apply(rgb_in[valid], method=interp)
    lab_out = rgb_to_lab(rgb_out, cs)
    lch_out = lab_to_lch(lab_out)

    deltas = hue_angle_delta(lch_out[:, 2], lch_in[valid, 2])
    return float(np.mean(deltas))


class LuminanceDependentExtractor(FeatureExtractor):
    """6-dimensional luminance-dependent hue-shift features."""

    _BANDS = list(HUE_BAND_CENTERS.keys())

    @property
    def feature_names(self) -> list[str]:
        return [f"lum_dep_hue_shift_{b}" for b in self._BANDS]

    @property
    def category_name(self) -> str:
        return "luminance_dependent"

    def extract(
        self,
        lut: LUT3D,
        colorspace: InputColorSpace,
        interpolation: InterpolationMethod = "trilinear",
    ) -> np.ndarray:
        values: list[float] = []
        for band in self._BANDS:
            cfg = HUE_BAND_CENTERS[band]
            L_center = cfg["L"]
            C = cfg["C"]
            h = cfg["h"]

            L_shadow = float(np.clip(L_center - _L_OFFSET, _L_MIN, _L_MAX))
            L_highlight = float(np.clip(L_center + _L_OFFSET, _L_MIN, _L_MAX))

            hs_shadow = _hue_shift_at_lightness(L_shadow, C, h, lut, colorspace, interpolation)
            hs_highlight = _hue_shift_at_lightness(L_highlight, C, h, lut, colorspace, interpolation)

            values.append(hs_highlight - hs_shadow)

        return np.array(values, dtype=np.float64)
