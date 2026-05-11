"use client";

import { AppShell } from "@/components/layout/AppShell";
import { EmptyState } from "@/components/ui/EmptyState";
import { Button } from "@/components/ui/Button";
import Link from "next/link";
import { PenLine, GraduationCap, Users, Sparkles } from "lucide-react";

const SHORTCUTS: Array<{
  title: string;
  description: string;
  href: string;
  icon: typeof PenLine;
  tone: "mint" | "yellow" | "purple";
}> = [
  {
    title: "과목 세특 작성",
    description: "과목·성취기준·활동을 선택하고 초안을 시작합니다.",
    href: "/writer/new/subject",
    icon: GraduationCap,
    tone: "mint",
  },
  {
    title: "담임 전용 기록",
    description: "행동특성·자율·진로·봉사 등 담임 영역을 작성합니다.",
    href: "/writer/new/homeroom",
    icon: Users,
    tone: "yellow",
  },
  {
    title: "즐겨찾기 템플릿",
    description: "자주 쓰는 관점·관찰 프레임을 재사용합니다.",
    href: "/library/templates",
    icon: Sparkles,
    tone: "purple",
  },
];

const TONE_CLASS: Record<string, string> = {
  mint: "bg-pastel-mint border-[#CCFBF1]",
  yellow: "bg-pastel-yellow border-[#FEF3C7]",
  purple: "bg-pastel-purple border-[#F3E8FF]",
};

export default function WriterPage() {
  return (
    <AppShell title="세특 작성">
      <div className="mb-8">
        <h2 className="text-display font-bold text-ink-dark">
          어떤 기록을 시작하실까요?
        </h2>
        <p className="mt-2 text-body-lg text-ink-gray">
          선생님의 관찰을 먼저 입력하고, AI가 기재요령 관점에서 검토합니다.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-5 md:grid-cols-3">
        {SHORTCUTS.map((s) => {
          const Icon = s.icon;
          return (
            <Link
              key={s.href}
              href={s.href}
              className={`rounded-lg border p-6 shadow-sm transition duration-base hover:-translate-y-0.5 hover:shadow-hover ${TONE_CLASS[s.tone]}`}
            >
              <Icon className="mb-3 h-6 w-6 text-ink-dark" />
              <h3 className="text-title font-bold text-ink-dark">{s.title}</h3>
              <p className="mt-2 text-body text-ink-gray">{s.description}</p>
            </Link>
          );
        })}
      </div>

      <div className="mt-10 card p-8">
        <EmptyState
          icon={PenLine}
          title="최근 작성한 초안이 없어요"
          description="위 카드에서 영역을 선택해 첫 기록을 시작해 보세요. 저장은 자동으로 이루어지며, 모든 버전은 감사 로그에 남습니다."
          action={
            <Link href="/writer/new/subject">
              <Button variant="primary">과목 세특 시작</Button>
            </Link>
          }
        />
      </div>
    </AppShell>
  );
}
