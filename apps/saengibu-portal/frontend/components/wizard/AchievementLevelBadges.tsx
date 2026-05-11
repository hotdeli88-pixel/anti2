"use client";

import { cn } from "@/lib/cn";
import type { Level } from "@/types/standards";

const LEVEL_TONE: Record<Level, string> = {
  A: "bg-ok-bg text-[#059669]",
  B: "bg-info-bg text-info",
  C: "bg-warn-bg text-warn",
  D: "bg-pastel-purple text-ai-detected",
  E: "bg-danger-bg text-danger",
  P: "bg-ok-bg text-[#059669]",
  F: "bg-danger-bg text-danger",
};

interface AchievementLevelBadgesProps {
  /** 보유한 레벨 코드 배열 (예: ['A','B','C','D','E']) */
  available: Level[];
  /** 선택된 레벨 (단일) */
  value?: Level;
  onChange?: (level: Level) => void;
  size?: "sm" | "md";
}

export function AchievementLevelBadges({
  available,
  value,
  onChange,
  size = "md",
}: AchievementLevelBadgesProps) {
  return (
    <div role="group" aria-label="성취수준" className="flex gap-1.5">
      {available.map((lvl) => {
        const selected = value === lvl;
        const sizeCls =
          size === "sm" ? "h-6 w-6 text-caption" : "h-8 w-8 text-body-sm";
        return (
          <button
            key={lvl}
            type="button"
            onClick={() => onChange?.(lvl)}
            aria-pressed={selected}
            disabled={!onChange}
            className={cn(
              "rounded-full font-bold transition focus-visible:outline-none",
              sizeCls,
              LEVEL_TONE[lvl],
              selected && "ring-2 ring-brand ring-offset-2",
              onChange && "hover:scale-110 cursor-pointer",
            )}
            title={`성취수준 ${lvl}`}
          >
            {lvl}
          </button>
        );
      })}
    </div>
  );
}
