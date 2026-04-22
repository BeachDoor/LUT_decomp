import { describe, it, expect } from "vitest";
import { normalizeFeature, buildRadarData } from "../../src/lib/normalize";
import type { FeatureDefinition, LutEntry } from "../../src/types/features";

const mockFeature = (
  id: string,
  lo: number,
  hi: number,
  neutral = 0
): FeatureDefinition => ({
  id,
  label: id,
  unit: "",
  category: "test",
  neutral_value: neutral,
  typical_range: [lo, hi],
});

describe("normalizeFeature", () => {
  it("maps midpoint to 0.5", () => {
    const f = mockFeature("f", -10, 10);
    expect(normalizeFeature(0, f)).toBeCloseTo(0.5);
  });

  it("clamps below range to 0", () => {
    const f = mockFeature("f", 0, 1);
    expect(normalizeFeature(-5, f)).toBe(0);
  });

  it("clamps above range to 1", () => {
    const f = mockFeature("f", 0, 1);
    expect(normalizeFeature(5, f)).toBe(1);
  });
});

describe("buildRadarData", () => {
  const features = [mockFeature("f1", 0, 10), mockFeature("f2", 0, 100)];
  const luts: LutEntry[] = [
    {
      id: "lut_a",
      name: "A",
      source_path: "",
      thumbnail_path: "",
      features: { f1: 5, f2: 50 },
    },
  ];

  it("returns one entry per feature id", () => {
    const data = buildRadarData(["f1", "f2"], features, luts);
    expect(data).toHaveLength(2);
  });

  it("normalizes values correctly", () => {
    const data = buildRadarData(["f1"], features, luts);
    expect(data[0]["lut_a"]).toBeCloseTo(0.5);
  });
});
