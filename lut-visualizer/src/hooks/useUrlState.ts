import { useEffect, useRef } from "react";
import { useAppStore } from "../store/useAppStore";
import type { ProjectionMethod } from "../types/features";

function encodeState(ids: string[], method: ProjectionMethod): string {
  const params = new URLSearchParams();
  if (ids.length > 0) params.set("sel", ids.join(","));
  if (method !== "pca") params.set("proj", method);
  return params.toString();
}

function decodeState(search: string): {
  ids: string[];
  method: ProjectionMethod;
} {
  const params = new URLSearchParams(search);
  const ids = params.get("sel")?.split(",").filter(Boolean) ?? [];
  const method = (params.get("proj") ?? "pca") as ProjectionMethod;
  return { ids, method };
}

export function useUrlState() {
  const selectedIds = useAppStore((s) => s.selectedIds);
  const method = useAppStore((s) => s.method);
  const setSelectedIds = useAppStore((s) => s.setSelectedIds);
  const setMethod = useAppStore((s) => s.setMethod);
  const payload = useAppStore((s) => s.payload);
  const initDone = useRef(false);

  // On first data load, restore state from URL
  useEffect(() => {
    if (!payload || initDone.current) return;
    initDone.current = true;
    const { ids, method: m } = decodeState(window.location.search);
    const validIds = ids.filter((id) => payload.luts.some((l) => l.id === id));
    if (validIds.length > 0) setSelectedIds(validIds);
    if (m !== "pca") setMethod(m);
  }, [payload, setSelectedIds, setMethod]);

  // Sync state → URL
  useEffect(() => {
    if (!initDone.current) return;
    const qs = encodeState(selectedIds, method);
    const newUrl = qs
      ? `${window.location.pathname}?${qs}`
      : window.location.pathname;
    window.history.replaceState(null, "", newUrl);
  }, [selectedIds, method]);
}
