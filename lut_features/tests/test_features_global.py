"""Tests for Category 3 – Global tone features."""

from __future__ import annotations

import numpy as np

from lut_features.colorspace import InputColorSpace
from lut_features.features.global_tone import GlobalToneExtractor
from lut_features.lut import LUT3D


def test_identity_chroma_multiplier_unity(identity_lut: LUT3D, default_cs: InputColorSpace):
    ext = GlobalToneExtractor()
    v = ext.extract(identity_lut, default_cs)
    # index 2: overall_chroma_multiplier
    np.testing.assert_allclose(v[2], 1.0, atol=0.1)


def test_identity_contrast_unity(identity_lut: LUT3D, default_cs: InputColorSpace):
    ext = GlobalToneExtractor()
    v = ext.extract(identity_lut, default_cs)
    # index 3: overall_contrast
    np.testing.assert_allclose(v[3], 1.0, atol=0.05)


def test_desaturate_chroma_below_one(desaturate_lut: LUT3D, default_cs: InputColorSpace):
    ext = GlobalToneExtractor()
    v = ext.extract(desaturate_lut, default_cs)
    assert v[2] < 1.0, f"Expected overall_chroma_multiplier < 1.0, got {v[2]:.3f}"


def test_feature_count(identity_lut: LUT3D, default_cs: InputColorSpace):
    ext = GlobalToneExtractor()
    v = ext.extract(identity_lut, default_cs)
    assert v.shape == (4,)
    assert len(ext.feature_names) == 4
