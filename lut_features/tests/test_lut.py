"""Tests for LUT3D interpolation."""

from __future__ import annotations

import numpy as np
import pytest

from lut_features.lut import LUT3D


def test_identity_is_identity(identity_lut: LUT3D):
    assert identity_lut.is_identity()


def test_warm_not_identity(warm_lut: LUT3D):
    assert not warm_lut.is_identity()


def test_trilinear_identity_passthrough(identity_lut: LUT3D):
    """Identity LUT with trilinear should return the input unchanged."""
    rgb = np.random.default_rng(0).uniform(0, 1, (20, 3))
    out = identity_lut.apply(rgb, method="trilinear")
    np.testing.assert_allclose(out, rgb, atol=1e-3)


def test_tetrahedral_identity_passthrough(identity_lut: LUT3D):
    rgb = np.random.default_rng(1).uniform(0, 1, (20, 3))
    out = identity_lut.apply(rgb, method="tetrahedral")
    np.testing.assert_allclose(out, rgb, atol=1e-3)


def test_trilinear_vs_tetrahedral_close(warm_lut: LUT3D):
    """Trilinear and tetrahedral should give close results for a smooth LUT."""
    rgb = np.random.default_rng(2).uniform(0.05, 0.95, (50, 3))
    tri = warm_lut.apply(rgb, method="trilinear")
    tet = warm_lut.apply(rgb, method="tetrahedral")
    np.testing.assert_allclose(tri, tet, atol=0.02)


def test_apply_shape_broadcast(identity_lut: LUT3D):
    """apply() preserves leading dimensions."""
    rgb = np.random.default_rng(3).uniform(0, 1, (4, 5, 3))
    out = identity_lut.apply(rgb)
    assert out.shape == (4, 5, 3)


def test_apply_clips_out_of_domain(identity_lut: LUT3D):
    """Values outside domain are clamped before interpolation."""
    rgb_lo = np.array([[-0.5, -0.5, -0.5]])
    rgb_hi = np.array([[1.5, 1.5, 1.5]])
    # Should not raise
    out_lo = identity_lut.apply(rgb_lo)
    out_hi = identity_lut.apply(rgb_hi)
    # Identity maps clipped input → output in [0, 1]
    assert np.all(out_lo >= -0.01)
    assert np.all(out_hi <= 1.01)


def test_unknown_method_raises(identity_lut: LUT3D):
    with pytest.raises(ValueError, match="Unknown interpolation"):
        identity_lut.apply(np.zeros((1, 3)), method="bicubic")  # type: ignore[arg-type]
