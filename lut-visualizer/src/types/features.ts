export interface FeatureDefinition {
  id: string;
  label: string;
  unit: string;
  category: string;
  neutral_value: number;
  typical_range: [number, number];
}

export interface CategoryDefinition {
  id: string;
  label: string;
  feature_ids: string[];
}

export interface FeatureSchema {
  categories: CategoryDefinition[];
  features: FeatureDefinition[];
}

export interface LutEntry {
  id: string;
  name: string;
  source_path: string;
  features: Record<string, number>;
  thumbnail_path: string;
}

export interface FeaturesPayload {
  schema_version: string;
  generated_at: string;
  feature_schema: FeatureSchema;
  luts: LutEntry[];
}

export type ProjectionMethod = "pca" | "umap";
export type ProjectionStatus = "idle" | "computing" | "done" | "error";
export type Theme = "light" | "dark";

export interface Point2D {
  x: number;
  y: number;
}
