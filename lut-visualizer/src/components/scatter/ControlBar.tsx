import { useAppStore } from "../../store/useAppStore";
import { LutChip } from "../common/LutChip";
import { SELECTION_COLORS } from "../../lib/colormap";
import type { ProjectionMethod } from "../../types/features";

const METHODS: { value: ProjectionMethod; label: string }[] = [
  { value: "pca", label: "PCA" },
  { value: "umap", label: "UMAP" },
];

export function ControlBar() {
  const method = useAppStore((s) => s.method);
  const status = useAppStore((s) => s.projectionStatus);
  const setMethod = useAppStore((s) => s.setMethod);
  const selectedIds = useAppStore((s) => s.selectedIds);
  const toggleSelected = useAppStore((s) => s.toggleSelected);
  const payload = useAppStore((s) => s.payload);

  const lutMap = new Map(payload?.luts.map((l) => [l.id, l.name]) ?? []);

  return (
    <div
      className="flex flex-wrap items-center gap-3 px-3 py-2 border-b border-[var(--color-border)]
                 bg-[var(--color-surface)] text-xs font-mono"
    >
      <div className="flex items-center gap-1">
        {METHODS.map((m) => (
          <button
            key={m.value}
            onClick={() => setMethod(m.value)}
            className={`px-3 py-1 rounded transition-colors ${
              method === m.value
                ? "bg-orange-500 text-white"
                : "bg-[var(--color-bg)] border border-[var(--color-border)] hover:border-orange-400"
            }`}
          >
            {m.label}
          </button>
        ))}
      </div>

      {status === "computing" && (
        <span className="text-[var(--color-muted)] animate-pulse">
          computing…
        </span>
      )}
      {status === "error" && (
        <span className="text-red-400">projection error</span>
      )}

      <div className="flex flex-wrap items-center gap-1 ml-auto">
        {selectedIds.length === 0 ? (
          <span className="text-[var(--color-muted)]">
            クリックしてLUTを選択 (最大4個)
          </span>
        ) : (
          selectedIds.map((id, i) => (
            <LutChip
              key={id}
              name={lutMap.get(id) ?? id}
              color={SELECTION_COLORS[i]}
              onRemove={() => toggleSelected(id)}
            />
          ))
        )}
      </div>
    </div>
  );
}
