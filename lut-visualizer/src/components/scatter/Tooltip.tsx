import { LutThumbnail } from "../common/LutThumbnail";
import type { LutEntry, FeatureDefinition } from "../../types/features";

interface TooltipProps {
  lut: LutEntry;
  features: FeatureDefinition[];
  x: number;
  y: number;
}

const KEY_FEATURES = [
  "global_temperature_shift",
  "overall_chroma_multiplier",
  "overall_contrast",
  "tone_curve_nonlinearity",
];

export function Tooltip({ lut, features, x, y }: TooltipProps) {
  const featureMap = new Map(features.map((f) => [f.id, f]));

  return (
    <div
      className="fixed z-50 pointer-events-none rounded border border-[var(--color-border)]
                 bg-[var(--color-surface)] shadow-xl text-xs font-mono min-w-[200px]"
      style={{ left: x + 14, top: y - 8 }}
    >
      <LutThumbnail
        thumbnailPath={lut.thumbnail_path}
        alt={lut.name}
        className="w-full h-[90px] rounded-t rounded-b-none"
      />
      <div className="px-3 py-2">
        <div className="font-bold text-orange-400 mb-1.5">{lut.name}</div>
        {KEY_FEATURES.map((fid) => {
          const fDef = featureMap.get(fid);
          if (!fDef) return null;
          const val = lut.features[fid] ?? 0;
          return (
            <div key={fid} className="flex justify-between gap-4 text-[10px]">
              <span className="text-[var(--color-muted)]">{fDef.label}</span>
              <span>
                {val.toFixed(3)} {fDef.unit}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
