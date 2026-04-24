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
    // Desktop: fixed-height column (no scroll)
    // Mobile: natural document flow (vertical scroll)
    <div className="flex flex-col lg:h-screen lg:overflow-hidden">

      {/* Header — sticky on mobile so it stays visible while scrolling */}
      <div className="sticky top-0 z-40 lg:static shrink-0">
        <Header exportTargetRef={exportRef} />
      </div>

      {/* Thumbnail strip — desktop only, sits between header and main panes */}
      <div className="hidden lg:block shrink-0">
        <ThumbnailStrip />
      </div>

      {/* Main content area */}
      <div ref={exportRef} className="flex flex-col lg:flex-row lg:flex-1 lg:overflow-hidden">

        {/* Scatter pane */}
        <div className="flex flex-col lg:flex-1 lg:min-w-0 lg:border-r border-[var(--color-border)]">
          <ControlBar />
          {/* Mobile: 50vh fixed; Desktop: flex-1 fills remaining space */}
          <div
            ref={scatterContainerRef}
            className="h-[50vh] lg:h-auto lg:flex-1 bg-[var(--color-bg)] overflow-hidden"
          >
            {dims.scatterW > 0 && (
              <ScatterPlot width={dims.scatterW} height={dims.scatterH} />
            )}
          </div>
        </div>

        {/* Thumbnail strip — mobile only, between scatter and radar */}
        <div className="lg:hidden shrink-0">
          <ThumbnailStrip />
        </div>

        {/* Radar pane */}
        <div className="lg:w-[480px] lg:shrink-0 lg:overflow-hidden bg-[var(--color-bg)]">
          <RadarGrid />
        </div>
      </div>
    </div>
  );
}
