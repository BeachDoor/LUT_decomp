import { describe, it, expect } from "vitest";
import {
  getSelectionColor,
  getLutColor,
  SELECTION_COLORS,
} from "../../src/lib/colormap";

describe("getSelectionColor", () => {
  it("returns first color for index 0", () => {
    expect(getSelectionColor(0)).toBe(SELECTION_COLORS[0]);
  });

  it("wraps around for out-of-range index", () => {
    expect(getSelectionColor(SELECTION_COLORS.length)).toBe(SELECTION_COLORS[0]);
  });
});

describe("getLutColor", () => {
  const selected = ["lut_a", "lut_b", "lut_c"];

  it("returns color for a selected LUT", () => {
    expect(getLutColor("lut_a", selected)).toBe(SELECTION_COLORS[0]);
    expect(getLutColor("lut_b", selected)).toBe(SELECTION_COLORS[1]);
  });

  it("returns null for unselected LUT", () => {
    expect(getLutColor("lut_z", selected)).toBeNull();
  });

  it("returns null for empty selection", () => {
    expect(getLutColor("lut_a", [])).toBeNull();
  });
});
