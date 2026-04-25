import { describe, it, expect } from "vitest";
import { computePCA } from "../../src/lib/projection/pca";

describe("computePCA", () => {
  it("returns n × 2 result", () => {
    const matrix = Array.from({ length: 10 }, (_, i) =>
      Array.from({ length: 5 }, (__, j) => i * j + Math.random() * 0.001)
    );
    const result = computePCA(matrix);
    expect(result).toHaveLength(10);
    expect(result[0]).toHaveLength(2);
  });

  it("is deterministic on the same input", () => {
    const matrix = [
      [1, 2, 3],
      [4, 5, 6],
      [7, 8, 9],
      [1, 3, 2],
      [9, 1, 4],
    ];
    const r1 = computePCA(matrix);
    const r2 = computePCA(matrix);
    for (let i = 0; i < r1.length; i++) {
      expect(r1[i][0]).toBeCloseTo(r2[i][0], 10);
      expect(r1[i][1]).toBeCloseTo(r2[i][1], 10);
    }
  });

  it("identity LUT projects to origin after centering", () => {
    // All-same rows → all project to (0, 0)
    const matrix = Array.from({ length: 5 }, () => [1, 2, 3, 4, 5]);
    const result = computePCA(matrix);
    for (const [x, y] of result) {
      expect(Math.abs(x)).toBeLessThan(1e-8);
      expect(Math.abs(y)).toBeLessThan(1e-8);
    }
  });

  it("warm vs cool LUTs separate on first PC", () => {
    // Warm: high R features; Cool: high B features
    const warmRow = [10, 0, 0, 0, 0]; // warm
    const coolRow = [0, 0, 0, 0, 10]; // cool
    const matrix = [warmRow, coolRow, warmRow, coolRow];
    const result = computePCA(matrix);
    // Warm and cool should have opposite signs on PC1
    const warmX = result[0][0];
    const coolX = result[1][0];
    expect(warmX * coolX).toBeLessThan(0);
  });
});
