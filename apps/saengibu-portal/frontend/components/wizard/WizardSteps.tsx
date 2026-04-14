"use client";

import { cn } from "@/lib/cn";
import { Check } from "lucide-react";

export interface WizardStep {
  id: string;
  label: string;
  hint?: string;
}

interface WizardStepsProps {
  steps: WizardStep[];
  current: number; // 0-based
  completed: number[];
  onStepClick?: (idx: number) => void;
  orientation?: "horizontal" | "vertical";
}

export function WizardSteps({
  steps,
  current,
  completed,
  onStepClick,
  orientation = "horizontal",
}: WizardStepsProps) {
  const isHorz = orientation === "horizontal";
  return (
    <ol
      className={cn(
        "flex gap-0",
        isHorz ? "flex-row items-stretch" : "flex-col items-start",
      )}
      aria-label="작성 단계 진행"
    >
      {steps.map((step, idx) => {
        const done = completed.includes(idx);
        const active = current === idx;
        const clickable = done && typeof onStepClick === "function";
        return (
          <li
            key={step.id}
            className={cn(
              "group relative flex-1 min-w-[140px]",
              isHorz ? "flex items-center" : "flex items-start gap-3",
            )}
          >
            <button
              type="button"
              disabled={!clickable}
              onClick={clickable ? () => onStepClick!(idx) : undefined}
              className={cn(
                "flex items-center gap-3 w-full text-left",
                clickable && "cursor-pointer",
                !clickable && "cursor-default",
              )}
              aria-current={active ? "step" : undefined}
            >
              <span
                className={cn(
                  "flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 text-body-sm font-bold transition-colors duration-quick",
                  done &&
                    "border-brand bg-brand text-white",
                  active && !done &&
                    "border-brand bg-white text-brand ring-4 ring-brand-light",
                  !active && !done &&
                    "border-surface-border bg-white text-ink-light",
                )}
              >
                {done ? <Check className="h-4 w-4" /> : idx + 1}
              </span>
              <span className="flex flex-col">
                <span
                  className={cn(
                    "text-body-sm font-semibold",
                    active ? "text-ink-dark" : "text-ink-gray",
                  )}
                >
                  {step.label}
                </span>
                {step.hint && (
                  <span className="text-caption text-ink-light">
                    {step.hint}
                  </span>
                )}
              </span>
            </button>
            {isHorz && idx < steps.length - 1 && (
              <div
                className={cn(
                  "mx-2 h-0.5 flex-1 min-w-6 transition-colors duration-quick",
                  done ? "bg-brand" : "bg-surface-border",
                )}
                aria-hidden
              />
            )}
          </li>
        );
      })}
    </ol>
  );
}
