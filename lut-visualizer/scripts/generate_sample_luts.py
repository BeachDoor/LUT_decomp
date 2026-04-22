"""Generate ~20 diverse synthetic LUTs for the demo features.json."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lut_features" / "src"))
from lut_features.colorspace import InputColorSpace, lab_to_lch, lch_to_lab, rgb_to_lab, lab_to_rgb

OUT_DIR = Path(__file__).parent.parent / "public" / "data" / "sample_luts"
OUT_DIR.mkdir(parents=True, exist_ok=True)
N = 17
CS = InputColorSpace.SRGB


def _write(name: str, fn: object) -> Path:
    vals = np.linspace(0.0, 1.0, N)
    lines = [f"LUT_3D_SIZE {N}", "DOMAIN_MIN 0.0 0.0 0.0", "DOMAIN_MAX 1.0 1.0 1.0", ""]
    for bi in range(N):
        for gi in range(N):
            for ri in range(N):
                r, g, b = vals[ri], vals[gi], vals[bi]
                ro, go, bo = fn(r, g, b)  # type: ignore[operator]
                lines.append(
                    f"{float(np.clip(ro,0,1)):.6f} "
                    f"{float(np.clip(go,0,1)):.6f} "
                    f"{float(np.clip(bo,0,1)):.6f}"
                )
    out = OUT_DIR / f"{name}.cube"
    out.write_text("\n".join(lines) + "\n")
    return out


def _scurve(x: float, strength: float = 1.0) -> float:
    x = float(np.clip(x, 0, 1))
    s = x * x * (3 - 2 * x)
    return x + (s - x) * strength


def _lum(r: float, g: float, b: float) -> float:
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


# 1. identity
_write("identity", lambda r, g, b: (r, g, b))

# 2. warm_mild
_write("warm_mild", lambda r, g, b: (r + 0.04, g + 0.005, b - 0.04))

# 3. warm_strong
_write("warm_strong", lambda r, g, b: (r + 0.09, g + 0.01, b - 0.09))

# 4. cool_mild
_write("cool_mild", lambda r, g, b: (r - 0.04, g - 0.005, b + 0.04))

# 5. cool_strong
_write("cool_strong", lambda r, g, b: (r - 0.09, g - 0.01, b + 0.09))

# 6. desaturate_50
def desat50(r: float, g: float, b: float):
    lum = _lum(r, g, b)
    return 0.5*r+0.5*lum, 0.5*g+0.5*lum, 0.5*b+0.5*lum
_write("desaturate_50", desat50)

# 7. desaturate_80
def desat80(r: float, g: float, b: float):
    lum = _lum(r, g, b)
    return 0.2*r+0.8*lum, 0.2*g+0.8*lum, 0.2*b+0.8*lum
_write("desaturate_80", desat80)

# 8. saturate_120
def sat120(r: float, g: float, b: float):
    lum = _lum(r, g, b)
    return 1.2*r-0.2*lum, 1.2*g-0.2*lum, 1.2*b-0.2*lum
_write("saturate_120", sat120)

# 9. high_contrast
def hicontrast(r: float, g: float, b: float):
    return _scurve(r, 0.8), _scurve(g, 0.8), _scurve(b, 0.8)
_write("high_contrast", hicontrast)

# 10. low_contrast_fade
def fade(r: float, g: float, b: float):
    return r*0.75+0.08, g*0.75+0.08, b*0.75+0.08
_write("low_contrast_fade", fade)

# 11. lifted_blacks
def lift(r: float, g: float, b: float):
    lum = _lum(r, g, b)
    sw = max(0, 1 - lum/0.3)
    return r+0.06*sw, g+0.04*sw, b+0.04*sw
_write("lifted_blacks", lift)

# 12. split_toning_blue_yellow
def split_by(r: float, g: float, b: float):
    lum = _lum(r, g, b)
    sw = max(0, 1 - lum/0.4)**1.5
    hw = max(0, (lum-0.6)/0.4)**1.5
    return r-0.04*sw+0.04*hw, g-0.02*sw+0.02*hw, b+0.07*sw-0.07*hw
_write("split_toning_blue_yellow", split_by)

# 13. split_toning_orange_teal (cross-process style)
def split_ot(r: float, g: float, b: float):
    lum = _lum(r, g, b)
    sw = max(0, 1 - lum/0.4)**1.5
    hw = max(0, (lum-0.6)/0.4)**1.5
    return r+0.05*sw-0.03*hw, g+0.01*sw+0.02*hw, b-0.06*sw+0.04*hw
_write("split_toning_orange_teal", split_ot)

# 14. vintage_fade  (warm + desaturated + faded)
def vintage(r: float, g: float, b: float):
    # desaturate
    lum = _lum(r, g, b)
    r2, g2, b2 = 0.7*r+0.3*lum, 0.7*g+0.3*lum, 0.7*b+0.3*lum
    # fade
    r2, g2, b2 = r2*0.8+0.07, g2*0.8+0.05, b2*0.8+0.03
    return r2, g2, b2
_write("vintage_fade", vintage)

# 15. cinematic_orange_teal (full LCh version, 17³)
def smoothstep(x: float) -> float:
    x = float(np.clip(x, 0, 1))
    return x * x * (3 - 2 * x)

def hue_push_scalar(h: float, center: float, width: float, amount: float) -> float:
    dist = (h - center + 180) % 360 - 180
    weight = max(0.0, 1.0 - (dist / width) ** 2)
    return h + weight * amount

def film_lch(r: float, g: float, b: float):
    rgb = np.array([r, g, b])
    lab = rgb_to_lab(rgb[np.newaxis], CS)[0]
    lch = lab_to_lch(lab[np.newaxis])[0]
    L, C, h = float(lch[0]), float(lch[1]), float(lch[2])
    sw = max(0, 1 - L / 35) ** 1.5
    L = L + 5 * sw
    L_n = float(np.clip(L / 100, 0, 1))
    L = 0.6 * smoothstep(L_n) * 100 + 0.4 * L
    h = hue_push_scalar(h, 40.0, 35.0, -12.0)
    h = hue_push_scalar(h, 220.0, 35.0, +15.0)
    h = h % 360
    C = C * (1 - 0.3 * max(0, 1 - L / 40))
    hw = float(np.clip((L - 60) / 30, 0, 1))
    lch_new = np.array([[L, C, h]])
    lab_new = lch_to_lab(lch_new)[0]
    lab_new[2] += 3.0 * hw
    rgb_out = lab_to_rgb(lab_new[np.newaxis], CS)[0]
    return float(rgb_out[0]), float(rgb_out[1]), float(rgb_out[2])

_write("cinematic_orange_teal", film_lch)

# 16. cross_process  (green push + strong saturation)
def cross(r: float, g: float, b: float):
    lum = _lum(r, g, b)
    r2 = _scurve(r*1.3-0.15, 0.5)
    g2 = _scurve(g*1.1+0.05, 0.5)
    b2 = _scurve(b*0.9-0.05, 0.3)
    return r2, g2, b2
_write("cross_process", cross)

# 17. cool_grade  (cool + high contrast + slight desat)
def cool_grade(r: float, g: float, b: float):
    r2 = _scurve(r*0.95-0.03, 0.6)
    g2 = _scurve(g*0.98, 0.6)
    b2 = _scurve(b*1.05+0.02, 0.6)
    lum = _lum(r2, g2, b2)
    return 0.9*r2+0.1*lum, 0.9*g2+0.1*lum, 0.9*b2+0.1*lum
_write("cool_grade", cool_grade)

# 18. warm_fade  (warm + faded blacks + low saturation)
def warm_fade(r: float, g: float, b: float):
    lum = _lum(r, g, b)
    r2, g2, b2 = 0.75*r+0.25*lum, 0.75*g+0.25*lum, 0.75*b+0.25*lum
    return r2*0.85+0.09, g2*0.85+0.06, b2*0.85+0.02
_write("warm_fade", warm_fade)

# 19. green_push  (hue push toward yellow-green)
def green_push(r: float, g: float, b: float):
    return r*0.9, g*1.08, b*0.88
_write("green_push", green_push)

# 20. matte_look  (low contrast, lifted shadows, slight cool)
def matte(r: float, g: float, b: float):
    return r*0.7+0.06, g*0.72+0.06, b*0.73+0.08
_write("matte_look", matte)

paths = sorted(OUT_DIR.glob("*.cube"))
print(f"Generated {len(paths)} LUTs in {OUT_DIR}")
for p in paths:
    print(f"  {p.name}")
