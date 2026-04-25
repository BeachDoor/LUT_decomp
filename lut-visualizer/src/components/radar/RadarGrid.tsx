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
    // Desktop: h-full fills fixed-height pane and scrolls internally
    // Mobile: natural height, parent scrolls
    <div className="flex flex-col lg:h-full">
      <LutSelector />
      <div className="lg:flex-1 lg:overflow-auto">
        {selectedLuts.length === 0 ? (
          <div className="flex items-center justify-center py-12 text-[var(--color-muted)] text-xs font-mono text-center px-8">
            LUTを選択するとレーダーチャートが表示されます
          </div>
        ) : (
          // Mobile: 1 column; tablet+: 2 columns
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-1 p-2">
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
