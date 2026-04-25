"""Shared fixtures for pytest."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from lut_features.parser import CubeData, parse_cube
from lut_features.lut import LUT3D
from lut_features.colorspace import InputColorSpace

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load(name: str) -> LUT3D:
    return LUT3D.from_cube_data(parse_cube(FIXTURES_DIR / name))


@pytest.fixture
def identity_lut() -> LUT3D:
    return _load("identity.cube")


@pytest.fixture
def warm_lut() -> LUT3D:
    return _load("warm_shift.cube")


@pytest.fixture
def cool_lut() -> LUT3D:
    return _load("cool_shift.cube")


@pytest.fixture
def desaturate_lut() -> LUT3D:
    return _load("desaturate.cube")


@pytest.fixture
def split_toning_lut() -> LUT3D:
    return _load("split_toning.cube")


@pytest.fixture
def default_cs() -> InputColorSpace:
    return InputColorSpace.SRGB
