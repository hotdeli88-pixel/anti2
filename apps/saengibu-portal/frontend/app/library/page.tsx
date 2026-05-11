"use client";

import { AppShell } from "@/components/layout/AppShell";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/Tabs";
import { Badge } from "@/components/ui/Badge";
import { AchievementLevelBadges } from "@/components/wizard/AchievementLevelBadges";
import { LevelDescriptorDrawer } from "@/components/wizard/LevelDescriptorDrawer";
import { useStandards } from "@/lib/queries";
import { BookMarked, Tag, Sparkles, Search } from "lucide-react";
import { useState } from "react";
import type { Level } from "@/types/standards";

const TAGS = [
  { subject: "수학", category: "수업활동", label: "문제풀이 활동", count: 12 },
  { subject: "수학", category: "수업활동", label: "교구 활용 활동", count: 8 },
  { subject: "국어", category: "수업활동", label: "토론", count: 22 },
  { subject: "국어", category: "수업활동", label: "글쓰기", count: 18 },
  { subject: "영어", category: "수업활동", label: "말하기 발표", count: 15 },
  { subject: "공통", category: "역할수행", label: "모둠장을 맡음", count: 45 },
];

const TEMPLATES = [
  { title: "수학 문제풀이 + 모둠장 리더십 종합", section: "과목별 세특", bytes: 1280, lastUsed: "2026-04-10" },
  { title: "국어 토론 활동 관찰 프레임", section: "과목별 세특", bytes: 1450, lastUsed: "2026-04-08" },
  { title: "자율활동 학급 자치 주도 사례", section: "자율·자치활동", bytes: 1380, lastUsed: "2026-04-05" },
];

const SUBJECTS = ["수학", "국어", "영어", "과학", "사회", "역사", "도덕", "체육", "음악", "미술"];

