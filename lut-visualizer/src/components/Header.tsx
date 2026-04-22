import { ThemeToggle } from "./ThemeToggle";
import { ExportButton } from "./common/ExportButton";

interface HeaderProps {
  exportTargetRef: React.RefObject<HTMLElement | null>;
}

export function Header({ exportTargetRef }: HeaderProps) {
  return (
    <header
      className="flex items-center justify-between px-4 py-2 border-b border-[var(--color-border)]
                 bg-[var(--color-surface)] shrink-0"
    >
      <div className="flex items-center gap-3">
        <span className="text-sm font-mono font-bold text-orange-400 tracking-wide">
          LUT Interpreter
        </span>
        <span className="text-xs text-[var(--color-muted)]">
          特徴量ビジュアライザ
        </span>
      </div>
      <div className="flex items-center gap-2">
        <ExportButton targetRef={exportTargetRef} />
        <ThemeToggle />
      </div>
    </header>
  );
}
