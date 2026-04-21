"""Category 1 – Hue-band behaviour (18 dimensions).

For each of the 6 perceptual hue bands (R/Y/G/C/B/M) we sample several
colours around a CIELAB LCh centre and measure:
  - hue_shift       : mean circular Δh° after LUT
  - chroma_change   : mean ratio C*_out / C*_in   (1.0 = unchanged)
  - lightness_change: mean ΔL*                    (0.0 = unchanged)
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

# Perceptually-tuned band centres in LCh (L*, C*, h°)
HUE_BAND_CENTERS: dict[str, dict[str, float]] = {
    "R": {"L": 50.0, "C": 60.0, "h": 30.0},
    "Y": {"L": 80.0, "C": 60.0, "h": 90.0},
    "G": {"L": 60.0, "C": 60.0, "h": 140.0},
    "C": {"L": 70.0, "C": 40.0, "h": 200.0},
    "B": {"L": 40.0, "C": 50.0, "h": 280.0},
    "M": {"L": 50.0, "C": 50.0, "h": 330.0},
}

# Hue offsets sampled around each centre
_H_OFFSETS = np.array([-20.0, -10.0, 0.0, 10.0, 20.0])
_CHROMA_MIN = 5.0   # below this C* hue is undefined – skip sample


def _make_samples(
    L: float, C: float, h_center: float, cs: InputColorSpace
) -> tuple[np.ndarray, np.ndarray]:
    """Generate in-gamut sample colours around a hue-band centre.

    Returns:
        rgb_in:  (K, 3) gamma-encoded input colours
        lab_in:  (K, 3) corresponding CIELAB values
    """
    rgb_list: list[np.ndarray] = []
    lab_list: list[np.ndarray] = []

    for dh in _H_OFFSETS:
        h = (h_center + dh) % 360.0
        C_try = C
        in_gamut = False
        for _ in range(6):  # iteratively reduce chroma until in gamut
            lch = np.array([L, C_try, h])
            lab = lch_to_lab(lch)
            rgb = lab_to_rgb(lab, cs)
            if np.all(rgb >= 0.0) and np.all(rgb <= 1.0):
                # Store the round-trip Lab so lch_in exactly matches what the LUT sees
                lab_actual = rgb_to_lab(rgb[np.newaxis], cs)[0]
                rgb_list.append(rgb)
                lab_list.append(lab_actual)
                break
            C_try *= 0.8
        # If still out of gamut after reduction, skip this sample

    if not rgb_list:
        raise ValueError(
            f"No in-gamut samples found for band centre L={L} C={C} h={h_center}"
        )

    return np.array(rgb_list), np.array(lab_list)


def _band_features(
    band: str,
    cs: InputColorSpace,
    lut: LUT3D,
    interp: InterpolationMethod,
) -> tuple[float, float, float]:
    """Compute (hue_shift, chroma_change, lightness_change) for one band."""
    cfg = HUE_BAND_CENTERS[band]
    rgb_in, lab_in = _make_samples(cfg["L"], cfg["C"], cfg["h"], cs)

    rgb_out = lut.apply(rgb_in, method=interp)
    lab_out = rgb_to_lab(rgb_out, cs)

    lch_in = lab_to_lch(lab_in)
    lch_out = lab_to_lch(lab_out)

    c_in = lch_in[:, 1]
    c_out = lch_out[:, 1]

    # Ignore samples where input chroma is too low (hue undefined)
    valid = c_in > _CHROMA_MIN
    if not valid.any():
        return 0.0, 1.0, 0.0

    h_in = lch_in[valid, 2]
    h_out = lch_out[valid, 2]
    hue_shift = float(np.mean(hue_angle_delta(h_out, h_in)))

    chroma_change = float(np.mean(c_out[valid] / np.where(c_in[valid] > 0, c_in[valid], 1.0)))

    lightness_change = float(np.mean(lch_out[valid, 0] - lch_in[valid, 0]))

    return hue_shift, chroma_change, lightness_change


class HueBandsExtractor(FeatureExtractor):
    """18-dimensional hue-band behaviour features."""

    _BANDS = list(HUE_BAND_CENTERS.keys())  # R, Y, G, C, B, M

    @property
    def feature_names(self) -> list[str]:
        names: list[str] = []
        for band in self._BANDS:
            names += [
                f"hue_band_{band}_hue_shift",
                f"hue_band_{band}_chroma_change",
                f"hue_band_{band}_lightness_change",
            ]
        return names

    @property
    def category_name(self) -> str:
        return "hue_bands"

    def extract(
        self,
        lut: LUT3D,
        colorspace: InputColorSpace,
        interpolation: InterpolationMethod = "trilinear",
    ) -> np.ndarray:
        values: list[float] = []
        for band in self._BANDS:
            hs, cc, lc = _band_features(band, colorspace, lut, interpolation)
            values += [hs, cc, lc]
        return np.array(values, dtype=np.float64)
