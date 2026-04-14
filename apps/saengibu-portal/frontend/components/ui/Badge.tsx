import { cn } from "@/lib/cn";
import type { HTMLAttributes } from "react";

type Tone = "pending" | "approved" | "review" | "danger" | "neutral";

const toneClass: Record<Tone, string> = {
  pending: "badge-pending",
  approved: "badge-approved",
  review: "badge-review",
  danger: "badge-danger",
  neutral: "badge-neutral",
};

export function Badge({
  tone = "neutral",
  className,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { tone?: Tone }) {
  return (
    <span className={cn("badge", toneClass[tone], className)} {...props} />
  );
}
