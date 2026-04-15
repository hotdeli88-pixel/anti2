"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { useStandard } from "@/lib/queries";
import { X, Sparkles, AlertCircle } from "lucide-react";

interface LevelDescriptorDrawerProps {
  standardId: number | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const LEVEL_BG: Record<string, string> = {
  A: "bg-ok-bg",
  B: "bg-info-bg",
  C: "bg-warn-bg",
  D: "bg-pastel-purple",
  E: "bg-danger-bg",
};

export function LevelDescriptorDrawer({
  standardId,
  open,
  onOpenChange,
}: LevelDescriptorDrawerProps) {
  const { data, isLoading } = useStandard(standardId ?? undefined);

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-overlay bg-black/40 data-[state=open]:animate-fade-in" />
        <Dialog.Content className="fixed right-0 top-0 z-modal h-full w-full max-w-xl overflow-y-auto bg-white shadow-hover data-[state=open]:animate-slide-in">
          <div className="sticky top-0 flex items-center justify-between border-b border-surface-border bg-white p-6">
            <Dialog.Title className="text-heading font-bold text-ink-dark">
              성취수준 상세
            </Dialog.Title>
            <Dialog.Close asChild>
              <button
                aria-label="닫기"
                className="rounded-md p-1 text-ink-gray hover:bg-surface-body"
              >
                <X className="h-5 w-5" />
              </button>
            </Dialog.Close>
          </div>

          <div className="p-6">
            {isLoading && <div className="text-ink-gray">불러오는 중…</div>}
            {data && (
              <>
                <div className="mb-4 rounded-md bg-surface-body p-4">
                  <div className="font-mono text-body-sm font-semibold text-brand">
                    {data.code}
                  </div>
                  <div className="mt-1 text-body-lg text-ink-dark">
                    {data.statement}
                  </div>
                  <div className="mt-2 text-caption text-ink-gray">
                    {data.subject_code} · {data.school_level} {data.grade}학년 ·{" "}
                    {data.eval_scale === "5grade" ? "5단계" : data.eval_scale === "3grade" ? "3단계" : "P/F"}
                  </div>
                </div>

                <div className="mb-2 flex items-center gap-2 text-body-sm font-semibold text-ink-dark">
                  <Sparkles className="h-4 w-4 text-brand" />
                  성취수준별 기대 수행
                </div>

                <ul className="space-y-3">
                  {data.levels.length === 0 && (
                    <li className="text-body text-ink-light">
                      성취수준 데이터가 아직 없어요.
                    </li>
                  )}
                  {data.levels.map((lv) => (
                    <li
                      key={lv.level}
                      className={`rounded-md border border-surface-border p-4 ${LEVEL_BG[lv.level] ?? "bg-white"}`}
                    >
                      <div className="mb-1 flex items-center gap-2">
                        <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-white text-body-sm font-bold text-ink-dark">
                          {lv.level}
                        </span>
                        {lv.cutline_hint && (
                          <span className="text-caption text-ink-gray">
                            {lv.cutline_hint}
                          </span>
                        )}
                      </div>
                      <p className="text-body text-ink-dark leading-relaxed">
                        {lv.descriptor}
                      </p>
                    </li>
                  ))}
                </ul>

                <div className="mt-6 flex items-start gap-2 rounded-md bg-warn-bg p-3 text-caption text-ink-dark">
                  <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-warn" />
                  <div>
                    성취수준은 <b>교사 내부 참고용</b>입니다. 생기부 본문에 등급(A/B/C/D/E)을 직접 표기하지 마세요.
                  </div>
                </div>
              </>
            )}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
