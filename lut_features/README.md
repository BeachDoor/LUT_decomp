# lut-features

LUT feature extraction module for photo/video grading pipelines.

Converts `.cube` 3D LUT files into ~40-dimensional perceptual feature vectors described in CIELAB space. These vectors are designed as input for downstream NMF-based look decomposition.

## Installation

```bash
git clone <repo>
cd lut_features
uv sync
```

For development (includes pytest, mypy):

```bash
uv sync --dev
```

## Basic Usage

```python
from lut_features import LUTFeatureExtractor, InputColorSpace

extractor = LUTFeatureExtractor(
    input_colorspace=InputColorSpace.SRGB,   # sRGB | Rec.709
    interpolation="trilinear",               # trilinear | tetrahedral
)

# Single LUT
features = extractor.extract("path/to/look.cube")
print(features.vector.shape)      # (40,)
print(features.feature_names)
print(features.to_json())

# Batch processing → feature matrix for NMF
paths = ["lut1.cube", "lut2.cube", "lut3.cube"]
matrix = extractor.feature_matrix(paths)   # shape (3, 40)

# Serialise
LUTFeatureExtractor.save_json(features, "features.json")
features2 = LUTFeatureExtractor.load_json("features.json")
```

### CLI example

```bash
uv run python examples/extract_single.py path/to/look.cube
uv run python examples/extract_single.py path/to/look.cube --colorspace Rec.709 --method tetrahedral --json out.json

uv run python examples/batch_extract.py /path/to/luts/ --out matrix.json
```

## Feature Vector (40 dimensions)

All features are computed in CIELAB D65 space. No normalisation is applied; downstream components are expected to standardise before NMF.

### Category 1 – Hue-band behaviour (18 dimensions)

For each of 6 perceptual hue bands **R / Y / G / C / B / M**, three metrics are computed by applying the LUT to a set of representative colours around the band centre.

| Suffix | Description | Unit | Identity value |
|--------|-------------|------|----------------|
| `_hue_shift` | Circular Δh° (positive = CCW rotation) | degrees | 0.0 |
| `_chroma_change` | C\*_out / C\*_in ratio | ratio | 1.0 |
| `_lightness_change` | ΔL\* (positive = brighter) | L\* units | 0.0 |

Band centres in LCh (L\*, C\*, h°): R=(50,60,30°) Y=(80,60,90°) G=(60,60,140°) C=(70,40,200°) B=(40,50,280°) M=(50,50,330°).

### Category 2 – Tone behaviour (9 dimensions)

Neutral-axis (R=G=B) patches at three luminance zones, measuring colour-cast introduced by the LUT.

| Feature | Description | Unit |
|---------|-------------|------|
| `tone_shadow_L/a/b_change` | ΔL\*, Δa\*, Δb\* at L\*=20 | Lab units |
| `tone_midtone_L/a/b_change` | ΔL\*, Δa\*, Δb\* at L\*=50 | Lab units |
| `tone_highlight_L/a/b_change` | ΔL\*, Δa\*, Δb\* at L\*=80 | Lab units |

Δa\* ≈ magenta/green cast; Δb\* ≈ yellow/blue cast (split-toning visible here).

### Category 3 – Global colour tone (4 dimensions)

| Feature | Description | Unit | Identity value |
|---------|-------------|------|----------------|
| `global_temperature_shift` | Shift along the Planckian locus in CIE 1960 UCS | uv | 0.0 |
| `global_tint_shift` | Shift perpendicular to the locus (green↔magenta) | uv | 0.0 |
| `overall_chroma_multiplier` | Mean C\*_out / C\*_in across all sampled colours | ratio | 1.0 |
| `overall_contrast` | L\* output range / input range on neutral axis | ratio | 1.0 |

### Category 4 – Luminance-dependent hue shift (6 dimensions)

For each of the 6 hue bands: `highlight_hue_shift − shadow_hue_shift`. A non-zero value reveals luminance-dependent hue rotation unique to 3D LUTs.

| Feature | Description | Unit | Identity value |
|---------|-------------|------|----------------|
| `lum_dep_hue_shift_R/Y/G/C/B/M` | Δ(hue shift) across lightness | degrees | 0.0 |

### Category 5 – Non-linearity indicators (3 dimensions)

| Feature | Description | Unit | Identity value |
|---------|-------------|------|----------------|
| `tone_curve_nonlinearity` | RMSE of L\*_out residuals vs linear fit | L\* units | 0.0 |
| `hue_rotation_variance` | Variance of per-band hue shifts | deg² | 0.0 |
| `chroma_response_nonlinearity` | RMSE of C\*_out residuals vs linear fit | C\* units | 0.0 |

## Running Tests

```bash
uv run pytest
uv run pytest -v                # verbose
uv run pytest --cov=lut_features  # with coverage
```

## Type Checking

```bash
uv run mypy src/
```

## Known Constraints

- **3D LUT only**: 1D `.cube` LUTs raise `CubeParseError`.
- **Supported colour spaces**: `sRGB` and `Rec.709`. `DaVinci Wide Gamut Intermediate` and `ACEScct` raise `NotImplementedError`.
- **LUT sizes**: 2–256. Smaller LUTs (< 17) introduce interpolation noise in features.
- **Temperature/tint approximation**: The Planckian locus search uses a polynomial approximation (Kang et al. 2002); very low/high CCT values may be less accurate.
- **No output normalisation**: Feature values are in physical units. Standardise before feeding to NMF.
