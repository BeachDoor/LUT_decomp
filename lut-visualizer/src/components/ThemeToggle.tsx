import { useAppStore } from "../store/useAppStore";

export function ThemeToggle() {
  const theme = useAppStore((s) => s.theme);
  const toggleTheme = useAppStore((s) => s.toggleTheme);

  return (
    <button
      onClick={toggleTheme}
      className="px-3 py-1.5 text-xs font-mono rounded border border-[var(--color-border)]
                 bg-[var(--color-surface)] hover:border-orange-500 hover:text-orange-400
                 transition-colors"
      aria-label="Toggle theme"
      title={theme === "dark" ? "Switch to light" : "Switch to dark"}
    >
      {theme === "dark" ? "☀ Light" : "◑ Dark"}
    </button>
  );
}
