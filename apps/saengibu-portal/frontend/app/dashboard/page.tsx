"use client";

import { AppShell } from "@/components/layout/AppShell";
import { StatsCards } from "@/components/records/StatsCards";
import { useApprovals } from "@/lib/queries";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

export default function DashboardPage() {
  const { data: approvals } = useApprovals();
  const recent = approvals?.slice(0, 5) ?? [];

  return (
    <AppShell title="대시보드">
      <StatsCards />
      <div className="card p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-bold">내 결재 대기 (최근 5건)</h2>
          <Link
            href="/records"
            className="flex items-center gap-1 text-sm font-semibold text-brand hover:underline"
          >
            전체 보기 <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
        {recent.length === 0 ? (
          <p className="text-sm text-ink-gray">대기 중인 결재가 없습니다.</p>
        ) : (
          <ul className="divide-y divide-surface-border">
            {recent.map((r) => (
              <li
                key={r.review_id}
                className="flex items-center justify-between py-3 text-sm"
              >
                <span>
                  <b>{r.student.name_masked}</b> · {r.section.name} ·{" "}
                  <span className="text-ink-gray">
                    {r.student.grade}-{r.student.class_no}
                  </span>
                </span>
                <span className="text-ink-gray">
                  {new Date(r.submitted_at).toLocaleString("ko-KR")}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </AppShell>
  );
}
