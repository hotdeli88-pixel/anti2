"use client";

import { useSchoolDecisions } from "@/lib/queries";
import { AlertTriangle, Info, ShieldAlert } from "lucide-react";
import { cn } from "@/lib/cn";

const SEV_STYLE: Record<string, { border: string; Icon: typeof Info; color: string }> = {
  info: { border: "border-l-brand", Icon: Info, color: "text-brand" },
  warn: { border: "border-l-warn", Icon: AlertTriangle, color: "text-warn" },
  block: { border: "border-l-danger", Icon: ShieldAlert, color: "text-danger" },
};

export function DecisionsPanel() {
  const { data, isLoading } = useSchoolDecisions();
  return (
    <>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-bold">우리 학교 내부 결정사항 (가이드라인)</h2>
      </div>
      {isLoading && <div className="text-ink-gray">불러오는 중…</div>}
      <div className="space-y-4">
        {data?.map((d) => {
          const sev = SEV_STYLE[d.severity] ?? SEV_STYLE.info;
          const { Icon } = sev;
          return (
            <div
              key={d.id}
              className={cn(
                "rounded-lg border border-surface-border bg-white p-6 shadow-sm border-l-4",
                sev.border,
              )}
            >
              <div className="mb-3 flex items-center gap-2 text-base font-bold text-brand">
                <Icon className={cn("h-4 w-4", sev.color)} />
                {d.title}
              </div>
              <div
                className="text-[15px] leading-relaxed text-ink-dark whitespace-pre-line"
                dangerouslySetInnerHTML={{ __html: renderMarkdown(d.body_markdown) }}
              />
              <div className="mt-3 flex gap-3 text-xs text-ink-light">
                <span>시행일: {d.effective_date}</span>
                <span>게시자: {d.posted_by}</span>
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
}

function renderMarkdown(s: string): string {
  const escaped = s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  return escaped
    .replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>")
    .replace(
      /==([^=]+)==/g,
      '<span class="bg-pastel-yellow px-1.5 py-0.5 rounded font-semibold">$1</span>',
    )
    .replace(/\n/g, "<br/>");
}
