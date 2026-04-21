"""Abstract base class for feature extractors."""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from ..colorspace import InputColorSpace
from ..lut import LUT3D, InterpolationMethod


class FeatureExtractor(ABC):
    """Extract a sub-vector of features from a LUT3D."""

    @property
    @abstractmethod
    def feature_names(self) -> list[str]:
        """Names for each output dimension."""
        ...

    @property
    @abstractmethod
    def category_name(self) -> str:
        """Human-readable category label applied to all dimensions."""
        ...

    @abstractmethod
    def extract(
        self,
        lut: LUT3D,
        colorspace: InputColorSpace,
        interpolation: InterpolationMethod = "trilinear",
    ) -> np.ndarray:
        """Compute features from the given LUT.

        Args:
            lut: The 3D LUT to analyse.
            colorspace: The assumed input/output colorspace of the LUT.
            interpolation: Interpolation method for LUT evaluation.

        Returns:
            1-D numpy array of shape (len(feature_names),).
        """
        ...
