import { useAppStore } from "../../store/useAppStore";
import { CategoryRadar } from "./CategoryRadar";
import { LutSelector } from "./LutSelector";
import { CATEGORY_COLORS } from "../../lib/colormap";

export function RadarGrid() {
  const payload = useAppStore((s) => s.payload);
  const selectedIds = useAppStore((s) => s.selectedIds);

  if (!payload) {
    return (
      <div className="flex items-center justify-center h-full text-[var(--color-muted)] text-xs font-mono">
        Loading…
      </div>
    );
  }

  const { categories, features } = payload.feature_schema;
  const selectedLuts = selectedIds
    .map((id) => payload.luts.find((l) => l.id === id))
    .filter((l): l is NonNullable<typeof l> => l !== undefined);

  return (
    <div className="flex flex-col h-full">
      <LutSelector />
      <div className="flex-1 overflow-auto">
        {selectedLuts.length === 0 ? (
          <div className="flex items-center justify-center h-full text-[var(--color-muted)] text-xs font-mono p-8 text-center">
            LUTを選択するとレーダーチャートが表示されます
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-1 p-2">
            {categories.map((cat) => (
              <div
                key={cat.id}
                className="rounded border border-[var(--color-border)] bg-[var(--color-bg)]"
              >
                <CategoryRadar
                  category={cat}
                  features={features}
                  selectedLuts={selectedLuts}
                  accentColor={CATEGORY_COLORS[cat.id] ?? "#888"}
                />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
