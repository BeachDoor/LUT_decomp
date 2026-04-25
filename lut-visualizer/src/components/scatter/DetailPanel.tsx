import { useAppStore } from "../../store/useAppStore";
import { getLutColor } from "../../lib/colormap";
import { CATEGORY_COLORS } from "../../lib/colormap";
import { LutThumbnail } from "../common/LutThumbnail";

export function DetailPanel() {
  const payload = useAppStore((s) => s.payload);
  const selectedIds = useAppStore((s) => s.selectedIds);

  if (!payload || selectedIds.length === 0) return null;

  const categories = payload.feature_schema.categories;
  const features = payload.feature_schema.features;
  const featureMap = new Map(features.map((f) => [f.id, f]));

  const selectedLuts = selectedIds
    .map((id) => payload.luts.find((l) => l.id === id))
    .filter(Boolean);

  return (
    <div
      className="border-t border-[var(--color-border)] bg-[var(--color-surface)]
                 overflow-auto text-xs font-mono"
      style={{ maxHeight: 220 }}
    >
      <div className="p-3">
        <div className="flex flex-wrap gap-3 mb-2">
          {selectedLuts.map((lut, i) => {
            if (!lut) return null;
            const color = getLutColor(lut.id, selectedIds) ?? "#888";
            return (
              <div key={lut.id} className="flex items-center gap-2">
                <LutThumbnail
                  thumbnailPath={lut.thumbnail_path}
                  alt={lut.name}
                  className="w-20 h-[53px] border"
                  style={{ borderColor: color }}
                />
                <span className="font-bold text-[11px]" style={{ color }}>
                  {i + 1}. {lut.name}
                </span>
              </div>
            );
          })}
        </div>

        <table className="w-full border-collapse">
          <thead>
            <tr className="text-[var(--color-muted)]">
              <th className="text-left py-0.5 pr-4 font-normal">特徴量</th>
              <th className="text-left py-0.5 pr-2 font-normal">単位</th>
              {selectedLuts.map((lut, i) => {
                if (!lut) return null;
                const color = getLutColor(lut.id, selectedIds) ?? "#888";
                return (
                  <th
                    key={lut.id}
                    className="text-right py-0.5 pl-4 font-normal"
                    style={{ color }}
                  >
                    {i + 1}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {categories.map((cat) => (
              <>
                <tr key={`cat-${cat.id}`}>
                  <td
                    colSpan={2 + selectedLuts.length}
                    className="pt-2 pb-0.5 text-[10px] uppercase tracking-wider"
                    style={{ color: CATEGORY_COLORS[cat.id] ?? "#888" }}
                  >
                    {cat.label}
                  </td>
                </tr>
                {cat.feature_ids.map((fid) => {
                  const fDef = featureMap.get(fid);
                  if (!fDef) return null;
                  return (
                    <tr
                      key={fid}
                      className="hover:bg-[var(--color-bg)] transition-colors"
                    >
                      <td className="py-0.5 pr-4 text-[var(--color-muted)]">
                        {fDef.label}
                      </td>
                      <td className="py-0.5 pr-2 text-[var(--color-muted)]">
                        {fDef.unit}
                      </td>
                      {selectedLuts.map((lut) => {
                        if (!lut) return null;
                        const val = lut.features[fid] ?? 0;
                        const neutral = fDef.neutral_value;
                        const diff = val - neutral;
                        const isSignificant = Math.abs(diff) > 0.01;
                        return (
                          <td
                            key={lut.id}
                            className="text-right py-0.5 pl-4 tabular-nums"
                            style={{
                              color: isSignificant
                                ? diff > 0
                                  ? "#f97316"
                                  : "#3b82f6"
                                : undefined,
                            }}
                          >
                            {val.toFixed(3)}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
