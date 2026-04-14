"use client";

import { AppShell } from "@/components/layout/AppShell";
import Link from "next/link";
import { Users, Sparkles, Compass, Heart, Activity, LifeBuoy } from "lucide-react";

const AREAS = [
  { code: "haengjongjeui", title: "행동특성 및 종합의견", hint: "학기·학년 전반 관찰 기반, 300자 이내", icon: Users, tone: "purple" },
  { code: "chang_jayul", title: "자율·자치활동", hint: "학급 자치·학교 행사 참여", icon: Compass, tone: "mint" },
  { code: "chang_jinro", title: "진로활동", hint: "진로탐색·직업 체험", icon: Sparkles, tone: "yellow" },
  { code: "chang_bongsa", title: "봉사활동 실적", hint: "(학교)/(개인) 구분, 실적별 50자", icon: Heart, tone: "mint" },
  { code: "ilsangsaenghwal", title: "일상생활 활동상황", hint: "특수교육 대상 일상생활 특기사항", icon: LifeBuoy, tone: "purple" },
  { code: "chulgyeol_teuggi", title: "출결 특기사항", hint: "결석 사유, 특기할 만한 출결", icon: Activity, tone: "yellow" },
];

const TONE: Record<string, string> = {
  mint: "bg-pastel-mint border-[#CCFBF1]",
  yellow: "bg-pastel-yellow border-[#FEF3C7]",
  purple: "bg-pastel-purple border-[#F3E8FF]",
};

export default function HomeroomPage() {
  return (
    <AppShell title="담임 전용">
      <div className="mb-8">
        <h2 className="text-display font-bold text-ink-dark">담임 전용 기록 영역</h2>
        <p className="mt-2 text-body-lg text-ink-gray">
          담임 선생님이 직접 관찰한 학생 정보를 바탕으로 기록합니다.
          본 시스템은 AI가 대신 쓰지 않고, 작성하신 초안에 훈령 기반 관점만 제시합니다.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {AREAS.map((a) => {
          const Icon = a.icon;
          return (
            <Link
              key={a.code}
              href={`/writer/new/homeroom/${a.code}`}
              className={`rounded-lg border p-6 shadow-sm transition duration-base hover:-translate-y-0.5 hover:shadow-hover ${TONE[a.tone]}`}
            >
              <Icon className="mb-3 h-6 w-6 text-ink-dark" />
              <h3 className="text-title font-bold text-ink-dark">{a.title}</h3>
              <p className="mt-2 text-body-sm text-ink-gray">{a.hint}</p>
            </Link>
          );
        })}
      </div>
    </AppShell>
  );
}
