"use client";

import { cn } from "@/lib/cn";

function cp949Bytes(text: string): number {
  let bytes = 0;
  for (const ch of text.replace(/\n/g, "\r\n")) {
    const code = ch.codePointAt(0) ?? 0;
    bytes += code < 0x80 ? 1 : 2;
  }
  return bytes;
}

interface ByteMeterProps {
  value: string;
  limit: number;
  counter?: (s: string) => number;
  warnRatio?: number;
  className?: string;
}

export function ByteMeter({
  value,
  limit,
  counter = cp949Bytes,
  warnRatio = 0.9,
  className,
}: ByteMeterProps) {
  const count = counter(value);
  const ratio = Math.min(count / limit, 1.5);
  const over = count > limit;
  const nearLimit = !over && count >= limit * warnRatio;

  const color = over
    ? "bg-danger"
    : nearLimit
      ? "bg-warn"
      : "bg-brand";

  return (
    <div className={cn("w-full", className)}>
      <div className="mb-1 flex items-baseline justify-between text-body-sm">
        <span className="font-medium text-ink-gray">Byte 사용량</span>
        <span
          className={cn(
            "font-mono font-semibold",
            over ? "text-danger" : nearLimit ? "text-warn" : "text-ink-dark",
          )}
        >
          {count} / {limit} B
          {over && <span className="ml-1">({count - limit} 초과)</span>}
        </span>
      </div>
      <div
        className="h-2 w-full overflow-hidden rounded-full bg-surface-subtle"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={limit}
        aria-valuenow={count}
        aria-label="Byte 사용량"
      >
        <div
          className={cn("h-full transition-all duration-moderate", color)}
          style={{ width: `${Math.min(ratio * 100, 100)}%` }}
        />
      </div>
      <p className="mt-1 text-caption text-ink-light">
        NEIS 실제 상한(CP949 기준)과 일치하지 않을 수 있으니 여유 있게 작성하세요.
      </p>
    </div>
  );
}

export { cp949Bytes };
