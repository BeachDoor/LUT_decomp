"""Category 3 – Global colour tone (4 dimensions).

  global_temperature_shift : shift along the Planckian locus (ΔT in kK)
  global_tint_shift         : perpendicular shift (Δv in CIE 1960 UCS)
  overall_chroma_multiplier : mean C*_out / C*_in across all sampled colours
  overall_contrast          : ratio of output vs input L* range on neutral axis
"""

from __future__ import annotations

import numpy as np

try:
    import colour
    _HAS_COLOUR = True
except ImportError:
    _HAS_COLOUR = False

from ..colorspace import (
    InputColorSpace,
    lab_to_lch,
    neutral_gray_rgb,
    rgb_to_lab,
    rgb_to_xyz,
)
from ..lut import LUT3D, InterpolationMethod
from .base import FeatureExtractor
from .hue_bands import HUE_BAND_CENTERS, _make_samples

# Sample L* levels for neutral-axis analysis
_NEUTRAL_L_STARS = np.linspace(10.0, 90.0, 17)

# D65 white point in CIE 1931 xy
_D65_xy = np.array([0.3127, 0.3290])

# CCT range for locus search (Kelvin)
_CCT_RANGE = np.linspace(1667.0, 25000.0, 500)


def _xy_to_uv_1960(xy: np.ndarray) -> np.ndarray:
    """CIE 1931 xy → CIE 1960 UCS (u, v)."""
    x, y = xy[..., 0], xy[..., 1]
    denom = -2 * x + 12 * y + 3
    u = 4 * x / denom
    v = 6 * y / denom
    return np.stack([u, v], axis=-1)


def _planckian_uv(T: float) -> np.ndarray:
    """Planckian locus in CIE 1960 UCS for a given CCT T (Kelvin)."""
    # Approximation valid for 1667–25000 K (Kang et al. 2002)
    if T < 4000:
        u = (0.179910 + 0.8776956e-3 * T - 0.2343589e-6 * T**2 + 0.9347633e-10 * T**3)
    else:
        u = (0.182240 + 0.1558992e-3 * T + 0.5298800e-7 * T**2)
    if T < 2222:
        v = (-0.9549476 + 3.081758e-3 * T - 5.084188e-7 * T**2 + 2.890174e-11 * T**3)
    elif T < 4000:
        v = (2.0813013 + 0.2191806e-4 * T - 0.2120674e-6 * T**2 + 2.163219e-10 * T**3)
    else:
        v = (-1.745674 + 3.744462e-3 * T - 3.901530e-7 * T**2 + 1.016977e-10 * T**3)
    return np.array([u, v])


_LOCUS_UVS: np.ndarray = np.array([_planckian_uv(T) for T in _CCT_RANGE])


def _decompose_uv_shift(
    uv_in: np.ndarray, uv_out: np.ndarray
) -> tuple[float, float]:
    """Decompose Δuv into (along-locus temperature, perpendicular tint) components.

    Returns:
        temp_shift : positive = warmer (lower CCT direction)
        tint_shift : positive = magenta, negative = green
    """
    # Find nearest locus point to uv_in
    dists = np.linalg.norm(_LOCUS_UVS - uv_in, axis=1)
    idx = int(np.argmin(dists))

    # Tangent direction at that locus point
    idx_lo = max(0, idx - 1)
    idx_hi = min(len(_CCT_RANGE) - 1, idx + 1)
    tangent = _LOCUS_UVS[idx_hi] - _LOCUS_UVS[idx_lo]
    norm = np.linalg.norm(tangent)
    if norm < 1e-10:
        return 0.0, 0.0
    tangent = tangent / norm

    delta = uv_out - uv_in
    # Along-locus component (temperature direction; CCT decreases as u increases)
    along = float(np.dot(delta, tangent))
    # Perpendicular component (tint)
    perp = float(tangent[0] * delta[1] - tangent[1] * delta[0])

    return along, perp


