"""Color space conversion utilities built on colour-science.

All feature computation uses CIELAB D65 as the working space.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, cast

import colour
import numpy as np

# D65 in CIE 1931 2° chromaticity coordinates
_D65: np.ndarray = cast(
    np.ndarray,
    colour.CCS_ILLUMINANTS["CIE 1931 2 Degree Standard Observer"]["D65"],
)


class InputColorSpace(Enum):
    SRGB = "sRGB"
    REC709 = "Rec.709"
    DAVINCI_WIDE_GAMUT_INTERMEDIATE = "DaVinci Wide Gamut Intermediate"
    ACESCCT = "ACEScct"


def _get_cs(cs: InputColorSpace) -> Any:
    """Return the colour-science RGB colourspace object."""
    _MAP = {
        InputColorSpace.SRGB: "sRGB",
        InputColorSpace.REC709: "ITU-R BT.709",
    }
    name = _MAP.get(cs)
    if name is not None:
        return colour.RGB_COLOURSPACES[name]
    raise NotImplementedError(
        f"Colorspace {cs.value!r} is not yet implemented. "
        "Supported: sRGB, Rec.709."
    )


def _decode_gamma(rgb: np.ndarray, cs: InputColorSpace) -> np.ndarray:
    """Decode gamma-encoded RGB to scene-linear."""
    if cs == InputColorSpace.ACESCCT:
        return cast(np.ndarray, colour.models.log_decoding_ACEScct(rgb))
    if cs == InputColorSpace.DAVINCI_WIDE_GAMUT_INTERMEDIATE:
        try:
            return cast(np.ndarray, colour.models.log_decoding_DaVinci_Intermediate(rgb))  # type: ignore[attr-defined]
        except AttributeError:
            raise NotImplementedError(
                "colour-science version does not expose "
                "log_decoding_DaVinci_Intermediate. Upgrade to >= 0.4.3."
            )
    return cast(np.ndarray, _get_cs(cs).cctf_decoding(rgb))


def _encode_gamma(rgb_linear: np.ndarray, cs: InputColorSpace) -> np.ndarray:
    """Encode scene-linear RGB to gamma."""
    if cs == InputColorSpace.ACESCCT:
        return cast(np.ndarray, colour.models.log_encoding_ACEScct(rgb_linear))
    if cs == InputColorSpace.DAVINCI_WIDE_GAMUT_INTERMEDIATE:
        try:
            return cast(np.ndarray, colour.models.log_encoding_DaVinci_Intermediate(rgb_linear))  # type: ignore[attr-defined]
        except AttributeError:
            raise NotImplementedError(
                "colour-science version does not expose "
                "log_encoding_DaVinci_Intermediate."
            )
    return cast(np.ndarray, _get_cs(cs).cctf_encoding(rgb_linear))


def _linear_to_xyz(rgb_linear: np.ndarray, cs: InputColorSpace) -> np.ndarray:
    """Convert scene-linear RGB to XYZ D65."""
    if cs in (InputColorSpace.ACESCCT,):
        ap1 = colour.RGB_COLOURSPACES["ACEScg"]
        return cast(np.ndarray, rgb_linear @ ap1.matrix_RGB_to_XYZ.T)
    return cast(np.ndarray, rgb_linear @ _get_cs(cs).matrix_RGB_to_XYZ.T)


def _xyz_to_linear(xyz: np.ndarray, cs: InputColorSpace) -> np.ndarray:
    """Convert XYZ D65 to scene-linear RGB."""
    if cs in (InputColorSpace.ACESCCT,):
        ap1 = colour.RGB_COLOURSPACES["ACEScg"]
        return cast(np.ndarray, xyz @ ap1.matrix_XYZ_to_RGB.T)
    return cast(np.ndarray, xyz @ _get_cs(cs).matrix_XYZ_to_RGB.T)


# ── Public API ──────────────────────────────────────────────────────────────

def rgb_to_lab(rgb: np.ndarray, cs: InputColorSpace) -> np.ndarray:
    """Gamma-encoded RGB → CIELAB D65.

    Args:
        rgb: (..., 3) array in the given colorspace's encoding range [0, 1].
        cs:  Source colorspace.

    Returns:
        (..., 3) Lab array.
    """
    rgb_linear = _decode_gamma(rgb, cs)
    xyz = _linear_to_xyz(rgb_linear, cs)
    return cast(np.ndarray, colour.XYZ_to_Lab(xyz, illuminant=_D65))


def lab_to_rgb(lab: np.ndarray, cs: InputColorSpace) -> np.ndarray:
    """CIELAB D65 → gamma-encoded RGB.

    Out-of-gamut linear values are clipped to [0, 1] before gamma encoding.
    """
    xyz = cast(np.ndarray, colour.Lab_to_XYZ(lab, illuminant=_D65))
    rgb_linear = _xyz_to_linear(xyz, cs)
    return _encode_gamma(np.clip(rgb_linear, 0.0, 1.0), cs)


def rgb_to_xyz(rgb: np.ndarray, cs: InputColorSpace) -> np.ndarray:
    """Gamma-encoded RGB → XYZ D65."""
    return _linear_to_xyz(_decode_gamma(rgb, cs), cs)


def lab_to_lch(lab: np.ndarray) -> np.ndarray:
    """CIELAB → LCHab. h is in degrees [0, 360)."""
    return cast(np.ndarray, colour.Lab_to_LCHab(lab))  # type: ignore[attr-defined]


def lch_to_lab(lch: np.ndarray) -> np.ndarray:
    """LCHab → CIELAB."""
    return cast(np.ndarray, colour.LCHab_to_Lab(lch))  # type: ignore[attr-defined]


def lch_to_rgb(lch: np.ndarray, cs: InputColorSpace) -> np.ndarray:
    """LCHab → gamma-encoded RGB (may be out of gamut)."""
    return lab_to_rgb(lch_to_lab(lch), cs)


def neutral_gray_rgb(
    l_star: float, cs: InputColorSpace = InputColorSpace.SRGB
) -> np.ndarray:
    """Return the gamma-encoded RGB of a neutral gray at the given L* value.

    Neutral: a*=0, b*=0.
    """
    lab = np.array([l_star, 0.0, 0.0])
    return lab_to_rgb(lab, cs)


def hue_angle_delta(h_out: np.ndarray, h_in: np.ndarray) -> np.ndarray:
    """Signed circular difference h_out - h_in, wrapped to (-180, 180]."""
    diff = h_out - h_in
    return cast(np.ndarray, (diff + 180.0) % 360.0 - 180.0)
