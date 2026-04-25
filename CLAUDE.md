# CLAUDE.md

## Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Stable production code |
| `develop` | Integration branch; merged into from feature branches |
| `claude/lut-feature-extraction-w5YgY` | Active development branch for LUT feature extraction |

Development happens on `claude/lut-feature-extraction-w5YgY`. At the end of each implementation phase, changes are merged into `develop` via fast-forward or merge commit.

Never push directly to `main` or `develop`; always merge from a feature branch.

## Python Environment

**Use `uv` exclusively for all Python environment management. Do not use `pip` directly.**

### Setup

```bash
cd lut_features
uv sync              # install all dependencies
uv sync --dev        # includes dev dependencies (pytest, mypy)
```

### Running tests

```bash
uv run pytest
```

### Type checking

```bash
uv run mypy src/
```

### Adding dependencies

```bash
uv add <package>
uv add --dev <package>   # dev-only
```

### Running examples

```bash
uv run python examples/extract_single.py path/to/lut.cube
```

## Design Decisions

- **Normalization**: Feature values are output as raw physical units (degrees, ratios, Lab units). No normalization. Downstream NMF module is responsible for scaling.
- **Error handling**: Strict mode. Invalid `.cube` files raise `CubeParseError` immediately. No silent fallbacks.
- **Color space**: All feature computation is performed in CIELAB (D65). Input RGB is decoded via the specified colorspace's EOTF before conversion.
- **Out-of-gamut handling**: Input RGB values outside `[domain_min, domain_max]` are clamped before LUT interpolation. Out-of-gamut colors generated during feature sample synthesis have their chroma reduced iteratively until in-gamut.
