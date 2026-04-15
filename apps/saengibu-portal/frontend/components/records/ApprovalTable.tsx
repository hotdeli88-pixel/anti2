"use client";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Table, THead, TBody, TH, TR, TD } from "@/components/ui/Table";
import { useApprovals, useApprove } from "@/lib/queries";
import { Filter, Sparkles } from "lucide-react";
import { useMemo, useState } from "react";

function formatDate(iso: string): string {
  const d = new Date(iso);
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}.${p(d.getMonth() + 1)}.${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
}

const STATUS_LABEL: Record<string, string> = {
  pending: "대기중",
  guide_correction: "가이드 교정 요망",
  approved: "승인 완료",
  rejected: "반려됨",
};

const STATUS_TONE: Record<string, "pending" | "approved" | "danger" | "review"> = {
  pending: "pending",
  guide_correction: "pending",
  approved: "approved",
  rejected: "danger",
};

function SkeletonRows() {
  return (
    <>
      {Array.from({ length: 4 }).map((_, i) => (
        <TR key={i}>
          {Array.from({ length: 7 }).map((__, j) => (
            <TD key={j}>
              <div className="skeleton h-4 w-full max-w-[140px]" />
            </TD>
          ))}
        </TR>
      ))}
    </>
  );
}

interface ApprovalTableProps {
  /** 부모로부터 초기 필터 prop. 미지정 시 자체 필터 토글. */
  defaultStatus?: string;
}

export function ApprovalTable({ defaultStatus }: ApprovalTableProps = {}) {
  // M-5: 상위에서 동일 queryKey로 호출되는 케이스를 피하기 위해 prop 우선,
  // 토글은 같은 키 prop 갱신으로 단일 호출 유지.
  const [filter, setFilter] = useState<string | undefined>(defaultStatus);
  const { data, isLoading } = useApprovals(filter);
  const approve = useApprove();

  const rows = useMemo(() => data ?? [], [data]);

  return (
    <>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-bold">승인 요청 목록</h2>
        <Button onClick={() => setFilter(filter ? undefined : "pending")}>
          <Filter className="h-3.5 w-3.5" />
          {filter ? "전체" : "대기만"}
        </Button>
      </div>

      <Table>
        <caption className="sr-only">승인 대기 기록 목록</caption>
        <THead>
          <TR>
            <TH scope="col">학년/반</TH>
            <TH scope="col">이름</TH>
            <TH scope="col">영역</TH>
            <TH scope="col">제출일시</TH>
            <TH scope="col">AI 경보</TH>
            <TH scope="col">상태</TH>
            <TH scope="col">관리</TH>
          </TR>
        </THead>
        <TBody>
          {isLoading && <SkeletonRows />}
          {!isLoading && rows.length === 0 && (
            <TR>
              <TD colSpan={7} className="text-center py-10">
                {/* M-10: 빈 상태에 aria-live 보강 */}
                <div role="status" aria-live="polite">
                  <div className="text-heading font-semibold text-ink-dark">
                    오늘은 검토할 초안이 없어요
                  </div>
                  <div className="mt-1 text-body text-ink-gray">
                    모두 처리하셨어요. 잠깐 쉬어가도 좋아요.
                  </div>
                </div>
              </TD>
            </TR>
          )}
          {rows.map((r) => (
            <TR key={r.review_id}>
              <TD>
                {r.student.grade}학년 {r.student.class_no}반
              </TD>
              <TD className="font-semibold">{r.student.name_masked}</TD>
              <TD>{r.section.name}</TD>
              <TD className="text-ink-gray">{formatDate(r.submitted_at)}</TD>
              <TD>
                {r.ai_warn_count > 0 ? (
                  <span className="badge badge-ai inline-flex items-center gap-1">
                    <Sparkles className="h-3 w-3" />
                    {r.ai_warn_count}건
                  </span>
                ) : (
                  <span className="text-ink-light text-caption">—</span>
                )}
              </TD>
              <TD>
                <Badge tone={STATUS_TONE[r.status] ?? "neutral"}>
                  {STATUS_LABEL[r.status] ?? r.status}
                </Badge>
              </TD>
              <TD>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm">
                    상세보기
                  </Button>
                  <Button
                    variant="primary"
                    size="sm"
                    disabled={r.status === "approved" || approve.isPending}
                    onClick={() =>
                      approve.mutate({
                        reviewId: r.review_id,
                        stepNo: r.step_no,
                      })
                    }
                  >
                    {r.status === "approved" ? "완료" : "승인"}
                  </Button>
                </div>
              </TD>
            </TR>
          ))}
        </TBody>
      </Table>
    </>
  );
}
