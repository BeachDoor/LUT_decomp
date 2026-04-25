"""Tests for Category 4 – Luminance-dependent hue shift."""

from __future__ import annotations

import numpy as np

from lut_features.colorspace import InputColorSpace
from lut_features.features.luminance_dependent import LuminanceDependentExtractor
from lut_features.lut import LUT3D


def test_identity_all_near_zero(identity_lut: LUT3D, default_cs: InputColorSpace):
    ext = LuminanceDependentExtractor()
    v = ext.extract(identity_lut, default_cs)
    np.testing.assert_allclose(v, 0.0, atol=1.0)


def test_feature_count(identity_lut: LUT3D, default_cs: InputColorSpace):
    ext = LuminanceDependentExtractor()
    v = ext.extract(identity_lut, default_cs)
    assert v.shape == (6,)
    assert len(ext.feature_names) == 6
