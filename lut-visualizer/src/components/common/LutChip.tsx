interface LutChipProps {
  name: string;
  color: string;
  onRemove?: () => void;
}

export function LutChip({ name, color, onRemove }: LutChipProps) {
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-mono"
      style={{ background: `${color}22`, border: `1px solid ${color}`, color }}
    >
      {name}
      {onRemove && (
        <button
          onClick={onRemove}
          className="ml-1 hover:opacity-70 leading-none"
          aria-label={`Remove ${name}`}
        >
          ×
        </button>
      )}
    </span>
  );
}
