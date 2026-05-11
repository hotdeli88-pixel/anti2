"use client";

import { useGuidelines } from "@/lib/queries";
import { PenLine, Book, FileText } from "lucide-react";

const ICONS: Record<string, typeof PenLine> = {
  pen: PenLine,
  book: Book,
  file: FileText,
};

export function GuidelinesPanel() {
  const { data, isLoading } = useGuidelines();
  return (
    <>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-bold">2026학년도 생기부 기재요령 세부사항</h2>
      </div>
      {isLoading && <div className="text-ink-gray">불러오는 중…</div>}
      <div className="space-y-4">
        {data?.map((g) => {
          const Icon = ICONS[g.icon] ?? PenLine;
          return (
            <div
              key={g.id}
              className="rounded-lg border border-surface-border bg-white p-6 shadow-sm"
            >
              <div className="mb-3 flex items-center gap-2 text-base font-bold text-brand">
                <Icon className="h-4 w-4" />
                {g.title}
              </div>
              <div
                className="text-[15px] leading-relaxed text-ink-dark whitespace-pre-line"
                dangerouslySetInnerHTML={{ __html: renderMarkdown(g.body_markdown) }}
              />
              {g.reference && (
                <div className="mt-3 text-xs text-ink-light">
                  근거: {g.reference}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </>
  );
}

// 단순 마크다운 → HTML (하이라이트·볼드만). DOMPurify는 서버 응답 신뢰 가정(관리자 입력) 후 적용 권장.
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
