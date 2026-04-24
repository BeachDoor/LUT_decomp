import { useRef, useEffect, useState } from "react";
import { useFeatureData } from "../hooks/useFeatureData";
import { useProjection } from "../hooks/useProjection";
import { useUrlState } from "../hooks/useUrlState";
import { useAppStore } from "../store/useAppStore";
import { Header } from "./Header";
import { ControlBar } from "./scatter/ControlBar";
import { ScatterPlot } from "./scatter/ScatterPlot";
import { ThumbnailStrip } from "./ThumbnailStrip";
import { RadarGrid } from "./radar/RadarGrid";

export function AppShell() {
  const { loading } = useFeatureData();
  useProjection();
  useUrlState();

  const theme = useAppStore((s) => s.theme);
  const exportRef = useRef<HTMLDivElement>(null);
  const [dims, setDims] = useState({ scatterW: 0, scatterH: 0 });
  const scatterContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  useEffect(() => {
    if (!scatterContainerRef.current) return;
    const ro = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry) {
        setDims({
          scatterW: Math.floor(entry.contentRect.width),
          scatterH: Math.floor(entry.contentRect.height),
        });
      }
    });
    ro.observe(scatterContainerRef.current);
    return () => ro.disconnect();
  }, []);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center text-[var(--color-muted)] font-mono text-sm">
        Loading features.json…
      </div>
    );
  }

  return (
    // Mobile: natural document flow (vertical scroll)
    // Desktop (lg): fixed viewport height, internal scroll only
    <div className="flex flex-col lg:h-screen lg:overflow-hidden">

      {/* Header — sticky on mobile */}
      <div className="sticky top-0 z-40 lg:static shrink-0">
        <Header exportTargetRef={exportRef} />
      </div>

      {/* Thumbnail strip — desktop only, top position */}
      <div className="hidden lg:block shrink-0">
        <ThumbnailStrip />
      </div>

      {/* ControlBar */}
      <div className="shrink-0">
        <ControlBar />
      </div>

      {/* Main area: flex-1 fills remaining viewport height on desktop */}
      <div
        ref={exportRef}
        // Desktop: horizontal 2-pane, fixed height (min-h-0 is critical for nested flex)
        // Mobile: vertical stack, natural height
        className="flex flex-col lg:flex-row lg:flex-1 lg:min-h-0 lg:overflow-hidden"
      >
        {/* Scatter pane */}
        <div
          // Desktop: fill width minus radar; min-h-0 allows the flex-col children to shrink
          // Mobile: natural width, natural height
          className="flex flex-col lg:flex-1 lg:min-w-0 lg:min-h-0 lg:border-r border-[var(--color-border)]"
        >
          <div
            ref={scatterContainerRef}
            // Mobile: 50vh fixed height
            // Desktop: flex-1 fills remaining; min-h-0 prevents overflow
            className="h-[50vh] lg:flex-1 lg:min-h-0 bg-[var(--color-bg)] overflow-hidden"
          >
            {dims.scatterW > 0 && dims.scatterH > 0 && (
              <ScatterPlot width={dims.scatterW} height={dims.scatterH} />
            )}
          </div>
        </div>

        {/* Thumbnail strip — mobile only, between scatter and radar */}
        <div className="lg:hidden shrink-0">
          <ThumbnailStrip />
        </div>

        {/* Radar pane */}
        <div className="lg:w-[480px] lg:shrink-0 lg:min-h-0 lg:overflow-hidden bg-[var(--color-bg)]">
          <RadarGrid />
        </div>
      </div>
    </div>
  );
}