export default function LibraryPage() {
  const [q, setQ] = useState("");
  const [grade, setGrade] = useState<number | undefined>(undefined);
  const [subject, setSubject] = useState<string | undefined>(undefined);
  const [drawerStandardId, setDrawerStandardId] = useState<number | null>(null);

  const { data, isLoading } = useStandards({
    schoolLevel: "middle",
    grade,
    subject,
    search: q || undefined,
    limit: 50,
  });

  return (
    <AppShell title="라이브러리">
      <div className="mb-6">
        <p className="text-body-lg text-ink-gray">
          학교 전체에서 공유되는 성취기준·활동 태그·개인 즐겨찾기 템플릿입니다.
        </p>
      </div>

      <Tabs defaultValue="standards">
        <TabsList>
          <TabsTrigger value="standards">
            <BookMarked className="mr-2 inline h-4 w-4" /> 성취기준
          </TabsTrigger>
          <TabsTrigger value="tags">
            <Tag className="mr-2 inline h-4 w-4" /> 활동 태그
          </TabsTrigger>
          <TabsTrigger value="templates">
            <Sparkles className="mr-2 inline h-4 w-4" /> 내 즐겨찾기
          </TabsTrigger>
        </TabsList>

        <TabsContent value="standards">
          <div className="mb-4 grid grid-cols-1 gap-3 md:grid-cols-[1fr_auto_auto]">
            <div className="flex items-center gap-2 rounded-md border border-surface-border bg-white px-3 py-2">
              <Search className="h-4 w-4 text-ink-gray" />
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="성취기준 코드·키워드 검색 (예: 9수, 토론)"
                className="flex-1 border-none bg-transparent text-body outline-none placeholder:text-ink-light"
                aria-label="성취기준 검색"
              />
            </div>
            <select
              value={grade ?? ""}
              onChange={(e) => setGrade(e.target.value ? Number(e.target.value) : undefined)}
              className="rounded-md border border-surface-border bg-white px-3 py-2 text-body"
              aria-label="학년 필터"
            >
              <option value="">전체 학년</option>
              <option value="1">1학년</option>
              <option value="2">2학년</option>
              <option value="3">3학년</option>
            </select>
            <select
              value={subject ?? ""}
              onChange={(e) => setSubject(e.target.value || undefined)}
              className="rounded-md border border-surface-border bg-white px-3 py-2 text-body"
              aria-label="과목 필터"
            >
              <option value="">전체 과목</option>
              {SUBJECTS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          <h2 className="mb-3 text-title font-bold">2022 개정 교육과정 · 중학교</h2>

          {isLoading && (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="skeleton h-24 w-full" />
              ))}
            </div>
          )}

          {!isLoading && (data?.items.length ?? 0) === 0 && (
            <div className="rounded-md border border-surface-border bg-surface-body p-10 text-center text-body text-ink-gray">
              조건에 맞는 성취기준이 없어요. 필터를 바꾸거나 검색어를 비워보세요.
            </div>
          )}

          <ul className="space-y-3">
            {data?.items.map((s) => {
              const availableLevels: Level[] = (s.levels?.map((l) => l.level) ??
                []) as Level[];
              return (
                <li key={s.id} className="card p-4">
                  <div className="flex items-start gap-4">
                    <div className="flex shrink-0 gap-2">
                      <Badge tone="review">{s.subject_code}</Badge>
                      <Badge tone="neutral">{s.grade}학년</Badge>
                    </div>
                    <div className="flex-1">
                      <div className="font-mono text-body-sm font-semibold text-brand">
                        {s.code}
                      </div>
                      <div className="mt-1 text-body text-ink-dark">{s.statement}</div>
                      {s.domain && (
                        <div className="mt-1 text-caption text-ink-light">
                          {s.domain}
                          {s.unit_title ? ` · ${s.unit_title}` : ""}
                        </div>
                      )}
                      {availableLevels.length > 0 && (
                        <div className="mt-2 flex items-center justify-between">
                          <AchievementLevelBadges available={availableLevels} size="sm" />
                          <button
                            type="button"
                            onClick={() => setDrawerStandardId(s.id)}
                            className="text-caption font-semibold text-brand hover:underline"
                          >
                            5단계 자세히
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>

          <LevelDescriptorDrawer
            standardId={drawerStandardId}
            open={drawerStandardId !== null}
            onOpenChange={(o) => !o && setDrawerStandardId(null)}
          />
        </TabsContent>

        <TabsContent value="tags">
          <h2 className="mb-4 text-title font-bold">과목·카테고리별 활동 태그</h2>
          <div className="flex flex-wrap gap-3">
            {TAGS.map((t) => (
              <div
                key={t.label}
                className="flex items-center gap-2 rounded-full border border-surface-border bg-white px-4 py-2"
              >
                <span className="text-caption text-ink-light">{t.subject}</span>
                <span className="text-caption text-ink-light">·</span>
                <span className="text-caption text-ink-gray">{t.category}</span>
                <span className="text-caption text-ink-light">·</span>
                <span className="text-body-sm font-semibold text-ink-dark">
                  {t.label}
                </span>
                <Badge tone="neutral">사용 {t.count}회</Badge>
              </div>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="templates">
          <h2 className="mb-4 text-title font-bold">내 즐겨찾기 템플릿</h2>
          <p className="mb-4 text-body-sm text-ink-gray">
            학생 실명은 자동으로 &#123;&#123;name&#125;&#125; 으로 치환되어 저장됩니다. 재사용 시 학생 맞춤 수정은 반드시 교사 본인이 직접 하세요.
          </p>
          <div className="space-y-3">
            {TEMPLATES.map((t) => (
              <div
                key={t.title}
                className="card flex items-center justify-between p-4"
              >
                <div>
                  <h3 className="text-title font-semibold text-ink-dark">
                    {t.title}
                  </h3>
                  <div className="mt-1 flex gap-3 text-caption text-ink-light">
                    <span>{t.section}</span>
                    <span>· {t.bytes} Byte</span>
                    <span>· 마지막 사용 {t.lastUsed}</span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button className="btn btn-sm">복사</button>
                  <button className="btn btn-outline btn-sm">편집</button>
                </div>
              </div>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </AppShell>
  );
}
