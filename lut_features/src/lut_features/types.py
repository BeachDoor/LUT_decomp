from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class LUTFeatureVector:
    """Feature vector extracted from a single LUT."""

    vector: np.ndarray
    feature_names: list[str]
    feature_categories: list[str]
    metadata: dict[str, Any]

    def __post_init__(self) -> None:
        n = len(self.vector)
        if len(self.feature_names) != n:
            raise ValueError(
                f"feature_names length {len(self.feature_names)} != vector length {n}"
            )
        if len(self.feature_categories) != n:
            raise ValueError(
                f"feature_categories length {len(self.feature_categories)} != vector length {n}"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "vector": self.vector.tolist(),
            "feature_names": self.feature_names,
            "feature_categories": self.feature_categories,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> LUTFeatureVector:
        return cls(
            vector=np.array(d["vector"]),
            feature_names=d["feature_names"],
            feature_categories=d["feature_categories"],
            metadata=d["metadata"],
        )
