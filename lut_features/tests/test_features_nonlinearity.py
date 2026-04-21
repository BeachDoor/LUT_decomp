"""Tests for Category 5 – Non-linearity indicators."""

from __future__ import annotations

import numpy as np

from lut_features.colorspace import InputColorSpace
from lut_features.features.nonlinearity import NonlinearityExtractor
from lut_features.lut import LUT3D


def test_identity_all_near_zero(identity_lut: LUT3D, default_cs: InputColorSpace):
    ext = NonlinearityExtractor()
    v = ext.extract(identity_lut, default_cs)
    # tone_curve_nonlinearity and chroma_response_nonlinearity should be ~ 0
    np.testing.assert_allclose(v[0], 0.0, atol=0.5)
    np.testing.assert_allclose(v[2], 0.0, atol=0.5)


def test_feature_count(identity_lut: LUT3D, default_cs: InputColorSpace):
    ext = NonlinearityExtractor()
    v = ext.extract(identity_lut, default_cs)
    assert v.shape == (3,)
    assert len(ext.feature_names) == 3


def test_all_nonnegative(identity_lut: LUT3D, default_cs: InputColorSpace):
    """RMSE-based indicators are non-negative."""
    ext = NonlinearityExtractor()
    v = ext.extract(identity_lut, default_cs)
    assert np.all(v >= 0.0)
