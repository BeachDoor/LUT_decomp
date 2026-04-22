import { useEffect, useRef } from "react";
import { useAppStore } from "../store/useAppStore";
import { computePCA } from "../lib/projection/pca";
import type { Point2D } from "../types/features";

export function useProjection() {
  const payload = useAppStore((s) => s.payload);
  const method = useAppStore((s) => s.method);
  const projectedPoints = useAppStore((s) => s.projectedPoints);
  const setProjectedPoints = useAppStore((s) => s.setProjectedPoints);
  const setProjectionStatus = useAppStore((s) => s.setProjectionStatus);
  const workerRef = useRef<Worker | null>(null);

  useEffect(() => {
    if (!payload || projectedPoints !== null) return;

    const ids = payload.luts.map((l) => l.id);
    const featureNames = payload.feature_schema.features.map((f) => f.id);
    const matrix = payload.luts.map((l) =>
      featureNames.map((fid) => l.features[fid] ?? 0)
    );

    if (method === "pca") {
      setProjectionStatus("computing");
      try {
        const coords = computePCA(matrix);
        const pts: Record<string, Point2D> = {};
        ids.forEach((id, i) => {
          pts[id] = { x: coords[i][0], y: coords[i][1] };
        });
        setProjectedPoints(pts);
      } catch {
        setProjectionStatus("error");
      }
      return;
    }

    // UMAP via web worker
    setProjectionStatus("computing");
    const worker = new Worker(
      new URL("../workers/umap.worker.ts", import.meta.url),
      { type: "module" }
    );
    workerRef.current = worker;

    worker.onmessage = (e: MessageEvent<{ embedding: number[][] }>) => {
      const pts: Record<string, Point2D> = {};
      ids.forEach((id, i) => {
        pts[id] = { x: e.data.embedding[i][0], y: e.data.embedding[i][1] };
      });
      setProjectedPoints(pts);
      worker.terminate();
    };

    worker.onerror = () => {
      setProjectionStatus("error");
      worker.terminate();
    };

    worker.postMessage({ matrix, nNeighbors: Math.min(10, ids.length - 1) });

    return () => {
      worker.terminate();
    };
  }, [payload, method, projectedPoints, setProjectedPoints, setProjectionStatus]);
}
