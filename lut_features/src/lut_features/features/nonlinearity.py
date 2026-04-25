"""Category 5 – Non-linearity indicators (3 dimensions).

  tone_curve_nonlinearity    : RMSE of L*_out residual from a linear fit
  hue_rotation_variance      : variance of per-band hue shifts (deg²)
  chroma_response_nonlinearity: RMSE of C*_out residual from a linear fit
"""

from __future__ import annotations

import numpy as np

from ..colorspace import (
    InputColorSpace,
    hue_angle_delta,
    lab_to_lch,
    lch_to_lab,
    lab_to_rgb,
    neutral_gray_rgb,
    rgb_to_lab,
)
from ..lut import LUT3D, InterpolationMethod
from .base import FeatureExtractor
from .hue_bands import HUE_BAND_CENTERS, _CHROMA_MIN, _make_samples

_NEUTRAL_SAMPLES = 33   # number of neutral grays for tone-curve analysis
_CHROMA_SAMPLES = 9     # number of C* levels for chroma-response analysis


def _tone_curve_nonlinearity(
    lut: LUT3D, cs: InputColorSpace, interp: InterpolationMethod
) -> float:
    """RMSE of L*_out residuals vs a linear fit through (L*_in, L*_out) data."""
    l_in = np.linspace(5.0, 95.0, _NEUTRAL_SAMPLES)
    l_out: list[float] = []

    for l_star in l_in:
        rgb_in = neutral_gray_rgb(l_star, cs)
        rgb_out = lut.apply(rgb_in[np.newaxis], method=interp)[0]
        lab_out = rgb_to_lab(np.clip(rgb_out[np.newaxis], 0, 1), cs)[0]
        l_out.append(float(lab_out[0]))

    l_out_arr = np.array(l_out)
    # Linear regression L*_out ~ a * L*_in + b
    coeffs = np.polyfit(l_in, l_out_arr, 1)
    predicted = np.polyval(coeffs, l_in)
    rmse = float(np.sqrt(np.mean((l_out_arr - predicted) ** 2)))
    return rmse


def _hue_rotation_variance(
    lut: LUT3D, cs: InputColorSpace, interp: InterpolationMethod
) -> float:
    """Variance of per-band hue shifts across the 6 hue bands (deg²)."""
    shifts: list[float] = []
    for band, cfg in HUE_BAND_CENTERS.items():
        try:
            rgb_in, lab_in = _make_samples(cfg["L"], cfg["C"], cfg["h"], cs)
        except ValueError:
            shifts.append(0.0)
            continue

        lch_in = lab_to_lch(lab_in)
        valid = lch_in[:, 1] > _CHROMA_MIN
        if not valid.any():
            shifts.append(0.0)
            continue

        rgb_out = lut.apply(rgb_in[valid], method=interp)
        lab_out = rgb_to_lab(rgb_out, cs)
        lch_out = lab_to_lch(lab_out)

        deltas = hue_angle_delta(lch_out[:, 2], lch_in[valid, 2])
        shifts.append(float(np.mean(deltas)))

    return float(np.var(shifts)) if shifts else 0.0


def _chroma_response_nonlinearity(
    lut: LUT3D, cs: InputColorSpace, interp: InterpolationMethod
) -> float:
    """RMSE of C*_out residuals vs a linear fit on (C*_in, C*_out) data."""
    c_in_all: list[float] = []
    c_out_all: list[float] = []

    for band, cfg in HUE_BAND_CENTERS.items():
        L = cfg["L"]
        h = cfg["h"]
        max_C = cfg["C"]

        for c_frac in np.linspace(0.1, 1.0, _CHROMA_SAMPLES):
            C_try = max_C * c_frac
            lch = np.array([L, C_try, h])
            lab = lch_to_lab(lch)
            rgb = lab_to_rgb(lab, cs)
            if not (np.all(rgb >= 0) and np.all(rgb <= 1)):
                continue

            # Use round-trip C* as the actual input chroma
            lab_actual = rgb_to_lab(rgb[np.newaxis], cs)[0]
            c_actual = float(lab_to_lch(lab_actual[np.newaxis])[0, 1])

            rgb_out = lut.apply(rgb[np.newaxis], method=interp)[0]
            lab_out = rgb_to_lab(np.clip(rgb_out[np.newaxis], 0, 1), cs)[0]
            c_out = float(lab_to_lch(lab_out[np.newaxis])[0, 1])

            c_in_all.append(c_actual)
            c_out_all.append(c_out)

    if len(c_in_all) < 3:
        return 0.0

    c_in_arr = np.array(c_in_all)
    c_out_arr = np.array(c_out_all)
    coeffs = np.polyfit(c_in_arr, c_out_arr, 1)
    predicted = np.polyval(coeffs, c_in_arr)
    return float(np.sqrt(np.mean((c_out_arr - predicted) ** 2)))


class NonlinearityExtractor(FeatureExtractor):
    """3-dimensional non-linearity indicator features."""

    @property
    def feature_names(self) -> list[str]:
        return [
            "tone_curve_nonlinearity",
            "hue_rotation_variance",
            "chroma_response_nonlinearity",
        ]

    @property
    def category_name(self) -> str:
        return "nonlinearity"

    def extract(
        self,
        lut: LUT3D,
        colorspace: InputColorSpace,
        interpolation: InterpolationMethod = "trilinear",
    ) -> np.ndarray:
        tc = _tone_curve_nonlinearity(lut, colorspace, interpolation)
        hr = _hue_rotation_variance(lut, colorspace, interpolation)
        cr = _chroma_response_nonlinearity(lut, colorspace, interpolation)
        return np.array([tc, hr, cr], dtype=np.float64)
