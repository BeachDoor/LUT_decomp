import { describe, it, expect } from "vitest";

// Isolated URL encode/decode logic extracted for testing
function encodeState(ids: string[], method: string): string {
  const params = new URLSearchParams();
  if (ids.length > 0) params.set("sel", ids.join(","));
  if (method !== "pca") params.set("proj", method);
  return params.toString();
}

function decodeState(search: string): { ids: string[]; method: string } {
  const params = new URLSearchParams(search);
  const ids = params.get("sel")?.split(",").filter(Boolean) ?? [];
  const method = params.get("proj") ?? "pca";
  return { ids, method };
}

describe("URL state encode/decode", () => {
  it("encodes selected IDs", () => {
    const qs = encodeState(["lut_a", "lut_b"], "pca");
    expect(qs).toContain("sel=lut_a%2Clut_b");
  });

  it("omits proj param for default method", () => {
    const qs = encodeState(["lut_a"], "pca");
    expect(qs).not.toContain("proj");
  });

  it("includes proj param for non-default method", () => {
    const qs = encodeState([], "umap");
    expect(qs).toContain("proj=umap");
  });

  it("round-trips selection IDs", () => {
    const ids = ["cinematic_orange_teal", "warm_strong", "cool_grade"];
    const qs = encodeState(ids, "pca");
    const decoded = decodeState(qs);
    expect(decoded.ids).toEqual(ids);
  });

  it("defaults method to pca when not in URL", () => {
    const decoded = decodeState("sel=lut_a");
    expect(decoded.method).toBe("pca");
  });

  it("returns empty IDs for empty query string", () => {
    const decoded = decodeState("");
    expect(decoded.ids).toEqual([]);
    expect(decoded.method).toBe("pca");
  });
});