def _global_temperature_tint(
    lut: LUT3D, cs: InputColorSpace, interp: InterpolationMethod
) -> tuple[float, float]:
    """Compute mean along-locus and perpendicular shifts on the neutral axis."""
    along_list: list[float] = []
    perp_list: list[float] = []

    for l_star in _NEUTRAL_L_STARS:
        rgb_in = neutral_gray_rgb(l_star, cs)
        xyz_in = rgb_to_xyz(rgb_in[np.newaxis], cs)[0]

        rgb_out = lut.apply(rgb_in[np.newaxis], method=interp)[0]
        xyz_out = rgb_to_xyz(np.clip(rgb_out[np.newaxis], 0, 1), cs)[0]

        # Skip degenerate (black or near-black) patches
        if xyz_in[1] < 1e-4 or xyz_out[1] < 1e-4:
            continue

        xy_in = xyz_in[:2] / (xyz_in.sum() + 1e-12)
        xy_out = xyz_out[:2] / (xyz_out.sum() + 1e-12)

        uv_in = _xy_to_uv_1960(xy_in)
        uv_out = _xy_to_uv_1960(xy_out)

        al, pe = _decompose_uv_shift(uv_in, uv_out)
        along_list.append(al)
        perp_list.append(pe)

    if not along_list:
        return 0.0, 0.0
    return float(np.mean(along_list)), float(np.mean(perp_list))


def _overall_chroma_multiplier(
    lut: LUT3D, cs: InputColorSpace, interp: InterpolationMethod
) -> float:
    """Mean C*_out / C*_in across representative saturated colours."""
    ratios: list[float] = []
    for band, cfg in HUE_BAND_CENTERS.items():
        try:
            rgb_in, lab_in = _make_samples(cfg["L"], cfg["C"], cfg["h"], cs)
        except ValueError:
            continue
        rgb_out = lut.apply(rgb_in, method=interp)
        lab_out = rgb_to_lab(rgb_out, cs)

        c_in = lab_to_lch(lab_in)[:, 1]
        c_out = lab_to_lch(lab_out)[:, 1]
        valid = c_in > 1.0
        if valid.any():
            ratios.extend((c_out[valid] / c_in[valid]).tolist())

    return float(np.mean(ratios)) if ratios else 1.0


def _overall_contrast(
    lut: LUT3D, cs: InputColorSpace, interp: InterpolationMethod
) -> float:
    """Ratio of output to input L* range on the neutral axis."""
    l_in_vals: list[float] = []
    l_out_vals: list[float] = []

    for l_star in _NEUTRAL_L_STARS:
        rgb_in = neutral_gray_rgb(l_star, cs)
        rgb_out = lut.apply(rgb_in[np.newaxis], method=interp)[0]
        lab_out = rgb_to_lab(np.clip(rgb_out[np.newaxis], 0, 1), cs)[0]
        l_in_vals.append(l_star)
        l_out_vals.append(float(lab_out[0]))

    if not l_in_vals:
        return 1.0

    l_in_range = max(l_in_vals) - min(l_in_vals)
    l_out_range = max(l_out_vals) - min(l_out_vals)

    if l_in_range < 1e-6:
        return 1.0
    return l_out_range / l_in_range


class GlobalToneExtractor(FeatureExtractor):
    """4-dimensional global colour-tone features."""

    @property
    def feature_names(self) -> list[str]:
        return [
            "global_temperature_shift",
            "global_tint_shift",
            "overall_chroma_multiplier",
            "overall_contrast",
        ]

    @property
    def category_name(self) -> str:
        return "global_tone"

    def extract(
        self,
        lut: LUT3D,
        colorspace: InputColorSpace,
        interpolation: InterpolationMethod = "trilinear",
    ) -> np.ndarray:
        temp, tint = _global_temperature_tint(lut, colorspace, interpolation)
        chroma = _overall_chroma_multiplier(lut, colorspace, interpolation)
        contrast = _overall_contrast(lut, colorspace, interpolation)
        return np.array([temp, tint, chroma, contrast], dtype=np.float64)
