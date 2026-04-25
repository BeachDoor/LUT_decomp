"""Adobe .cube LUT file parser.

Only 3D LUTs are supported. The data ordering in .cube format is R-fastest:
  flat_index = r + g*N + b*N*N
After reading, data is stored as ndarray[r, g, b, channel].
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


class CubeParseError(ValueError):
    """Raised when a .cube file cannot be parsed."""


@dataclass
class CubeData:
    """Parsed representation of a .cube LUT file."""

    size: int
    domain_min: np.ndarray  # shape (3,)
    domain_max: np.ndarray  # shape (3,)
    data: np.ndarray        # shape (size, size, size, 3), indexed [r, g, b, c]


def parse_cube(path: str | Path) -> CubeData:
    """Parse an Adobe .cube LUT file (3D only).

    Raises:
        FileNotFoundError: If the file does not exist.
        CubeParseError: If the file is malformed or is a 1D LUT.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"LUT file not found: {path}")

    size: int | None = None
    domain_min = np.array([0.0, 0.0, 0.0])
    domain_max = np.array([1.0, 1.0, 1.0])
    data_rows: list[list[float]] = []

    with path.open(encoding="utf-8", errors="replace") as f:
        for line_no, raw in enumerate(f, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            upper = line.upper()

            if upper.startswith("LUT_1D_SIZE"):
                raise CubeParseError(
                    f"{path}: 1D LUTs are not supported (line {line_no})"
                )

            if upper.startswith("LUT_3D_SIZE"):
                parts = line.split()
                if len(parts) != 2:
                    raise CubeParseError(
                        f"{path}: malformed LUT_3D_SIZE at line {line_no}"
                    )
                try:
                    size = int(parts[1])
                except ValueError:
                    raise CubeParseError(
                        f"{path}: non-integer LUT_3D_SIZE at line {line_no}"
                    )
                if not (2 <= size <= 256):
                    raise CubeParseError(
                        f"{path}: LUT_3D_SIZE {size} out of range [2, 256]"
                    )
                continue

            if upper.startswith("DOMAIN_MIN"):
                parts = line.split()
                if len(parts) != 4:
                    raise CubeParseError(
                        f"{path}: malformed DOMAIN_MIN at line {line_no}"
                    )
                try:
                    domain_min = np.array([float(p) for p in parts[1:]])
                except ValueError:
                    raise CubeParseError(
                        f"{path}: invalid DOMAIN_MIN values at line {line_no}"
                    )
                continue

            if upper.startswith("DOMAIN_MAX"):
                parts = line.split()
                if len(parts) != 4:
                    raise CubeParseError(
                        f"{path}: malformed DOMAIN_MAX at line {line_no}"
                    )
                try:
                    domain_max = np.array([float(p) for p in parts[1:]])
                except ValueError:
                    raise CubeParseError(
                        f"{path}: invalid DOMAIN_MAX values at line {line_no}"
                    )
                continue

            # Skip other known header keywords
            if upper.startswith(("TITLE", "LUT_3D_INPUT_RANGE")):
                continue

            # Data line: must start with a digit, '-', or '.'
            if line[0] in "0123456789-.":
                parts = line.split()
                if len(parts) < 3:
                    raise CubeParseError(
                        f"{path}: data line {line_no} has fewer than 3 values"
                    )
                try:
                    data_rows.append([float(p) for p in parts[:3]])
                except ValueError:
                    raise CubeParseError(
                        f"{path}: non-numeric data at line {line_no}"
                    )
                continue

            # Unknown keyword — silently skip (some LUT tools add extras)

    if size is None:
        raise CubeParseError(f"{path}: LUT_3D_SIZE directive not found")

    expected = size ** 3
    if len(data_rows) != expected:
        raise CubeParseError(
            f"{path}: expected {expected} data rows for size {size}, "
            f"got {len(data_rows)}"
        )

    # .cube ordering: R fastest → flat[r + g*N + b*N*N]
    # reshape(N, N, N, 3) in C-order gives [b, g, r, c]; transpose to [r, g, b, c]
    flat = np.array(data_rows, dtype=np.float64)        # (N^3, 3)
    cube = flat.reshape(size, size, size, 3)             # [b, g, r, c]
    data = cube.transpose(2, 1, 0, 3)                   # [r, g, b, c]

    return CubeData(size=size, domain_min=domain_min, domain_max=domain_max, data=data)
