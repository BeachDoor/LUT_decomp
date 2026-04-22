import { useRef, useEffect, useState } from "react";
import { useFeatureData } from "../hooks/useFeatureData";
import { useProjection } from "../hooks/useProjection";
import { useUrlState } from "../hooks/useUrlState";
import { useAppStore } from "../store/useAppStore";
import { Header } from "./Header";
import { ControlBar } from "./scatter/ControlBar";
import { ScatterPlot } from "./scatter/ScatterPlot";
import { DetailPanel } from "./scatter/DetailPanel";
import { RadarGrid } from "./radar/RadarGrid";

export function AppShell() {
  const { loading } = useFeatureData();
  useProjection();
  useUrlState();

  const theme = useAppStore((s) => s.theme);
  const exportRef = useRef<HTMLDivElement>(null);
  const [dims, setDims] = useState({ scatterW: 600, scatterH: 420 });
  const scatterContainerRef = useRef<HTMLDivElement>(null);

  // Apply theme class to <html>
  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  // Measure scatter container
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
    <div className="flex flex-col h-screen overflow-hidden">
      <Header exportTargetRef={exportRef} />

      <div ref={exportRef} className="flex flex-1 overflow-hidden">
        {/* Left pane — scatter plot */}
        <div className="flex flex-col flex-1 min-w-0 border-r border-[var(--color-border)]">
          <ControlBar />
          <div
            ref={scatterContainerRef}
            className="flex-1 bg-[var(--color-bg)] overflow-hidden"
          >
            {dims.scatterW > 0 && (
              <ScatterPlot width={dims.scatterW} height={dims.scatterH} />
            )}
          </div>
          <DetailPanel />
        </div>

        {/* Right pane — radar charts */}
        <div className="flex flex-col w-[480px] shrink-0 bg-[var(--color-bg)]">
          <RadarGrid />
        </div>
      </div>
    </div>
  );
}
