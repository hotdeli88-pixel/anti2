"use client";

import { AppShell } from "@/components/layout/AppShell";
import { Badge } from "@/components/ui/Badge";
import { Megaphone, Pin } from "lucide-react";

const POSTS = [
  {
    id: "p1",
    category: "announcement",
    title: "2026학년도 1학기 생기부 마감 일정 안내",
    summary: "1차 작성 마감 7/10, 1검 7/12, 2검 7/14, 최종 3검 7/15. 기한 준수 바랍니다.",
    author: "교무부",
    date: "2026-04-14",
    pinned: true,
  },
  {
    id: "p2",
    category: "training",
    title: "훈령 제555호 2026 AI 활용 유의사항 연수 안내",
    summary: "4/20(월) 오후 3시 시청각실. 자료는 공유 폴더에 업로드됩니다.",
    author: "연구부",
    date: "2026-04-12",
    pinned: false,
  },
  {
    id: "p3",
    category: "library",
    title: "학교 자체 허용 도서 리스트 등록 안내",
    summary: "올해 독서활동 인정 도서 목록을 라이브러리에 등록했습니다. 확인 부탁드립니다.",
    author: "도서부",
    date: "2026-04-08",
    pinned: false,
  },
  {
    id: "p4",
    category: "faq",
    title: "자주 묻는 질문: Byte 수 계산 방식",
    summary: "NEIS와 동일하게 CP949 기준. 한글 2B, 영문 1B, 엔터 2B. 이모지·확장 한자는 금지.",
    author: "시스템 관리자",
    date: "2026-04-05",
    pinned: false,
  },
];

const CATEGORY_LABEL: Record<string, string> = {
  announcement: "공지",
  training: "연수",
  library: "자료",
  faq: "FAQ",
  release: "업데이트",
};

const CATEGORY_TONE: Record<string, "review" | "pending" | "approved" | "neutral"> = {
  announcement: "review",
  training: "pending",
  library: "approved",
  faq: "neutral",
  release: "approved",
};

export default function BoardPage() {
  return (
    <AppShell title="공지·게시판">
      <div className="mb-6">
        <p className="text-body-lg text-ink-gray">
          학교 운영 관련 공지, 훈령 변경사항, 연수 안내, 자주 묻는 질문을 확인하세요.
        </p>
      </div>

      <ul className="space-y-3">
        {POSTS.map((p) => (
          <li
            key={p.id}
            className="card flex items-start gap-4 p-5 transition hover:-translate-y-0.5 hover:shadow-hover"
          >
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand-light text-brand">
              {p.pinned ? (
                <Pin className="h-5 w-5" />
              ) : (
                <Megaphone className="h-5 w-5" />
              )}
            </div>
            <div className="flex-1">
              <div className="mb-1 flex items-center gap-2">
                <Badge tone={CATEGORY_TONE[p.category] ?? "neutral"}>
                  {CATEGORY_LABEL[p.category] ?? p.category}
                </Badge>
                {p.pinned && (
                  <Badge tone="pending">
                    고정
                  </Badge>
                )}
              </div>
              <h3 className="text-title font-semibold text-ink-dark">{p.title}</h3>
              <p className="mt-1 text-body text-ink-gray">{p.summary}</p>
              <div className="mt-2 text-caption text-ink-light">
                {p.author} · {p.date}
              </div>
            </div>
          </li>
        ))}
      </ul>
    </AppShell>
  );
}
