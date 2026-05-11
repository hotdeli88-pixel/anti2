"use client";

import { cn } from "@/lib/cn";
import { Check, Plus } from "lucide-react";

export interface TagItem {
  id: string;
  label: string;
  category?: string;
  description?: string;
}

interface TagChipGroupProps {
  label: string;
  hint?: string;
  tags: TagItem[];
  value: string[];
  onChange: (ids: string[]) => void;
  max?: number;
  size?: "sm" | "md";
  ariaLabel?: string;
}

export function TagChipGroup({
  label,
  hint,
  tags,
  value,
  onChange,
  max,
  size = "md",
  ariaLabel,
}: TagChipGroupProps) {
  const toggle = (id: string) => {
    if (value.includes(id)) {
      onChange(value.filter((v) => v !== id));
    } else {
      if (max && value.length >= max) return;
      onChange([...value, id]);
    }
  };

  return (
    <fieldset aria-label={ariaLabel ?? label}>
      <div className="mb-2 flex items-baseline justify-between">
        <legend className="text-body-sm font-semibold text-ink-dark">
          {label}
          {max && (
            <span className="ml-2 text-caption text-ink-light">
              {value.length} / {max}개
            </span>
          )}
        </legend>
        {hint && <span className="text-caption text-ink-light">{hint}</span>}
      </div>
      <div className="flex flex-wrap gap-2">
        {tags.map((tag) => {
          const selected = value.includes(tag.id);
          const disabled =
            !selected && typeof max === "number" && value.length >= max;
          return (
            <button
              key={tag.id}
              type="button"
              onClick={() => toggle(tag.id)}
              disabled={disabled}
              aria-pressed={selected}
              title={tag.description}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-full border font-medium transition-all duration-quick",
                size === "sm"
                  ? "px-3 py-1.5 text-caption"
                  : "px-4 py-2 text-body-sm",
                selected
                  ? "border-brand bg-brand-light text-brand"
                  : "border-surface-border bg-white text-ink-gray hover:border-brand hover:bg-brand-light/50 hover:text-ink-dark",
                disabled && "cursor-not-allowed opacity-40 hover:!bg-white",
              )}
            >
              {selected ? (
                <Check className="h-3 w-3" />
              ) : (
                <Plus className="h-3 w-3" />
              )}
              {tag.label}
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}
