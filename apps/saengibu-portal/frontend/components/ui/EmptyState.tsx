import { cn } from "@/lib/cn";
import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-16 px-8 text-center",
        className,
      )}
    >
      {Icon && (
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-brand-light text-brand">
          <Icon className="h-7 w-7" />
        </div>
      )}
      <h3 className="text-heading font-semibold text-ink-dark">{title}</h3>
      {description && (
        <p className="mt-2 max-w-md text-body text-ink-gray">{description}</p>
      )}
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}
