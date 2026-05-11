"use client";

import { useDashboardStats } from "@/lib/queries";
import { cn } from "@/lib/cn";

const tiles: Array<{
  key: keyof NonNullable<ReturnType<typeof useDashboardStats>["data"]>;
  title: string;
  tone: "yellow" | "mint" | "purple";
}> = [
  { key: "pending_approvals", title: "승인 대기 중", tone: "yellow" },
  { key: "approved_this_week", title: "이번 주 승인 완료", tone: "mint" },
  { key: "ai_corrections", title: "AI 가이드 교정", tone: "purple" },
];

const toneClass: Record<string, string> = {
  yellow: "bg-pastel-yellow border-[#FEF3C7]",
  mint: "bg-pastel-mint border-[#CCFBF1]",
  purple: "bg-pastel-purple border-[#F3E8FF]",
};

export function StatsCards() {
  const { data, isLoading } = useDashboardStats();
  return (
    <div
      className="animate-fade-in mb-8 grid grid-cols-1 gap-5 md:grid-cols-3"
      style={{ animationDelay: "0.1s" }}
    >
      {tiles.map((t) => (
        <div
          key={t.key}
          className={cn(
            "rounded-lg border p-6 shadow-sm transition hover:-translate-y-0.5 hover:shadow-hover",
            toneClass[t.tone],
          )}
        >
          <div className="mb-2 text-sm font-semibold text-ink-gray">
            {t.title}
          </div>
          <div className="text-[32px] font-bold text-ink-dark">
            {isLoading ? "—" : `${data?.[t.key] ?? 0}건`}
          </div>
        </div>
      ))}
    </div>
  );
}
