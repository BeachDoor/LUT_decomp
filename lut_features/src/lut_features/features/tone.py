"""Category 2 – Tone behaviour (9 dimensions).

Measures ΔL*, Δa*, Δb* on the neutral (achromatic) axis at three luminance
levels that correspond to perceptual shadow, midtone, and highlight zones.
"""

from __future__ import annotations

import numpy as np

from ..colorspace import InputColorSpace, neutral_gray_rgb, rgb_to_lab
from ..lut import LUT3D, InterpolationMethod
from .base import FeatureExtractor

# Target L* values for the three zones
_TONE_ZONES = {
    "shadow":    20.0,
    "midtone":   50.0,
    "highlight": 80.0,
}


class ToneExtractor(FeatureExtractor):
    """9-dimensional tone-behaviour features."""

    @property
    def feature_names(self) -> list[str]:
        names: list[str] = []
        for zone in _TONE_ZONES:
            names += [
                f"tone_{zone}_L_change",
                f"tone_{zone}_a_change",
                f"tone_{zone}_b_change",
            ]
        return names

    @property
    def category_name(self) -> str:
        return "tone"

    def extract(
        self,
        lut: LUT3D,
        colorspace: InputColorSpace,
        interpolation: InterpolationMethod = "trilinear",
    ) -> np.ndarray:
        values: list[float] = []
        for l_star in _TONE_ZONES.values():
            rgb_in = neutral_gray_rgb(l_star, colorspace)  # (3,)
            lab_in = np.array([l_star, 0.0, 0.0])

            rgb_out = lut.apply(rgb_in[np.newaxis], method=interpolation)[0]
            lab_out = rgb_to_lab(rgb_out[np.newaxis], colorspace)[0]

            dL = float(lab_out[0] - lab_in[0])
            da = float(lab_out[1] - lab_in[1])
            db = float(lab_out[2] - lab_in[2])
            values += [dL, da, db]

        return np.array(values, dtype=np.float64)
