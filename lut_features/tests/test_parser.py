"""Tests for the .cube file parser."""

from __future__ import annotations

import textwrap
from pathlib import Path

import numpy as np
import pytest

from lut_features.parser import CubeData, CubeParseError, parse_cube

FIXTURES = Path(__file__).parent / "fixtures"


def test_identity_parse():
    data = parse_cube(FIXTURES / "identity.cube")
    assert data.size == 17
    assert data.data.shape == (17, 17, 17, 3)
    np.testing.assert_array_almost_equal(data.domain_min, [0, 0, 0])
    np.testing.assert_array_almost_equal(data.domain_max, [1, 1, 1])


def test_identity_data_ordering():
    """In identity LUT, data[r,g,b] == [r_val, g_val, b_val]."""
    data = parse_cube(FIXTURES / "identity.cube")
    N = data.size
    vals = np.linspace(0, 1, N)
    for ri in [0, 4, 8, N - 1]:
        for gi in [0, 4, N - 1]:
            for bi in [0, N - 1]:
                expected = [vals[ri], vals[gi], vals[bi]]
                np.testing.assert_allclose(data.data[ri, gi, bi], expected, atol=1e-5)


def test_missing_size(tmp_path: Path):
    cube = tmp_path / "bad.cube"
    cube.write_text("0.0 0.0 0.0\n1.0 1.0 1.0\n")
    with pytest.raises(CubeParseError, match="LUT_3D_SIZE"):
        parse_cube(cube)


def test_1d_lut_rejected(tmp_path: Path):
    cube = tmp_path / "1d.cube"
    cube.write_text("LUT_1D_SIZE 3\n0.0\n0.5\n1.0\n")
    with pytest.raises(CubeParseError, match="1D"):
        parse_cube(cube)


def test_wrong_count(tmp_path: Path):
    cube = tmp_path / "bad.cube"
    cube.write_text("LUT_3D_SIZE 2\n0.0 0.0 0.0\n1.0 1.0 1.0\n")
    with pytest.raises(CubeParseError, match="expected 8"):
        parse_cube(cube)


def test_file_not_found():
    with pytest.raises(FileNotFoundError):
        parse_cube("/nonexistent/path/file.cube")


def test_comments_and_blank_lines(tmp_path: Path):
    """Parser skips # comments and blank lines."""
    N = 2
    lines = [
        "# This is a comment",
        "",
        "LUT_3D_SIZE 2",
        "DOMAIN_MIN 0.0 0.0 0.0",
        "DOMAIN_MAX 1.0 1.0 1.0",
        "",
    ]
    # 8 data rows for 2^3
    vals = np.linspace(0, 1, 2)
    for b in range(2):
        for g in range(2):
            for r in range(2):
                lines.append(f"{vals[r]:.1f} {vals[g]:.1f} {vals[b]:.1f}")
    (tmp_path / "c.cube").write_text("\n".join(lines))
    data = parse_cube(tmp_path / "c.cube")
    assert data.size == 2
