import { useAppStore } from "../store/useAppStore";
import { getLutColor } from "../lib/colormap";
import { LutThumbnail } from "./common/LutThumbnail";

export function ThumbnailStrip() {
  const payload = useAppStore((s) => s.payload);
  const selectedIds = useAppStore((s) => s.selectedIds);
  const toggleSelected = useAppStore((s) => s.toggleSelected);

  if (!payload || selectedIds.length === 0) return null;

  const selectedLuts = selectedIds
    .map((id) => payload.luts.find((l) => l.id === id))
    .filter((l): l is NonNullable<typeof l> => l !== undefined);

  return (
    <div
      className="flex gap-3 px-3 py-2 border-b border-[var(--color-border)]
                 bg-[var(--color-surface)] overflow-x-auto shrink-0"
    >
      {selectedLuts.map((lut, i) => {
        const color = getLutColor(lut.id, selectedIds) ?? "#888";
        return (
          <div key={lut.id} className="flex flex-col shrink-0 gap-1">
            <div className="relative">
              <LutThumbnail
                thumbnailPath={lut.thumbnail_path}
                alt={lut.name}
                className="w-[160px] h-[107px] lg:w-[200px] lg:h-[133px] border-2"
                style={{ borderColor: color }}
              />
              <button
                onClick={() => toggleSelected(lut.id)}
                className="absolute top-1 right-1 w-4 h-4 rounded-full flex items-center
                           justify-center text-[9px] leading-none font-bold"
                style={{ background: color, color: "#fff" }}
                aria-label={`Remove ${lut.name}`}
              >
                ×
              </button>
            </div>
            <span
              className="text-[10px] font-mono truncate w-[160px] lg:w-[200px]"
              style={{ color }}
            >
              {i + 1}. {lut.name}
            </span>
          </div>
        );
      })}
    </div>
  );
}
