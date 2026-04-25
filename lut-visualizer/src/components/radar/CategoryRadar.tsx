import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";
import { buildRadarData } from "../../lib/normalize";
import { SELECTION_COLORS } from "../../lib/colormap";
import type {
  CategoryDefinition,
  FeatureDefinition,
  LutEntry,
} from "../../types/features";

interface CategoryRadarProps {
  category: CategoryDefinition;
  features: FeatureDefinition[];
  selectedLuts: LutEntry[];
  accentColor: string;
}

export function CategoryRadar({
  category,
  features,
  selectedLuts,
  accentColor,
}: CategoryRadarProps) {
  if (selectedLuts.length === 0) return null;

  // For hue_bands (18 features), show only hue_shift per band to avoid clutter
  let featureIds = category.feature_ids;
  if (category.id === "hue_bands") {
    featureIds = featureIds.filter((fid) => fid.endsWith("_hue_shift"));
  }

  const data = buildRadarData(featureIds, features, selectedLuts);

  return (
    <div className="p-2">
      <div
        className="text-[10px] font-mono uppercase tracking-wider mb-1 px-1"
        style={{ color: accentColor }}
      >
        {category.label}
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <RadarChart data={data} margin={{ top: 10, right: 20, bottom: 10, left: 20 }}>
          <PolarGrid stroke="var(--color-border)" />
          <PolarAngleAxis
            dataKey="subject"
            tick={{ fontSize: 8, fontFamily: "monospace", fill: "var(--color-muted)" }}
          />
          <Tooltip
            contentStyle={{
              background: "var(--color-surface)",
              border: "1px solid var(--color-border)",
              borderRadius: 4,
              fontSize: 10,
              fontFamily: "monospace",
            }}
            formatter={(val: number) => val.toFixed(3)}
          />
          {selectedLuts.map((lut, i) => (
            <Radar
              key={lut.id}
              name={lut.name}
              dataKey={lut.id}
              stroke={SELECTION_COLORS[i]}
              fill={SELECTION_COLORS[i]}
              fillOpacity={0.12}
              strokeWidth={1.5}
            />
          ))}
          {selectedLuts.length > 1 && (
            <Legend
              wrapperStyle={{ fontSize: 9, fontFamily: "monospace" }}
            />
          )}
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
