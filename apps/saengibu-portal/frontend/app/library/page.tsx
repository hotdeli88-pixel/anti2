"use client";

import { AppShell } from "@/components/layout/AppShell";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/Tabs";
import { Badge } from "@/components/ui/Badge";
import { BookMarked, Tag, Sparkles, Search } from "lucide-react";
import { useState } from "react";

const STANDARDS = [
  { grade: 1, subject: "수학", code: "[9수01-01]", statement: "소인수분해의 뜻을 알고, 자연수를 소인수분해 할 수 있다.", domain: "수와 연산" },
  { grade: 1, subject: "수학", code: "[9수02-01]", statement: "다양한 상황을 문자를 사용한 식으로 나타낼 수 있다.", domain: "문자와 식" },
  { grade: 1, subject: "국어", code: "[9국02-01]", statement: "읽기는 글에 나타난 정보와 독자의 배경지식을 활용하여 문제를 해결하는 과정임을 이해한다.", domain: "읽기" },
  { grade: 2, subject: "영어", code: "[9영02-02]", statement: "자신이나 주변 사람 및 일상생활에 관해 묻거나 답할 수 있다.", domain: "말하기" },
];

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

export default function LibraryPage() {
  const [q, setQ] = useState("");
  const filteredStandards = STANDARDS.filter(
    (s) =>
      !q ||
      s.code.includes(q) ||
      s.statement.includes(q) ||
      s.subject.includes(q),
  );

  return (
    <AppShell title="라이브러리">
      <div className="mb-6">
        <p className="text-body-lg text-ink-gray">
          학교 전체에서 공유되는 성취기준·활동 태그·개인 즐겨찾기 템플릿입니다.
        </p>
      </div>
      <div className="mb-4 flex items-center gap-2 rounded-md border border-surface-border bg-white px-3 py-2">
        <Search className="h-4 w-4 text-ink-gray" />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="성취기준 코드·키워드 검색 (예: 9수, 토론)"
          className="flex-1 border-none bg-transparent text-body outline-none placeholder:text-ink-light"
        />
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
          <h2 className="mb-4 text-title font-bold">2022 개정 교육과정 · 중학교</h2>
          <ul className="space-y-3">
            {filteredStandards.map((s) => (
              <li key={s.code} className="card p-4">
                <div className="flex items-start gap-4">
                  <div className="flex gap-2">
                    <Badge tone="review">{s.subject}</Badge>
                    <Badge tone="neutral">{s.grade}학년</Badge>
                  </div>
                  <div className="flex-1">
                    <div className="font-mono text-body-sm font-semibold text-brand">
                      {s.code}
                    </div>
                    <div className="mt-1 text-body text-ink-dark">{s.statement}</div>
                    <div className="mt-1 text-caption text-ink-light">
                      {s.domain}
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
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
