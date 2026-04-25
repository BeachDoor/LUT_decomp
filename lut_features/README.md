# lut-features

LUT feature extraction module for photo/video grading pipelines.

`.cube` 形式の3D LUTファイルを読み込み、写真家・カラリストの語彙に対応した約40次元の知覚的特徴量ベクトルに変換します。特徴量は全てCIELAB D65空間で計算され、後段のNMF (非負値行列因子分解) への入力として設計されています。

```
[LUT群] → [lut-features] → 特徴量行列 → [NMF] → 基底成分 → look生成
```

---

## インストール

Python 3.11以上・[uv](https://docs.astral.sh/uv/) が必要です。

```bash
git clone <repo-url>
cd lut_features
uv sync
```

開発用 (pytest / mypy を含む):

```bash
uv sync --dev
```

---

## クイックスタート

### 単一LUTから特徴量を抽出する

```python
from lut_features import LUTFeatureExtractor

extractor = LUTFeatureExtractor()
features = extractor.extract("path/to/look.cube")

print(features.vector.shape)       # (40,)
print(features.feature_names[:4])  # ['hue_band_R_hue_shift', ...]
```

### 複数LUTをまとめてNMF用行列にする

```python
import numpy as np
from lut_features import LUTFeatureExtractor

extractor = LUTFeatureExtractor()

paths = ["film_a.cube", "film_b.cube", "film_c.cube"]
matrix = extractor.feature_matrix(paths)
# → shape (3, 40)  : 行 = LUT, 列 = 特徴量次元
```

---

## 詳細な使い方

### LUTFeatureExtractor の初期化オプション

```python
from lut_features import LUTFeatureExtractor, InputColorSpace

extractor = LUTFeatureExtractor(
    input_colorspace=InputColorSpace.SRGB,   # LUTの入出力色空間
    interpolation="trilinear",               # 補間方式
)
```

| パラメータ | 選択肢 | デフォルト | 説明 |
|-----------|--------|-----------|------|
| `input_colorspace` | `InputColorSpace.SRGB` / `InputColorSpace.REC709` | `SRGB` | LUTが想定する入出力色空間 |
| `interpolation` | `"trilinear"` / `"tetrahedral"` | `"trilinear"` | LUT補間方式。`"tetrahedral"` はDaVinci Resolveの内部動作に近い |

### 単一LUTの処理

```python
features = extractor.extract("look.cube")

# 特徴量ベクトル (numpy配列)
print(features.vector)             # [ 0.5  1.02  0.3 ... ]

# 各次元の名前
print(features.feature_names)
# ['hue_band_R_hue_shift', 'hue_band_R_chroma_change', ...]

# カテゴリ名 (NMFの解釈に利用可)
print(features.feature_categories)
# ['hue_bands', 'hue_bands', ..., 'tone', ..., 'global_tone', ...]

# 入力LUTのメタデータ
print(features.metadata)
# {'source': 'look.cube', 'lut_size': 33, 'colorspace': 'sRGB', ...}
```

### バッチ処理

```python
from pathlib import Path

lut_paths = list(Path("/path/to/luts").glob("*.cube"))

# 個別のLUTFeatureVectorのリストとして取得
results = extractor.extract_batch(lut_paths)

# NMF用に特徴量行列として取得  (n_luts × n_features)
matrix = extractor.feature_matrix(lut_paths)
print(matrix.shape)   # (n_luts, 40)
```

### 特定の特徴量だけを参照する

```python
features = extractor.extract("look.cube")

# 名前で特定の次元を引く
idx = features.feature_names.index("overall_chroma_multiplier")
print(f"彩度変化: {features.vector[idx]:.3f}")   # 1.0 = 変化なし

# カテゴリでまとめて取り出す
import numpy as np
tone_mask = [c == "tone" for c in features.feature_categories]
tone_features = features.vector[tone_mask]
print(f"トーン特徴量 (9次元): {tone_features}")
```

### 結果の保存・読み込み

```python
# JSON
LUTFeatureExtractor.save_json(features, "features.json")
loaded = LUTFeatureExtractor.load_json("features.json")

# Pickle (numpy配列をそのまま保持)
LUTFeatureExtractor.save_pickle(features, "features.pkl")
loaded = LUTFeatureExtractor.load_pickle("features.pkl")

# dict / JSON文字列に変換
d = features.to_dict()
j = features.to_json()

# 復元
from lut_features import LUTFeatureVector
features2 = LUTFeatureVector.from_dict(d)
```

---

## CLIスクリプト

### 単一LUTの特徴量を表示する

```bash
uv run python examples/extract_single.py path/to/look.cube
```

出力例:

```
Processing: look.cube

Feature vector shape: (40,)
LUT size: 33³
Colorspace: sRGB
Interpolation: trilinear

── hue_bands ──
  hue_band_R_hue_shift                          +2.3410
  hue_band_R_chroma_change                      +1.0521
  hue_band_R_lightness_change                   -0.4120
  ...

── tone ──
  tone_shadow_L_change                          +0.1200
  tone_shadow_a_change                          +0.0500
  tone_shadow_b_change                          -1.8300   # ← シャドウに青被り
  ...
```

オプション:

```bash
# 色空間を指定して実行
uv run python examples/extract_single.py look.cube --colorspace Rec.709

# Tetrahedral補間を使用
uv run python examples/extract_single.py look.cube --method tetrahedral

# JSONファイルに保存
uv run python examples/extract_single.py look.cube --json output.json
```

### ディレクトリ内のLUTを一括処理する

```bash
uv run python examples/batch_extract.py /path/to/luts/

# 特徴量行列をJSONに保存
uv run python examples/batch_extract.py /path/to/luts/ --out matrix.json
```

---

## 特徴量ベクトルの各次元

全特徴量はCIELAB D65空間で計算されます。**正規化なし**のため、NMFに入力する前に各次元を標準化してください。

### カテゴリ1 — 色相帯別挙動 (18次元)

6つの知覚的色相帯 **R / Y / G / C / B / M** それぞれについて、代表色の近傍サンプルをLUTに通して平均した3指標。

| 次元名のパターン | 説明 | 単位 | identity値 |
|---|---|---|---|
| `hue_band_*_hue_shift` | 色相回転量 Δh° (正 = 反時計回り) | 度 | 0.0 |
| `hue_band_*_chroma_change` | 彩度変化比 C\*_out / C\*_in | 比率 | 1.0 |
| `hue_band_*_lightness_change` | 明度変化 ΔL\* | L\*単位 | 0.0 |

`*` に入るバンド: `R` `Y` `G` `C` `B` `M`

バンド中心 (L\*, C\*, h°):
`R=(50, 60, 30°)` `Y=(80, 60, 90°)` `G=(60, 60, 140°)` `C=(70, 40, 200°)` `B=(40, 50, 280°)` `M=(50, 50, 330°)`

### カテゴリ2 — トーン挙動 (9次元)

無彩色軸 (R=G=B) 上の3点でLUT通過後のLab変化を測定。split toningやカラーグレード独特の色被りを捉えます。

| 次元名 | 説明 | 単位 | identity値 |
|---|---|---|---|
| `tone_shadow_L_change` | シャドウ (L\*≈20) の明度変化 | L\*単位 | 0.0 |
| `tone_shadow_a_change` | シャドウのマゼンタ/グリーン被り | a\*単位 | 0.0 |
| `tone_shadow_b_change` | シャドウのイエロー/ブルー被り | b\*単位 | 0.0 |
| `tone_midtone_*` | ミッドトーン (L\*≈50) の同3指標 | 同上 | 0.0 |
| `tone_highlight_*` | ハイライト (L\*≈80) の同3指標 | 同上 | 0.0 |

**読み方**: `tone_shadow_b_change < 0` なら シャドウに青/シアン被り。`tone_highlight_b_change > 0` ならハイライトに黄/オレンジ被り (split toningの典型パターン)。

### カテゴリ3 — グローバル色調 (4次元)

| 次元名 | 説明 | 単位 | identity値 |
|---|---|---|---|
| `global_temperature_shift` | Planckian locusに沿った移動量 (正 = warm方向) | CIE 1960 UCS (uv) | 0.0 |
| `global_tint_shift` | locusへの垂直方向移動量 (正 = magenta方向) | CIE 1960 UCS (uv) | 0.0 |
| `overall_chroma_multiplier` | 全体的な彩度変化倍率 | 比率 | 1.0 |
| `overall_contrast` | 出力L\*レンジ / 入力L\*レンジ | 比率 | 1.0 |

### カテゴリ4 — 輝度依存hue shift (6次元)

各色相帯について「明部のhue shift − 暗部のhue shift」を計算。3D LUTならではの、輝度によって色相回転が変わる挙動を捉えます。

| 次元名 | 説明 | 単位 | identity値 |
|---|---|---|---|
| `lum_dep_hue_shift_R/Y/G/C/B/M` | ハイライト − シャドウのhue shift差 | 度 | 0.0 |

### カテゴリ5 — 非線形性指標 (3次元)

| 次元名 | 説明 | 単位 | identity値 |
|---|---|---|---|
| `tone_curve_nonlinearity` | L\*_out の線形フィット残差RMSE | L\*単位 | 0.0 |
| `hue_rotation_variance` | 6バンドのhue shiftの分散 | 度² | 0.0 |
| `chroma_response_nonlinearity` | C\*_out の線形フィット残差RMSE | C\*単位 | 0.0 |

---

## テスト・型チェック

```bash
# テスト実行
uv run pytest

# 詳細表示
uv run pytest -v

# カバレッジ付き
uv run pytest --cov=lut_features

# 型チェック (strict mode)
uv run mypy src/

# テスト用フィクスチャLUTを再生成する場合
uv run python tests/generate_fixtures.py
```

---

## エラーハンドリング

本モジュールはstrictモードで動作します。問題のあるファイルは即座に例外を送出します。

```python
from lut_features import LUTFeatureExtractor, CubeParseError

extractor = LUTFeatureExtractor()

try:
    features = extractor.extract("bad_file.cube")
except FileNotFoundError:
    print("ファイルが見つかりません")
except CubeParseError as e:
    print(f"LUTファイルの形式が不正です: {e}")
```

---

## 既知の制約

- **3D LUTのみ対応**: 1D `.cube` LUTは `CubeParseError` を送出します。
- **対応色空間**: `sRGB` と `Rec.709` のみ。`DaVinci Wide Gamut Intermediate` と `ACEScct` は `NotImplementedError` を送出します (将来実装予定)。
- **推奨LUTサイズ**: 17×17×17以上。それ以下では補間誤差が特徴量に影響します。
- **Temperature/tint近似**: Planckian locus探索にKang et al. 2002の多項式近似を使用。1667K〜25000Kの範囲外は精度が低下します。
- **正規化なし**: 出力は全て物理単位のraw値です。NMFに入力する前に標準化 (例: `sklearn.preprocessing.StandardScaler`) を行ってください。
