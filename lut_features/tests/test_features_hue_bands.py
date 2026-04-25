"""Tests for Category 1 – Hue-band features."""

from __future__ import annotations

import numpy as np

from lut_features.colorspace import InputColorSpace
from lut_features.features.hue_bands import HueBandsExtractor
from lut_features.lut import LUT3D


def test_identity_hue_shift_zero(identity_lut: LUT3D, default_cs: InputColorSpace):
    ext = HueBandsExtractor()
    v = ext.extract(identity_lut, default_cs)
    # feature_names: [band_hue_shift, band_chroma_change, band_lightness_change, ...]
    # hue_shift slots: indices 0, 3, 6, 9, 12, 15
    hue_shifts = v[0::3]
    np.testing.assert_allclose(hue_shifts, 0.0, atol=1.0)


def test_identity_chroma_change_unity(identity_lut: LUT3D, default_cs: InputColorSpace):
    ext = HueBandsExtractor()
    v = ext.extract(identity_lut, default_cs)
    chroma_changes = v[1::3]
    np.testing.assert_allclose(chroma_changes, 1.0, atol=0.05)


def test_identity_lightness_change_zero(identity_lut: LUT3D, default_cs: InputColorSpace):
    ext = HueBandsExtractor()
    v = ext.extract(identity_lut, default_cs)
    lightness_changes = v[2::3]
    np.testing.assert_allclose(lightness_changes, 0.0, atol=1.0)


def test_desaturate_chroma_below_one(desaturate_lut: LUT3D, default_cs: InputColorSpace):
    ext = HueBandsExtractor()
    v = ext.extract(desaturate_lut, default_cs)
    chroma_changes = v[1::3]
    assert np.all(chroma_changes < 1.0), (
        f"Expected all chroma_change < 1.0 for desaturate LUT, got {chroma_changes}"
    )


def test_feature_count(identity_lut: LUT3D, default_cs: InputColorSpace):
    ext = HueBandsExtractor()
    v = ext.extract(identity_lut, default_cs)
    assert v.shape == (18,)
    assert len(ext.feature_names) == 18
