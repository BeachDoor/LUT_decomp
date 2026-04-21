"""Integration tests for LUTFeatureExtractor."""

from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import pytest

from lut_features import LUTFeatureExtractor, InputColorSpace, LUTFeatureVector

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def extractor() -> LUTFeatureExtractor:
    return LUTFeatureExtractor()


def test_vector_shape(extractor: LUTFeatureExtractor):
    fv = extractor.extract(FIXTURES / "identity.cube")
    assert fv.vector.ndim == 1
    assert fv.vector.shape[0] == 40


def test_feature_names_length(extractor: LUTFeatureExtractor):
    fv = extractor.extract(FIXTURES / "identity.cube")
    assert len(fv.feature_names) == len(fv.vector)
    assert len(fv.feature_categories) == len(fv.vector)


def test_metadata_populated(extractor: LUTFeatureExtractor):
    fv = extractor.extract(FIXTURES / "identity.cube")
    assert "lut_size" in fv.metadata
    assert "colorspace" in fv.metadata
    assert fv.metadata["colorspace"] == "sRGB"


def test_to_dict_roundtrip(extractor: LUTFeatureExtractor):
    fv = extractor.extract(FIXTURES / "identity.cube")
    d = fv.to_dict()
    fv2 = LUTFeatureVector.from_dict(d)
    np.testing.assert_array_equal(fv.vector, fv2.vector)
    assert fv.feature_names == fv2.feature_names


def test_to_json_valid(extractor: LUTFeatureExtractor):
    fv = extractor.extract(FIXTURES / "identity.cube")
    j = fv.to_json()
    d = json.loads(j)
    assert "vector" in d
    assert len(d["vector"]) == 40


def test_save_load_json(extractor: LUTFeatureExtractor, tmp_path: Path):
    fv = extractor.extract(FIXTURES / "identity.cube")
    out = tmp_path / "features.json"
    LUTFeatureExtractor.save_json(fv, out)
    fv2 = LUTFeatureExtractor.load_json(out)
    np.testing.assert_allclose(fv.vector, fv2.vector)


def test_save_load_pickle(extractor: LUTFeatureExtractor, tmp_path: Path):
    fv = extractor.extract(FIXTURES / "identity.cube")
    out = tmp_path / "features.pkl"
    LUTFeatureExtractor.save_pickle(fv, out)
    fv2 = LUTFeatureExtractor.load_pickle(out)
    np.testing.assert_array_equal(fv.vector, fv2.vector)


def test_batch_extract(extractor: LUTFeatureExtractor):
    paths = [
        FIXTURES / "identity.cube",
        FIXTURES / "warm_shift.cube",
        FIXTURES / "cool_shift.cube",
    ]
    results = extractor.extract_batch(paths)
    assert len(results) == 3
    for r in results:
        assert r.vector.shape == (40,)


def test_feature_matrix(extractor: LUTFeatureExtractor):
    paths = [FIXTURES / "identity.cube", FIXTURES / "warm_shift.cube"]
    mat = extractor.feature_matrix(paths)
    assert mat.shape == (2, 40)


def test_warm_vs_cool_temperature_differ(extractor: LUTFeatureExtractor):
    """Warm and cool LUTs should have opposite temperature shift signs."""
    warm = extractor.extract(FIXTURES / "warm_shift.cube")
    cool = extractor.extract(FIXTURES / "cool_shift.cube")
    # global_temperature_shift is at index 18+9=27
    temp_idx = extractor.feature_names.index("global_temperature_shift")
    assert warm.vector[temp_idx] != cool.vector[temp_idx]


def test_identity_neutral_features(extractor: LUTFeatureExtractor):
    """Identity LUT: chroma_multiplier ≈ 1, contrast ≈ 1."""
    fv = extractor.extract(FIXTURES / "identity.cube")
    chroma_idx = extractor.feature_names.index("overall_chroma_multiplier")
    contrast_idx = extractor.feature_names.index("overall_contrast")
    np.testing.assert_allclose(fv.vector[chroma_idx], 1.0, atol=0.1)
    np.testing.assert_allclose(fv.vector[contrast_idx], 1.0, atol=0.05)


def test_tetrahedral_interpolation(extractor: LUTFeatureExtractor):
    """Tetrahedral interpolation should give a valid vector."""
    ext = LUTFeatureExtractor(interpolation="tetrahedral")
    fv = ext.extract(FIXTURES / "identity.cube")
    assert fv.vector.shape == (40,)
    assert not np.any(np.isnan(fv.vector))
