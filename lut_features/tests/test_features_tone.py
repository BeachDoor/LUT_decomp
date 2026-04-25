"""Tests for Category 2 – Tone features."""

from __future__ import annotations

import numpy as np

from lut_features.colorspace import InputColorSpace
from lut_features.features.tone import ToneExtractor
from lut_features.lut import LUT3D


def test_identity_all_zero(identity_lut: LUT3D, default_cs: InputColorSpace):
    ext = ToneExtractor()
    v = ext.extract(identity_lut, default_cs)
    np.testing.assert_allclose(v, 0.0, atol=0.5)


def test_feature_count(identity_lut: LUT3D, default_cs: InputColorSpace):
    ext = ToneExtractor()
    v = ext.extract(identity_lut, default_cs)
    assert v.shape == (9,)
    assert len(ext.feature_names) == 9


def test_split_toning_shadow_b_negative(split_toning_lut: LUT3D, default_cs: InputColorSpace):
    """Blue shadows should yield negative Δb* in the shadow zone."""
    ext = ToneExtractor()
    v = ext.extract(split_toning_lut, default_cs)
    # tone_shadow_b_change is at index 2 (L, a, b for shadow)
    shadow_b = v[2]
    assert shadow_b < 0, f"Expected shadow Δb* < 0, got {shadow_b:.3f}"


def test_split_toning_highlight_b_positive(split_toning_lut: LUT3D, default_cs: InputColorSpace):
    """Yellow highlights should yield positive Δb* in the highlight zone."""
    ext = ToneExtractor()
    v = ext.extract(split_toning_lut, default_cs)
    # tone_highlight_b_change is at index 8 (3+3+2)
    highlight_b = v[8]
    assert highlight_b > 0, f"Expected highlight Δb* > 0, got {highlight_b:.3f}"


def test_warm_shift_midtone_b_positive(warm_lut: LUT3D, default_cs: InputColorSpace):
    """Warm shift should increase b* (yellow direction) on neutral midtones."""
    ext = ToneExtractor()
    v = ext.extract(warm_lut, default_cs)
    midtone_b = v[5]  # shadow: 0,1,2  midtone: 3,4,5
    assert midtone_b > 0, f"Expected midtone Δb* > 0 for warm LUT, got {midtone_b:.3f}"
