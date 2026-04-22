import { useState, useRef } from "react";
import { exportAsPng, exportAsSvg } from "../../lib/export";

interface ExportButtonProps {
  targetRef: React.RefObject<HTMLElement | null>;
  svgRef?: React.RefObject<SVGSVGElement | null>;
}

export function ExportButton({ targetRef, svgRef }: ExportButtonProps) {
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const handlePng = async () => {
    setOpen(false);
    if (targetRef.current) {
      await exportAsPng(targetRef.current);
    }
  };

  const handleSvg = () => {
    setOpen(false);
    if (svgRef?.current) {
      exportAsSvg(svgRef.current);
    }
  };

  return (
    <div className="relative" ref={menuRef} data-export-exclude>
      <button
        onClick={() => setOpen((v) => !v)}
        className="px-3 py-1.5 text-xs font-mono rounded border border-[var(--color-border)]
                   bg-[var(--color-surface)] hover:border-orange-500 hover:text-orange-400
                   transition-colors"
      >
        Export ▾
      </button>
      {open && (
        <div
          className="absolute right-0 top-full mt-1 z-50 rounded border border-[var(--color-border)]
                     bg-[var(--color-surface)] shadow-lg text-xs font-mono min-w-[120px]"
        >
          <button
            onClick={handlePng}
            className="w-full px-4 py-2 text-left hover:bg-[var(--color-border)] transition-colors"
          >
            Export PNG
          </button>
          {svgRef && (
            <button
              onClick={handleSvg}
              className="w-full px-4 py-2 text-left hover:bg-[var(--color-border)] transition-colors"
            >
              Export SVG
            </button>
          )}
        </div>
      )}
    </div>
  );
}
