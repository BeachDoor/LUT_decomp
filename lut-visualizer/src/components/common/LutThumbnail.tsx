import { useState } from "react";
import type React from "react";

interface LutThumbnailProps {
  thumbnailPath: string;
  alt: string;
  className?: string;
  style?: React.CSSProperties;
}

export function LutThumbnail({ thumbnailPath, alt, className = "", style }: LutThumbnailProps) {
  const [failed, setFailed] = useState(false);

  const src = `${import.meta.env.BASE_URL}${thumbnailPath.replace(/^\//, "")}`;

  if (failed) {
    return (
      <div
        className={`flex items-center justify-center bg-[var(--color-border)]
                    text-[var(--color-muted)] text-[10px] font-mono rounded ${className}`}
        style={style}
      >
        No image
      </div>
    );
  }

  return (
    <img
      src={src}
      alt={alt}
      onError={() => setFailed(true)}
      className={`object-cover rounded ${className}`}
      style={style}
      loading="lazy"
    />
  );
}
