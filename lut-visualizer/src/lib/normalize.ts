import type { FeatureDefinition, LutEntry } from "../types/features";

/**
 * Normalize a feature value to [0, 1] using the feature's typical_range.
 * Values outside the range are clamped.
 */
export function normalizeFeature(
  value: number,
  feature: FeatureDefinition
): number {
  const [lo, hi] = feature.typical_range;
  if (hi === lo) return 0.5;
  return Math.max(0, Math.min(1, (value - lo) / (hi - lo)));
}

/**
 * Build radar chart data for a set of features and LUTs.
 * Returns an array of { subject, ...lutId } objects.
 */
export function buildRadarData(
  featureIds: string[],
  features: FeatureDefinition[],
  luts: LutEntry[]
): Record<string, string | number>[] {
  const featureMap = new Map(features.map((f) => [f.id, f]));

  return featureIds.map((fid) => {
    const fDef = featureMap.get(fid);
    const row: Record<string, string | number> = {
      subject: fDef?.label ?? fid,
      fullMark: 1,
    };
    for (const lut of luts) {
      const raw = lut.features[fid] ?? 0;
      row[lut.id] = fDef ? normalizeFeature(raw, fDef) : 0;
    }
    return row;
  });
}

/**
 * Normalize a feature matrix (n_luts × n_features) column-wise to [0, 1]
 * using each feature's typical_range. Used before PCA/UMAP projection.
 */
export function normalizeMatrix(
  matrix: number[][],
  features: FeatureDefinition[]
): number[][] {
  return matrix.map((row) =>
    row.map((val, j) => normalizeFeature(val, features[j]))
  );
}
