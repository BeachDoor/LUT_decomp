/** Palette for up to 4 simultaneously selected LUTs (accessible, high-contrast). */
export const SELECTION_COLORS = [
  "#f97316", // orange
  "#3b82f6", // blue
  "#22c55e", // green
  "#a855f7", // purple
] as const;

/** Category accent colors (matches radar chart fills). */
export const CATEGORY_COLORS: Record<string, string> = {
  hue_bands: "#f97316",
  tone: "#3b82f6",
  global_tone: "#22c55e",
  luminance_dependent: "#a855f7",
  nonlinearity: "#ec4899",
};

export function getSelectionColor(index: number): string {
  return SELECTION_COLORS[index % SELECTION_COLORS.length];
}

/** Returns the color for a LUT given the current selection array. */
export function getLutColor(
  lutId: string,
  selectedIds: string[]
): string | null {
  const idx = selectedIds.indexOf(lutId);
  return idx >= 0 ? SELECTION_COLORS[idx] : null;
}
