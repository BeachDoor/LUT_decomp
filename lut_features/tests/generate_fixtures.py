"""Generate synthetic .cube fixture files for testing.

Run from the lut_features/ directory:
    uv run python tests/generate_fixtures.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

FIXTURES = Path(__file__).parent / "fixtures"
FIXTURES.mkdir(exist_ok=True)

N = 17  # LUT size (smaller = faster tests, still reasonable accuracy)


def _write_cube(name: str, fn: object) -> None:
    vals = np.linspace(0.0, 1.0, N)
    lines = [
        f"LUT_3D_SIZE {N}",
        "DOMAIN_MIN 0.0 0.0 0.0",
        "DOMAIN_MAX 1.0 1.0 1.0",
        "",
    ]
    # .cube ordering: R fastest
    for b in range(N):
        for g in range(N):
            for r in range(N):
                rv, gv, bv = vals[r], vals[g], vals[b]
                ro, go, bo = fn(rv, gv, bv)  # type: ignore[operator]
                ro = float(np.clip(ro, 0.0, 1.0))
                go = float(np.clip(go, 0.0, 1.0))
                bo = float(np.clip(bo, 0.0, 1.0))
                lines.append(f"{ro:.6f} {go:.6f} {bo:.6f}")

    (FIXTURES / name).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  wrote {name}")


def identity(r: float, g: float, b: float) -> tuple[float, float, float]:
    return r, g, b


def warm_shift(r: float, g: float, b: float) -> tuple[float, float, float]:
    """Adds a warm (orange) colour cast: boost R, reduce B."""
    return r + 0.07, g + 0.01, b - 0.07


def cool_shift(r: float, g: float, b: float) -> tuple[float, float, float]:
    """Adds a cool (blue) colour cast: reduce R, boost B."""
    return r - 0.07, g - 0.01, b + 0.07


def desaturate(r: float, g: float, b: float) -> tuple[float, float, float]:
    """Desaturate by 50% toward luminance."""
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    f = 0.5
    return f * r + (1 - f) * lum, f * g + (1 - f) * lum, f * b + (1 - f) * lum


def split_toning(r: float, g: float, b: float) -> tuple[float, float, float]:
    """Blue shadows, yellow highlights (split-toning)."""
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    shadow_w = float(np.clip(1.0 - lum / 0.35, 0.0, 1.0))
    highlight_w = float(np.clip((lum - 0.65) / 0.35, 0.0, 1.0))
    # shadows → blue  (increase B, decrease R/G slightly)
    # highlights → yellow/warm (increase R/G, decrease B)
    r_out = r - 0.06 * shadow_w + 0.06 * highlight_w
    g_out = g - 0.03 * shadow_w + 0.03 * highlight_w
    b_out = b + 0.10 * shadow_w - 0.10 * highlight_w
    return r_out, g_out, b_out


if __name__ == "__main__":
    print("Generating fixtures …")
    _write_cube("identity.cube", identity)
    _write_cube("warm_shift.cube", warm_shift)
    _write_cube("cool_shift.cube", cool_shift)
    _write_cube("desaturate.cube", desaturate)
    _write_cube("split_toning.cube", split_toning)
    print("Done.")
