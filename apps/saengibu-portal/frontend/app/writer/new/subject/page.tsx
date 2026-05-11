"use client";

import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { WizardSteps, type WizardStep } from "@/components/wizard/WizardSteps";
import { TagChipGroup, type TagItem } from "@/components/wizard/TagChipGroup";
import { ByteMeter } from "@/components/wizard/ByteMeter";
import { FileUploader } from "@/components/wizard/FileUploader";
import { ArrowLeft, ArrowRight, Shield, MessageSquareWarning, Check } from "lucide-react";
import { useState } from "react";

const STEPS: WizardStep[] = [
  { id: "target", label: "학생·과목 선택", hint: "학급·학생·단원" },
  { id: "standards", label: "성취기준 선택", hint: "2022 개정 교육과정" },
  { id: "tags", label: "활동·학생 특성", hint: "관찰 체크리스트" },
  { id: "draft", label: "초안 작성", hint: "교사 직접 입력" },
  { id: "feedback", label: "AI 관점 점검", hint: "검토 제안 확인" },
  { id: "submit", label: "1검 제출", hint: "확인 체크리스트" },
];

const MATH_STANDARDS: Array<{ code: string; statement: string }> = [
  { code: "[9수01-01]", statement: "소인수분해의 뜻을 알고, 자연수를 소인수분해 할 수 있다." },
  { code: "[9수01-02]", statement: "최대공약수와 최소공배수의 성질을 이해하고, 이를 구할 수 있다." },
  { code: "[9수02-01]", statement: "다양한 상황을 문자를 사용한 식으로 나타낼 수 있다." },
  { code: "[9수03-01]", statement: "좌표평면을 이해하고, 순서쌍과 좌표를 표현할 수 있다." },
];

const ACTIVITY_TAGS: TagItem[] = [
  { id: "t1", label: "문제풀이 활동", category: "수업활동" },
  { id: "t2", label: "창의적 사고 활동" },
  { id: "t3", label: "교구 활용 활동" },
  { id: "t4", label: "개별 학습 활동" },
  { id: "t5", label: "탐구 보고서 작성" },
  { id: "t6", label: "자료 해석 활동" },
  { id: "t7", label: "그래프 그리기 활동" },
  { id: "t8", label: "실생활 연계 활동" },
];

const ROLE_TAGS: TagItem[] = [
  { id: "r1", label: "과목 부장을 맡음" },
  { id: "r2", label: "모둠장을 맡음" },
  { id: "r3", label: "모둠원으로 활동함" },
];

const TRAIT_TAGS: TagItem[] = [
  { id: "p1", label: "개념에 대한 이해가 빠름" },
  { id: "p2", label: "원리나 개념의 융합 능력이 좋음" },
  { id: "p3", label: "논리적 사고력이 우수함" },
  { id: "p4", label: "난이도 높은 개념을 쉽게 이해함" },
  { id: "p5", label: "도형 및 공간 감각이 뛰어남" },
];

const SECTION_BYTE_LIMIT = 1500; // 과목별 세특 (500자 × 3B = 1,500B)

