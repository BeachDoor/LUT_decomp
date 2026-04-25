const WATERMARK = "LUT Interpreter";

/**
 * Export an HTML element as a PNG blob by rendering onto a canvas.
 * Adds a watermark in the bottom-right corner.
 */
export async function exportAsPng(
  element: HTMLElement,
  filename = "lut-interpreter-export.png"
): Promise<void> {
  // Dynamic import to keep bundle lean
  const { toPng } = await import("html-to-image");
  const dataUrl = await toPng(element, {
    backgroundColor: "#1a1a2e",
    filter: (node) => {
      // Exclude export button itself from capture
      if (node instanceof HTMLElement && node.dataset["exportExclude"]) {
        return false;
      }
      return true;
    },
  });

  // Draw watermark on canvas
  const img = new Image();
  img.src = dataUrl;
  await new Promise<void>((res) => (img.onload = () => res()));

  const canvas = document.createElement("canvas");
  canvas.width = img.width;
  canvas.height = img.height;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  ctx.drawImage(img, 0, 0);

  // Watermark
  const fontSize = Math.max(12, img.width / 60);
  ctx.font = `${fontSize}px monospace`;
  ctx.fillStyle = "rgba(255, 255, 255, 0.35)";
  ctx.textAlign = "right";
  ctx.textBaseline = "bottom";
  ctx.fillText(WATERMARK, img.width - 12, img.height - 10);

  canvas.toBlob((blob) => {
    if (!blob) return;
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }, "image/png");
}

/**
 * Export an SVG element as an SVG file with watermark text appended.
 */
export function exportAsSvg(
  svgElement: SVGSVGElement,
  filename = "lut-interpreter-export.svg"
): void {
  const clone = svgElement.cloneNode(true) as SVGSVGElement;

  // Append watermark text
  const width = parseFloat(svgElement.getAttribute("width") ?? "800");
  const height = parseFloat(svgElement.getAttribute("height") ?? "600");
  const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
  text.setAttribute("x", String(width - 10));
  text.setAttribute("y", String(height - 8));
  text.setAttribute("text-anchor", "end");
  text.setAttribute("font-size", "12");
  text.setAttribute("font-family", "monospace");
  text.setAttribute("fill", "rgba(255,255,255,0.35)");
  text.textContent = WATERMARK;
  clone.appendChild(text);

  const blob = new Blob([new XMLSerializer().serializeToString(clone)], {
    type: "image/svg+xml",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
