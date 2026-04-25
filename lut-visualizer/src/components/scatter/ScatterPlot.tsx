import { useRef, useEffect, useState } from "react";
import * as d3 from "d3";
import { useAppStore } from "../../store/useAppStore";
import { Tooltip } from "./Tooltip";
import { getLutColor, SELECTION_COLORS } from "../../lib/colormap";
import type { LutEntry, FeatureDefinition } from "../../types/features";

interface ScatterPlotProps {
  width: number;
  height: number;
}

const MARGIN = { top: 24, right: 24, bottom: 24, left: 24 };
const DOT_R = 7;

export function ScatterPlot({ width, height }: ScatterPlotProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const zoomRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null);
  const [transform, setTransform] = useState<d3.ZoomTransform>(d3.zoomIdentity);
  const [tooltip, setTooltip] = useState<{
    lut: LutEntry;
    x: number;
    y: number;
  } | null>(null);

  const payload = useAppStore((s) => s.payload);
  const projectedPoints = useAppStore((s) => s.projectedPoints);
  const projectionStatus = useAppStore((s) => s.projectionStatus);
  const selectedIds = useAppStore((s) => s.selectedIds);
  const hoveredId = useAppStore((s) => s.hoveredId);
  const toggleSelected = useAppStore((s) => s.toggleSelected);
  const setHoveredId = useAppStore((s) => s.setHoveredId);

  const features: FeatureDefinition[] =
    payload?.feature_schema.features ?? [];

  // Set up zoom
  useEffect(() => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.3, 12])
      .on("zoom", (event: d3.D3ZoomEvent<SVGSVGElement, unknown>) => {
        setTransform(event.transform);
      });
    zoomRef.current = zoom;
    svg.call(zoom);
    return () => {
      svg.on(".zoom", null);
    };
  }, []);

  const handleReset = () => {
    if (!svgRef.current || !zoomRef.current) return;
    d3.select(svgRef.current)
      .transition()
      .duration(400)
      .call(zoomRef.current.transform, d3.zoomIdentity);
  };

  if (!projectedPoints || !payload) {
    return (
      <div
        className="flex items-center justify-center text-[var(--color-muted)] font-mono text-xs"
        style={{ width, height }}
      >
        {projectionStatus === "computing"
          ? "Projecting…"
          : projectionStatus === "error"
            ? "Projection failed"
            : "Loading…"}
      </div>
    );
  }

  const luts = payload.luts;
  const pts = luts.map((l) => projectedPoints[l.id]).filter(Boolean);

  const xExtent = d3.extent(pts, (d) => d.x) as [number, number];
  const yExtent = d3.extent(pts, (d) => d.y) as [number, number];

  const xPad = (xExtent[1] - xExtent[0]) * 0.15 || 1;
  const yPad = (yExtent[1] - yExtent[0]) * 0.15 || 1;

  const xScale = d3
    .scaleLinear()
    .domain([xExtent[0] - xPad, xExtent[1] + xPad])
    .range([MARGIN.left, width - MARGIN.right]);
  const yScale = d3
    .scaleLinear()
    .domain([yExtent[0] - yPad, yExtent[1] + yPad])
    .range([height - MARGIN.bottom, MARGIN.top]);

  // Apply current zoom transform
  const tx = transform.x;
  const ty = transform.y;
  const tk = transform.k;
  const cx = (x: number) => tx + xScale(x) * tk;
  const cy = (y: number) => ty + yScale(y) * tk;

  return (
    <div className="relative" style={{ width, height }}>
      <svg
        ref={svgRef}
        width={width}
        height={height}
        className="cursor-crosshair select-none"
      >
        {/* Grid lines */}
        <g opacity={0.12}>
          {[0.2, 0.4, 0.6, 0.8].map((t) => {
            const xVal = xExtent[0] - xPad + (xExtent[1] + 2 * xPad - (xExtent[0] - xPad)) * t;
            const yVal = yExtent[0] - yPad + (yExtent[1] + 2 * yPad - (yExtent[0] - yPad)) * t;
            return (
              <g key={t}>
                <line
                  x1={cx(xVal)} y1={MARGIN.top}
                  x2={cx(xVal)} y2={height - MARGIN.bottom}
                  stroke="currentColor" strokeWidth={1}
                />
                <line
                  x1={MARGIN.left} y1={cy(yVal)}
                  x2={width - MARGIN.right} y2={cy(yVal)}
                  stroke="currentColor" strokeWidth={1}
                />
              </g>
            );
          })}
        </g>

        {/* Dots and labels */}
        <g>
          {luts.map((lut) => {
            const pt = projectedPoints[lut.id];
            if (!pt) return null;
            const px = cx(pt.x);
            const py = cy(pt.y);
            const selColor = getLutColor(lut.id, selectedIds);
            const isHovered = lut.id === hoveredId;
            const isSelected = selColor !== null;
            const selIdx = selectedIds.indexOf(lut.id);

            return (
              <g
                key={lut.id}
                transform={`translate(${px},${py})`}
                style={{ cursor: "pointer" }}
                onMouseEnter={(e) => {
                  setHoveredId(lut.id);
                  setTooltip({ lut, x: e.clientX, y: e.clientY });
                }}
                onMouseMove={(e) => {
                  setTooltip((t) => (t ? { ...t, x: e.clientX, y: e.clientY } : null));
                }}
                onMouseLeave={() => {
                  setHoveredId(null);
                  setTooltip(null);
                }}
                onClick={() => toggleSelected(lut.id)}
              >
                <circle
                  r={isHovered || isSelected ? DOT_R + 2 : DOT_R}
                  fill={selColor ?? "var(--color-muted)"}
                  fillOpacity={isSelected ? 0.85 : 0.45}
                  stroke={isSelected ? selColor : isHovered ? "#fff" : "none"}
                  strokeWidth={isSelected ? 2 : 1.5}
                />
                {isSelected && (
                  <text
                    dy={-DOT_R - 4}
                    textAnchor="middle"
                    fontSize={9}
                    fontFamily="monospace"
                    fill={SELECTION_COLORS[selIdx]}
                  >
                    {selIdx + 1}
                  </text>
                )}
                {(isHovered || isSelected) && (
                  <text
                    dy={DOT_R + 12}
                    textAnchor="middle"
                    fontSize={9}
                    fontFamily="monospace"
                    fill={selColor ?? "#fff"}
                    opacity={0.85}
                  >
                    {lut.name}
                  </text>
                )}
              </g>
            );
          })}
        </g>
      </svg>

      {/* Reset zoom button */}
      <button
        onClick={handleReset}
        className="absolute bottom-3 right-3 px-2 py-1 text-[10px] font-mono rounded
                   border border-[var(--color-border)] bg-[var(--color-surface)]
                   hover:border-orange-500 hover:text-orange-400 transition-colors"
      >
        Reset
      </button>

      {tooltip && (
        <Tooltip
          lut={tooltip.lut}
          features={features}
          x={tooltip.x}
          y={tooltip.y}
        />
      )}
    </div>
  );
}
