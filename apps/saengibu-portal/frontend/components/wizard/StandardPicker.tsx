"use client";

import { useStandards } from "@/lib/queries";
import { AchievementLevelBadges } from "./AchievementLevelBadges";
import { Search, Check } from "lucide-react";
import { cn } from "@/lib/cn";
import { useState } from "react";
import type { Level } from "@/types/standards";

interface StandardPickerProps {
  schoolLevel: string;
  grade: number;
  subject?: string;
  /** 선택된 standard id 배열 (다중 선택) */
  value: number[];
  onChange: (ids: number[]) => void;
  /** 5단계 디스크립터 보기를 클릭했을 때 호출 */
  onShowDescriptor?: (id: number) => void;
}

export function StandardPicker({
  schoolLevel,
  grade,
  subject,
  value,
  onChange,
  onShowDescriptor,
}: StandardPickerProps) {
  const [search, setSearch] = useState("");
  const { data, isLoading } = useStandards({
    schoolLevel,
    grade,
    subject,
    search: search || undefined,
    limit: 50,
  });

  const toggle = (id: number) =>
    onChange(value.includes(id) ? value.filter((v) => v !== id) : [...value, id]);

  return (
    <div>
      <div className="mb-3 flex items-center gap-2 rounded-md border border-surface-border bg-white px-3 py-2">
        <Search className="h-4 w-4 text-ink-gray" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="성취기준 코드·키워드 검색 (예: 9수, 소인수)"
          className="flex-1 border-none bg-transparent text-body outline-none placeholder:text-ink-light"
          aria-label="성취기준 검색"
        />
      </div>

      {isLoading && (
        <div className="space-y-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="skeleton h-20 w-full" />
          ))}
        </div>
      )}

      {!isLoading && (data?.items.length ?? 0) === 0 && (
        <div className="rounded-md border border-surface-border bg-surface-body p-8 text-center text-body text-ink-gray">
          성취기준 데이터가 아직 등록되지 않았어요.
          <br />
          관리자가 시드를 적재하면 여기에 표시됩니다.
        </div>
      )}

      <ul className="space-y-2">
        {data?.items.map((s) => {
          const selected = value.includes(s.id);
          const availableLevels: Level[] = (s.levels?.map((l) => l.level) ??
            []) as Level[];
          return (
            <li
              key={s.id}
              className={cn(
                "rounded-md border p-4 transition",
                selected
                  ? "border-brand bg-brand-light"
                  : "border-surface-border bg-white hover:border-brand",
              )}
            >
              <div className="flex items-start gap-3">
                <button
                  type="button"
                  onClick={() => toggle(s.id)}
                  aria-pressed={selected}
                  className={cn(
                    "mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded border-2",
                    selected
                      ? "border-brand bg-brand text-white"
                      : "border-surface-border bg-white",
                  )}
                  aria-label={`${s.code} 선택`}
                >
                  {selected && <Check className="h-3 w-3" />}
                </button>
                <div className="flex-1">
                  <div className="font-mono text-body-sm font-semibold text-brand">
                    {s.code}
                  </div>
                  <div className="mt-0.5 text-body text-ink-dark">
                    {s.statement}
                  </div>
                  {s.domain && (
                    <div className="mt-1 text-caption text-ink-light">
                      {s.domain}
                      {s.unit_title ? ` · ${s.unit_title}` : ""}
                    </div>
                  )}
                  {availableLevels.length > 0 && (
                    <div className="mt-2 flex items-center justify-between">
                      <AchievementLevelBadges
                        available={availableLevels}
                        size="sm"
                      />
                      {onShowDescriptor && (
                        <button
                          type="button"
                          onClick={() => onShowDescriptor(s.id)}
                          className="text-caption font-semibold text-brand hover:underline"
                        >
                          5단계 보기
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
