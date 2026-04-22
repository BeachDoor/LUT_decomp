import { useAppStore } from "../../store/useAppStore";
import { SELECTION_COLORS } from "../../lib/colormap";

export function LutSelector() {
  const payload = useAppStore((s) => s.payload);
  const selectedIds = useAppStore((s) => s.selectedIds);
  const toggleSelected = useAppStore((s) => s.toggleSelected);

  if (!payload) return null;

  return (
    <div className="px-3 py-2 border-b border-[var(--color-border)] text-xs font-mono">
      <div className="text-[var(--color-muted)] mb-1.5">
        レーダー比較 — LUT選択 (最大4個)
      </div>
      <div className="flex flex-wrap gap-1">
        {payload.luts.map((lut) => {
          const selIdx = selectedIds.indexOf(lut.id);
          const isSelected = selIdx >= 0;
          const color = isSelected ? SELECTION_COLORS[selIdx] : undefined;
          return (
            <button
              key={lut.id}
              onClick={() => toggleSelected(lut.id)}
              className="px-2 py-0.5 rounded border transition-colors text-[10px]"
              style={
                isSelected
                  ? {
                      borderColor: color,
                      color,
                      background: `${color}18`,
                    }
                  : {
                      borderColor: "var(--color-border)",
                      color: "var(--color-muted)",
                    }
              }
            >
              {isSelected && (
                <span className="mr-1 font-bold">{selIdx + 1}.</span>
              )}
              {lut.name}
            </button>
          );
        })}
      </div>
    </div>
  );
}
