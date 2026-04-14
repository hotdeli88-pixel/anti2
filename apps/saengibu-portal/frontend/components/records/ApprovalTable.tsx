"use client";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Table, THead, TBody, TH, TR, TD } from "@/components/ui/Table";
import { useApprovals, useApprove } from "@/lib/queries";
import { Filter } from "lucide-react";
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

export function ApprovalTable() {
  const [filter, setFilter] = useState<string | undefined>();
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
        <THead>
          <TR>
            <TH>학년/반</TH>
            <TH>이름</TH>
            <TH>영역</TH>
            <TH>제출일시</TH>
            <TH>상태</TH>
            <TH>관리</TH>
          </TR>
        </THead>
        <TBody>
          {isLoading && (
            <TR>
              <TD colSpan={6} className="text-center text-ink-gray">
                불러오는 중…
              </TD>
            </TR>
          )}
          {!isLoading && rows.length === 0 && (
            <TR>
              <TD colSpan={6} className="text-center text-ink-gray">
                승인 대기 요청이 없습니다.
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
