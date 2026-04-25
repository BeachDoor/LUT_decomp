"""
Generate a realistic "cinematic orange-teal" LUT and run feature extraction
on it alongside colour-science's Colour_Correct.cube for comparison.

Usage:
    uv run python demo_real_lut.py
"""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np

# ── 1. Build the film look LUT ──────────────────────────────────────────────
# We work in LCh to apply perceptually meaningful operations:
#   • S-curve contrast on L*
#   • Shadow lift (filmic toe)
#   • Orange-teal hue push (hue-selective)
#   • Slight shadow desaturation

import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from lut_features.colorspace import (
    InputColorSpace,
    lab_to_lch,
    lch_to_lab,
    neutral_gray_rgb,
    rgb_to_lab,
    lab_to_rgb,
)

CS = InputColorSpace.SRGB
N = 33


def _smoothstep(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def _hue_push(h: np.ndarray, center: float, width: float, amount: float) -> np.ndarray:
    """Push hue values near `center` by `amount` degrees."""
    dist = (h - center + 180) % 360 - 180          # signed angular distance
    weight = np.maximum(0.0, 1.0 - (dist / width) ** 2)
    return h + weight * amount


def film_look_transform(rgb_in: np.ndarray) -> np.ndarray:
    """Apply a cinematic orange-teal grade in LCh space.

    Operations:
    1. Shadow lift (filmic toe)
    2. S-curve contrast on L*
    3. Hue push: reds/oranges → more orange; blues/cyans → more teal
    4. Slight shadow desaturation
    5. Subtle warm cast on highlights
    """
    lab = rgb_to_lab(np.clip(rgb_in, 0, 1), CS)        # (..., 3) Lab
    lch = lab_to_lch(lab)                               # (..., 3) LCh

    L = lch[..., 0].copy()
    C = lch[..., 1].copy()
    h = lch[..., 2].copy()

    # ① Shadow lift: add ~4 L* units in deep shadows
    shadow_w = np.clip(1.0 - L / 35.0, 0, 1) ** 1.5
    L = L + 5.0 * shadow_w

    # ② S-curve contrast (smooth)
    L_norm = np.clip(L / 100.0, 0, 1)
    L_curved = _smoothstep(L_norm) * 100.0
    L = 0.6 * L_curved + 0.4 * L           # blend: partial S-curve

    # ③ Orange-teal hue push
    #    reds/oranges (h ≈ 20–60°) → shift -12° (more orange/cinnabar)
    #    blues/cyans  (h ≈ 200–240°) → shift +15° (more teal)
    h = _hue_push(h, center=40.0,  width=35.0, amount=-12.0)
    h = _hue_push(h, center=220.0, width=35.0, amount=+15.0)
    h = h % 360.0

    # ④ Shadow desaturation (chroma *= 0.7 in deep shadows)
    sat_factor = 1.0 - 0.3 * np.clip(1.0 - L / 40.0, 0, 1)
    C = C * sat_factor

    # ⑤ Slight warm cast in highlights (b* +3 at L* > 70)
    highlight_w = np.clip((L - 60.0) / 30.0, 0, 1)

    lch_new = np.stack([L, C, h], axis=-1)
    lab_new = lch_to_lab(lch_new)
    lab_new[..., 2] += 3.0 * highlight_w   # add to b* (warm/yellow direction)

    rgb_out = lab_to_rgb(lab_new, CS)
    return np.clip(rgb_out, 0, 1)


def generate_film_lut(path: Path, size: int = N) -> None:
    vals = np.linspace(0.0, 1.0, size)
    r_idx, g_idx, b_idx = np.meshgrid(vals, vals, vals, indexing="ij")  # (N,N,N)
    rgb_grid = np.stack([r_idx, g_idx, b_idx], axis=-1)                  # (N,N,N,3)
    rgb_out = film_look_transform(rgb_grid)                               # (N,N,N,3)

    lines = [f"LUT_3D_SIZE {size}", "DOMAIN_MIN 0.0 0.0 0.0", "DOMAIN_MAX 1.0 1.0 1.0", ""]
    # .cube ordering: R fastest → iterate B, G, R
    for bi in range(size):
        for gi in range(size):
            for ri in range(size):
                ro, go, bo = rgb_out[ri, gi, bi]
                lines.append(f"{ro:.6f} {go:.6f} {bo:.6f}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  Generated: {path} ({size}³ = {size**3} entries)")


# ── 2. Copy colour-science's Colour_Correct.cube ────────────────────────────
def find_colour_correct() -> Path | None:
    base = Path("/root/.cache/uv")
    matches = list(base.rglob("Colour_Correct.cube"))
    # prefer resolve_cube version
    for m in matches:
        if "resolve_cube" in str(m):
            return m
    return matches[0] if matches else None


# ── 3. Run the extractor and print a comparison report ──────────────────────
from lut_features import LUTFeatureExtractor, InputColorSpace as ICS


def print_report(title: str, fv: object) -> None:  # type: ignore[type-arg]
    from lut_features import LUTFeatureVector
    fv_: LUTFeatureVector = fv  # type: ignore[assignment]

    print(f"\n{'═'*60}")
    print(f"  {title}")
    print(f"  LUT size: {fv_.metadata['lut_size']}³  |  colorspace: {fv_.metadata['colorspace']}")
    print(f"{'═'*60}")

    prev_cat = None
    for name, cat, val in zip(fv_.feature_names, fv_.feature_categories, fv_.vector):
        if cat != prev_cat:
            print(f"\n  ── {cat} ──")
            prev_cat = cat
        bar_len = int(abs(val) * 5) if cat != "global_tone" else int(abs(val) * 1000)
        bar = ("+" if val >= 0 else "─") * min(bar_len, 30)
        print(f"  {name:<45s}  {val:+8.3f}  {bar}")


def interpret(fv: object) -> None:  # type: ignore[type-arg]
    from lut_features import LUTFeatureVector
    fv_: LUTFeatureVector = fv  # type: ignore[assignment]
    v = fv_.vector
    names = fv_.feature_names

    def get(n: str) -> float:
        return float(v[names.index(n)])

    print("\n  ── 解釈 ──")

    temp = get("global_temperature_shift")
    print(f"  色温度: {'🔶 ウォーム寄り' if temp > 0.0001 else '🔷 クール寄り' if temp < -0.0001 else 'ニュートラル'} (shift={temp:+.5f} uv)")

    cm = get("overall_chroma_multiplier")
    print(f"  彩度: {'✅ 増加' if cm > 1.05 else '↘ 減少' if cm < 0.95 else 'ほぼ変化なし'} (×{cm:.3f})")

    contrast = get("overall_contrast")
    print(f"  コントラスト: {'高め' if contrast > 1.05 else '低め' if contrast < 0.95 else 'ほぼ変化なし'} (ratio={contrast:.3f})")

    shadow_b = get("tone_shadow_b_change")
    high_b   = get("tone_highlight_b_change")
    if shadow_b < -0.5 and high_b > 0.5:
        print(f"  トーン: ブルーシャドウ + イエローハイライト (split-toning)")
    elif shadow_b > 0.5 and high_b < -0.5:
        print(f"  トーン: ウォームシャドウ + クールハイライト (cinematic)")
    elif abs(shadow_b) < 0.3 and abs(high_b) < 0.3:
        print(f"  トーン: 色被りなし (neutral)")
    else:
        print(f"  トーン: shadow Δb*={shadow_b:+.2f}  highlight Δb*={high_b:+.2f}")

    r_hs = get("hue_band_R_hue_shift")
    b_hs = get("hue_band_B_hue_shift")
    if r_hs < -2 or b_hs > 2:
        print(f"  色相: レッド→オレンジ / ブルー→ティール方向のプッシュ (orange-teal look)")

    nl = get("tone_curve_nonlinearity")
    print(f"  非線形性: トーンカーブ残差RMSE={nl:.3f} L*単位 ({'有意なS-curve' if nl > 0.5 else 'ほぼ線形'})")


# ── main ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    lut_dir = Path("sample_luts")
    lut_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("  LUT特徴量抽出デモ")
    print("=" * 60)

    # Generate film look LUT
    film_path = lut_dir / "cinematic_orange_teal.cube"
    print("\n[1/2] フィルムルックLUTを生成中 ...")
    generate_film_lut(film_path)

    # Copy Colour_Correct
    cc_src = find_colour_correct()
    cc_path = lut_dir / "colour_correct.cube"
    if cc_src:
        shutil.copy(cc_src, cc_path)
        print(f"[2/2] colour-science テストLUTをコピー: {cc_src.name}")
    else:
        print("[2/2] Colour_Correct.cube が見つかりませんでした")

    # Run extractor
    extractor = LUTFeatureExtractor(input_colorspace=ICS.SRGB)

    print("\n" + "=" * 60)
    print("  特徴量抽出を実行中 ...")
    print("=" * 60)

    luts_to_run = [(film_path, "Cinematic Orange-Teal")]
    if cc_path.exists():
        luts_to_run.append((cc_path, "Colour_Correct (colour-science)"))

    results = []
    for path, title in luts_to_run:
        print(f"\n  処理中: {path.name}")
        fv = extractor.extract(path)
        results.append((title, fv))
        print_report(title, fv)
        interpret(fv)

    # Side-by-side summary
    if len(results) == 2:
        print(f"\n\n{'═'*60}")
        print("  比較サマリー")
        print(f"{'═'*60}")
        print(f"  {'特徴量':<40s}  {'Orange-Teal':>12s}  {'Colour_Correct':>14s}")
        print(f"  {'-'*40}  {'-'*12}  {'-'*14}")
        highlight_names = [
            "global_temperature_shift",
            "global_tint_shift",
            "overall_chroma_multiplier",
            "overall_contrast",
            "tone_shadow_b_change",
            "tone_highlight_b_change",
            "hue_band_R_hue_shift",
            "hue_band_B_hue_shift",
            "tone_curve_nonlinearity",
        ]
        fv1 = results[0][1]
        fv2 = results[1][1]
        for name in highlight_names:
            idx = fv1.feature_names.index(name)
            v1 = fv1.vector[idx]
            v2 = fv2.vector[idx]
            print(f"  {name:<40s}  {v1:>+12.4f}  {v2:>+14.4f}")

    print("\n完了。")
