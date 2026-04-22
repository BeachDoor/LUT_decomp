import { create } from "zustand";
import type {
  FeaturesPayload,
  ProjectionMethod,
  ProjectionStatus,
  Theme,
  Point2D,
} from "../types/features";

const MAX_SELECTED = 4;

interface AppState {
  payload: FeaturesPayload | null;
  selectedIds: string[];
  hoveredId: string | null;
  method: ProjectionMethod;
  projectedPoints: Record<string, Point2D> | null;
  projectionStatus: ProjectionStatus;
  theme: Theme;

  setPayload: (p: FeaturesPayload) => void;
  toggleSelected: (id: string) => void;
  setSelectedIds: (ids: string[]) => void;
  setHoveredId: (id: string | null) => void;
  setMethod: (m: ProjectionMethod) => void;
  setProjectedPoints: (pts: Record<string, Point2D>) => void;
  setProjectionStatus: (s: ProjectionStatus) => void;
  toggleTheme: () => void;
  setTheme: (t: Theme) => void;
}

export const useAppStore = create<AppState>()((set) => ({
  payload: null,
  selectedIds: [],
  hoveredId: null,
  method: "pca",
  projectedPoints: null,
  projectionStatus: "idle",
  theme: "dark",

  setPayload: (payload) => set({ payload }),

  toggleSelected: (id) =>
    set((s) => {
      const already = s.selectedIds.includes(id);
      if (already) {
        return { selectedIds: s.selectedIds.filter((x) => x !== id) };
      }
      if (s.selectedIds.length >= MAX_SELECTED) {
        return { selectedIds: [...s.selectedIds.slice(1), id] };
      }
      return { selectedIds: [...s.selectedIds, id] };
    }),

  setSelectedIds: (ids) => set({ selectedIds: ids.slice(0, MAX_SELECTED) }),

  setHoveredId: (hoveredId) => set({ hoveredId }),

  setMethod: (method) =>
    set({ method, projectedPoints: null, projectionStatus: "idle" }),

  setProjectedPoints: (projectedPoints) =>
    set({ projectedPoints, projectionStatus: "done" }),

  setProjectionStatus: (projectionStatus) => set({ projectionStatus }),

  toggleTheme: () =>
    set((s) => ({ theme: s.theme === "dark" ? "light" : "dark" })),

  setTheme: (theme) => set({ theme }),
}));