export default function SubjectWriterWizardPage() {
  const [current, setCurrent] = useState(0);
  const [completed, setCompleted] = useState<number[]>([]);
  const [targetStudent] = useState({ grade: 1, klass: 3, name: "홍**", no: "1030101" });
  const [subject] = useState("수학");
  const [standards, setStandards] = useState<string[]>([]);
  const [activities, setActivities] = useState<string[]>([]);
  const [roles, setRoles] = useState<string[]>([]);
  const [traits, setTraits] = useState<string[]>([]);
  const [draft, setDraft] = useState("");
  const [checklist, setChecklist] = useState({
    noFabrication: false,
    guidelinesReviewed: false,
    ownSentence: false,
  });

  const next = () => {
    setCompleted((c) => Array.from(new Set([...c, current])));
    setCurrent((c) => Math.min(c + 1, STEPS.length - 1));
  };
  const prev = () => setCurrent((c) => Math.max(c - 1, 0));

  const allChecked =
    checklist.noFabrication && checklist.guidelinesReviewed && checklist.ownSentence;

  return (
    <AppShell title="과목 세특 작성">
      <div className="mb-8">
        <WizardSteps
          steps={STEPS}
          current={current}
          completed={completed}
          onStepClick={(idx) => setCurrent(idx)}
        />
      </div>

      <div className="card p-8 min-h-[520px]">
        {current === 0 && (
          <section>
            <h2 className="text-heading font-bold text-ink-dark">학생과 과목을 선택하세요</h2>
            <p className="mt-1 text-body text-ink-gray">
              본인이 담당하는 학급·학생·과목·단원만 선택 가능합니다. (데모에서는 단일 값 고정)
            </p>
            <dl className="mt-6 grid grid-cols-[100px_1fr] gap-y-3 text-body-lg">
              <dt className="text-ink-gray">학년/반</dt>
              <dd className="font-semibold">
                {targetStudent.grade}학년 {targetStudent.klass}반
              </dd>
              <dt className="text-ink-gray">학생</dt>
              <dd className="font-semibold">
                {targetStudent.name} ({targetStudent.no})
              </dd>
              <dt className="text-ink-gray">과목</dt>
              <dd className="font-semibold">{subject} (중학교 1학년)</dd>
              <dt className="text-ink-gray">단원</dt>
              <dd>자동 선택 · 수와 연산</dd>
            </dl>
          </section>
        )}

        {current === 1 && (
          <section>
            <h2 className="text-heading font-bold text-ink-dark">성취기준 선택</h2>
            <p className="mt-1 text-body text-ink-gray">
              2022 개정 교육과정 기준입니다. 최소 1개 이상 선택해 주세요.
            </p>
            <ul className="mt-6 space-y-2">
              {MATH_STANDARDS.map((s) => {
                const sel = standards.includes(s.code);
                return (
                  <li key={s.code}>
                    <button
                      type="button"
                      onClick={() =>
                        setStandards((curr) =>
                          curr.includes(s.code)
                            ? curr.filter((c) => c !== s.code)
                            : [...curr, s.code],
                        )
                      }
                      className={`w-full text-left rounded-md border p-4 transition ${sel ? "border-brand bg-brand-light" : "border-surface-border bg-white hover:border-brand"}`}
                      aria-pressed={sel}
                    >
                      <div className="flex items-start gap-3">
                        <span
                          className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded border-2 ${sel ? "border-brand bg-brand text-white" : "border-surface-border bg-white"}`}
                        >
                          {sel && <Check className="h-3 w-3" />}
                        </span>
                        <div>
                          <div className="font-mono text-body-sm font-semibold text-brand">
                            {s.code}
                          </div>
                          <div className="mt-0.5 text-body text-ink-dark">
                            {s.statement}
                          </div>
                        </div>
                      </div>
                    </button>
                  </li>
                );
              })}
            </ul>
          </section>
        )}

        {current === 2 && (
          <section className="space-y-6">
            <h2 className="text-heading font-bold text-ink-dark">
              관찰한 활동·역할·학생 특성
            </h2>
            <p className="text-body text-ink-gray">
              단서 제공용 체크리스트입니다. AI가 이 정보를 바탕으로 "고려할 관점"만 제시합니다.
            </p>
            <TagChipGroup
              label="수업 활동 유형"
              hint="2개 이내 권장"
              tags={ACTIVITY_TAGS}
              value={activities}
              onChange={setActivities}
              max={2}
            />
            <TagChipGroup
              label="역할 수행"
              hint="1개 권장"
              tags={ROLE_TAGS}
              value={roles}
              onChange={setRoles}
              max={1}
            />
            <TagChipGroup
              label="학생 수업 특성"
              hint="2개 이내 권장"
              tags={TRAIT_TAGS}
              value={traits}
              onChange={setTraits}
              max={2}
            />
          </section>
        )}

        {current === 3 && (
          <section className="space-y-4">
            <div>
              <h2 className="text-heading font-bold text-ink-dark">
                교사 초안을 직접 작성하세요
              </h2>
              <p className="mt-1 text-body text-ink-gray">
                훈령에 따라 AI가 대신 쓰지 않습니다. 관찰 내용을 선생님의 언어로 먼저 기록해 주세요.
              </p>
            </div>
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              rows={10}
              className="w-full resize-y rounded-md border border-surface-border bg-white p-4 text-body-lg leading-relaxed focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/30"
              placeholder="예) 수와 연산 단원 학습에서 소인수분해와 최대공약수를 활용해 …"
              aria-label="초안 입력"
            />
            <ByteMeter value={draft} limit={SECTION_BYTE_LIMIT} />
            <div className="mt-4">
              <h3 className="mb-2 text-body-sm font-semibold text-ink-dark">
                학생 과제 업로드 (선택)
              </h3>
              <FileUploader />
            </div>
          </section>
        )}

        {current === 4 && (
          <section>
            <h2 className="text-heading font-bold text-ink-dark">AI 관점 점검</h2>
            <p className="mt-1 text-body text-ink-gray">
              초안을 기반으로 <b>문장을 대신 쓰지 않고</b>, 누락된 관점과 재확인할 포인트만 제시합니다.
            </p>
            <div className="mt-6 space-y-3">
              <div className="rounded-md border border-info/30 bg-info-bg p-4">
                <div className="flex items-start gap-3">
                  <MessageSquareWarning className="mt-0.5 h-5 w-5 text-info" />
                  <div>
                    <h4 className="font-semibold text-ink-dark">
                      Byte 사용량 {SECTION_BYTE_LIMIT}B 중 {cp949Approx(draft)}B
                    </h4>
                    <p className="mt-1 text-body text-ink-gray">
                      현재 여유분이 충분합니다. 구체적 성취 과정을 1-2문장 더 보강해 보세요.
                    </p>
                  </div>
                </div>
              </div>
              <div className="rounded-md border border-warn/30 bg-warn-bg p-4">
                <div className="flex items-start gap-3">
                  <Shield className="mt-0.5 h-5 w-5 text-warn" />
                  <div>
                    <h4 className="font-semibold text-ink-dark">
                      성취기준 연계 서술이 약합니다
                    </h4>
                    <p className="mt-1 text-body text-ink-gray">
                      선택한 {standards.length}개의 성취기준 중 <b>구체적 수행 사례</b>가
                      드러나는지 한 번 더 확인해 주세요. (근거: 훈령 제555호 제15조)
                    </p>
                  </div>
                </div>
              </div>
              <div className="rounded-md border border-ok/30 bg-ok-bg p-4">
                <div className="flex items-start gap-3">
                  <Check className="mt-0.5 h-5 w-5 text-ok" />
                  <div>
                    <h4 className="font-semibold text-ink-dark">
                      금지 표현·실명 노출 없음
                    </h4>
                    <p className="mt-1 text-body text-ink-gray">
                      공인어학시험, 부모 직업, 대학명 등 기재 금지 항목이 감지되지 않았습니다.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {current === 5 && (
          <section>
            <h2 className="text-heading font-bold text-ink-dark">확인 후 1검 제출</h2>
            <p className="mt-1 text-body text-ink-gray">
              훈령 제555호 2026 신설 조항에 따라 최종 입력 전 아래 3가지를 반드시 확인해 주세요.
            </p>
            <div className="mt-6 space-y-3">
              {[
                {
                  key: "noFabrication" as const,
                  label: "학생의 실제 수행과 무관한 허위·과장 내용이 없음을 확인했습니다.",
                },
                {
                  key: "guidelinesReviewed" as const,
                  label: "기재요령의 각종 유의사항을 재확인했습니다.",
                },
                {
                  key: "ownSentence" as const,
                  label: "AI 피드백을 참고했으나, 문장은 제가 직접 작성했습니다.",
                },
              ].map((c) => (
                <label
                  key={c.key}
                  className="flex cursor-pointer items-start gap-3 rounded-md border border-surface-border bg-surface-body p-4 hover:bg-white"
                >
                  <input
                    type="checkbox"
                    checked={checklist[c.key]}
                    onChange={(e) =>
                      setChecklist((prev) => ({ ...prev, [c.key]: e.target.checked }))
                    }
                    className="mt-0.5 h-5 w-5 accent-brand"
                  />
                  <span className="text-body-lg text-ink-dark">{c.label}</span>
                </label>
              ))}
              <Button
                variant="primary"
                disabled={!allChecked}
                className="mt-4 w-full"
              >
                {allChecked ? "1검 제출하기" : "모든 항목을 확인해 주세요"}
              </Button>
            </div>
          </section>
        )}
      </div>

      {/* Navigation */}
      <div className="mt-6 flex items-center justify-between">
        <Button
          onClick={prev}
          disabled={current === 0}
          className="gap-2"
          variant="default"
        >
          <ArrowLeft className="h-4 w-4" /> 이전
        </Button>
        <span className="text-caption text-ink-light">
          {current + 1} / {STEPS.length} 단계
        </span>
        <Button
          onClick={next}
          disabled={current === STEPS.length - 1}
          variant="primary"
          className="gap-2"
        >
          다음 <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </AppShell>
  );
}

function cp949Approx(text: string): number {
  let bytes = 0;
  for (const ch of text.replace(/\n/g, "\r\n")) {
    const code = ch.codePointAt(0) ?? 0;
    bytes += code < 0x80 ? 1 : 2;
  }
  return bytes;
}
