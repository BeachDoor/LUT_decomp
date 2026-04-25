"""Main integration interface for LUT feature extraction."""

from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any

import numpy as np

from .colorspace import InputColorSpace
from .lut import LUT3D, InterpolationMethod
from .parser import parse_cube
from .types import LUTFeatureVector
from .features import (
    HueBandsExtractor,
    ToneExtractor,
    GlobalToneExtractor,
    LuminanceDependentExtractor,
    NonlinearityExtractor,
    FeatureExtractor,
)


class LUTFeatureExtractor:
    """Extract perceptual feature vectors from .cube LUT files.

    Example::

        extractor = LUTFeatureExtractor()
        features = extractor.extract("path/to/look.cube")
        print(features.vector.shape)    # (40,)
        print(features.feature_names)
    """

    def __init__(
        self,
        input_colorspace: InputColorSpace = InputColorSpace.SRGB,
        interpolation: InterpolationMethod = "trilinear",
        extractors: list[FeatureExtractor] | None = None,
    ) -> None:
        self.input_colorspace = input_colorspace
        self.interpolation = interpolation
        self._extractors: list[FeatureExtractor] = extractors or [
            HueBandsExtractor(),
            ToneExtractor(),
            GlobalToneExtractor(),
            LuminanceDependentExtractor(),
            NonlinearityExtractor(),
        ]

    @property
    def feature_names(self) -> list[str]:
        names: list[str] = []
        for ext in self._extractors:
            names.extend(ext.feature_names)
        return names

    @property
    def feature_categories(self) -> list[str]:
        cats: list[str] = []
        for ext in self._extractors:
            cats.extend([ext.category_name] * len(ext.feature_names))
        return cats

    def extract(self, path: str | Path) -> LUTFeatureVector:
        """Extract features from a single .cube file.

        Args:
            path: Path to a .cube LUT file.

        Returns:
            LUTFeatureVector with a 1-D vector of shape (N,).
        """
        path = Path(path)
        cube = parse_cube(path)
        lut = LUT3D.from_cube_data(cube)
        return self._extract_from_lut(lut, str(path))

    def extract_from_lut(self, lut: LUT3D, name: str = "") -> LUTFeatureVector:
        """Extract features from an already-loaded LUT3D object."""
        return self._extract_from_lut(lut, name)

    def _extract_from_lut(self, lut: LUT3D, source: str) -> LUTFeatureVector:
        parts: list[np.ndarray] = []
        for ext in self._extractors:
            parts.append(
                ext.extract(lut, self.input_colorspace, self.interpolation)
            )
        vector = np.concatenate(parts)

        metadata: dict[str, Any] = {
            "source": source,
            "lut_size": lut.size,
            "colorspace": self.input_colorspace.value,
            "interpolation": self.interpolation,
            "domain_min": lut.domain_min.tolist(),
            "domain_max": lut.domain_max.tolist(),
        }

        return LUTFeatureVector(
            vector=vector,
            feature_names=self.feature_names,
            feature_categories=self.feature_categories,
            metadata=metadata,
        )

    def extract_batch(self, paths: list[str | Path]) -> list[LUTFeatureVector]:
        """Extract features from multiple .cube files.

        Args:
            paths: List of paths to .cube files.

        Returns:
            List of LUTFeatureVector, one per file.
        """
        return [self.extract(p) for p in paths]

    @staticmethod
    def save_json(features: LUTFeatureVector, path: str | Path) -> None:
        Path(path).write_text(features.to_json(), encoding="utf-8")

    @staticmethod
    def load_json(path: str | Path) -> LUTFeatureVector:
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        return LUTFeatureVector.from_dict(d)

    @staticmethod
    def save_pickle(features: LUTFeatureVector, path: str | Path) -> None:
        Path(path).write_bytes(pickle.dumps(features))

    @staticmethod
    def load_pickle(path: str | Path) -> LUTFeatureVector:
        return pickle.loads(Path(path).read_bytes())  # type: ignore[no-any-return]  # noqa: S301

    def feature_matrix(self, paths: list[str | Path]) -> np.ndarray:
        """Return a (n_luts, n_features) matrix for batch NMF input."""
        results = self.extract_batch(paths)
        return np.stack([r.vector for r in results])
