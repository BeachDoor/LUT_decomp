"""LUT3D data structure with trilinear and tetrahedral interpolation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from scipy.interpolate import RegularGridInterpolator

from .parser import CubeData, parse_cube


InterpolationMethod = Literal["trilinear", "tetrahedral"]


@dataclass
class LUT3D:
    """3D look-up table with grid interpolation.

    Data is stored as ndarray[r, g, b, channel] in [0..1] normalised space.
    """

    data: np.ndarray        # (N, N, N, 3), indexed [r, g, b, c]
    size: int
    domain_min: np.ndarray  # (3,)
    domain_max: np.ndarray  # (3,)

    # Cached trilinear interpolators (one per channel), built on first use
    _trilinear_interps: list[RegularGridInterpolator] | None = None

    @classmethod
    def from_cube(cls, path: str) -> LUT3D:
        cube = parse_cube(path)
        return cls.from_cube_data(cube)

    @classmethod
    def from_cube_data(cls, cube: CubeData) -> LUT3D:
        return cls(
            data=cube.data,
            size=cube.size,
            domain_min=cube.domain_min,
            domain_max=cube.domain_max,
        )

    def _build_trilinear(self) -> None:
        pts = np.linspace(0.0, 1.0, self.size)
        self._trilinear_interps = [
            RegularGridInterpolator(
                (pts, pts, pts),
                self.data[..., i],
                method="linear",
                bounds_error=False,
                fill_value=None,  # nearest extrapolation outside bounds
            )
            for i in range(3)
        ]

    def _normalize(self, rgb: np.ndarray) -> np.ndarray:
        """Map from [domain_min, domain_max] → [0, 1]."""
        span = self.domain_max - self.domain_min
        # Avoid division by zero on degenerate axes
        span = np.where(span == 0, 1.0, span)
        return np.asarray(np.clip((rgb - self.domain_min) / span, 0.0, 1.0))

    def apply(
        self,
        rgb: np.ndarray,
        method: InterpolationMethod = "trilinear",
    ) -> np.ndarray:
        """Apply the LUT to RGB values.

        Args:
            rgb: Array of shape (..., 3) with values in [domain_min, domain_max].
            method: Interpolation method.

        Returns:
            Array of same shape as *rgb* with LUT-mapped values.
        """
        orig_shape = rgb.shape
        norm = self._normalize(rgb).reshape(-1, 3)  # (M, 3)

        if method == "trilinear":
            result = self._apply_trilinear(norm)
        elif method == "tetrahedral":
            result = self._apply_tetrahedral(norm)
        else:
            raise ValueError(f"Unknown interpolation method: {method!r}")

        return result.reshape(orig_shape)

    def _apply_trilinear(self, norm: np.ndarray) -> np.ndarray:
        if self._trilinear_interps is None:
            self._build_trilinear()
        assert self._trilinear_interps is not None
        return np.stack([interp(norm) for interp in self._trilinear_interps], axis=-1)  # (M, 3)

    def _apply_tetrahedral(self, norm: np.ndarray) -> np.ndarray:
        """Sakamoto tetrahedral interpolation (6-tetrahedra decomposition)."""
        N = self.size
        g = norm * (N - 1)
        r_lo = np.floor(g[:, 0]).astype(int)
        g_lo = np.floor(g[:, 1]).astype(int)
        b_lo = np.floor(g[:, 2]).astype(int)

        r_hi = np.minimum(r_lo + 1, N - 1)
        g_hi = np.minimum(g_lo + 1, N - 1)
        b_hi = np.minimum(b_lo + 1, N - 1)

        tr = (g[:, 0] - r_lo)[:, np.newaxis]  # (M, 1)
        tg = (g[:, 1] - g_lo)[:, np.newaxis]
        tb = (g[:, 2] - b_lo)[:, np.newaxis]

        d = self.data
        c000 = d[r_lo, g_lo, b_lo]   # (M, 3)
        c100 = d[r_hi, g_lo, b_lo]
        c010 = d[r_lo, g_hi, b_lo]
        c110 = d[r_hi, g_hi, b_lo]
        c001 = d[r_lo, g_lo, b_hi]
        c101 = d[r_hi, g_lo, b_hi]
        c011 = d[r_lo, g_hi, b_hi]
        c111 = d[r_hi, g_hi, b_hi]

        tr_ = tr  # (M, 1) — broadcast-compatible with (M, 3)
        tg_ = tg
        tb_ = tb

        def cond(mask: np.ndarray) -> np.ndarray:
            return mask[:, np.newaxis]  # (M, 1) → broadcasts to (M, 3)

        # Six Sakamoto tetrahedra
        result = np.where(
            cond((tr_.ravel() >= tg_.ravel()) & (tg_.ravel() >= tb_.ravel())),
            (1 - tr_) * c000 + (tr_ - tg_) * c100 + (tg_ - tb_) * c110 + tb_ * c111,
            np.where(
                cond((tr_.ravel() >= tb_.ravel()) & (tb_.ravel() > tg_.ravel())),
                (1 - tr_) * c000 + (tr_ - tb_) * c100 + (tb_ - tg_) * c101 + tg_ * c111,
                np.where(
                    cond((tg_.ravel() > tr_.ravel()) & (tr_.ravel() >= tb_.ravel())),
                    (1 - tg_) * c000 + (tg_ - tr_) * c010 + (tr_ - tb_) * c110 + tb_ * c111,
                    np.where(
                        cond((tg_.ravel() >= tb_.ravel()) & (tb_.ravel() > tr_.ravel())),
                        (1 - tg_) * c000 + (tg_ - tb_) * c010 + (tb_ - tr_) * c011 + tr_ * c111,
                        np.where(
                            cond((tb_.ravel() > tr_.ravel()) & (tr_.ravel() > tg_.ravel())),
                            (1 - tb_) * c000 + (tb_ - tr_) * c001 + (tr_ - tg_) * c101 + tg_ * c111,
                            (1 - tb_) * c000 + (tb_ - tg_) * c001 + (tg_ - tr_) * c011 + tr_ * c111,
                        ),
                    ),
                ),
            ),
        )
        return np.asarray(result)  # (M, 3)

    def is_identity(self, tol: float = 1e-4) -> bool:
        """Return True if this LUT maps every input to itself."""
        N = self.size
        pts = np.linspace(0.0, 1.0, N)
        rr, gg, bb = np.meshgrid(pts, pts, pts, indexing="ij")
        expected = np.stack([rr, gg, bb], axis=-1)  # (N, N, N, 3)
        return bool(np.allclose(self.data, expected, atol=tol))
