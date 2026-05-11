"use client";

import { useLogout, useMe } from "@/lib/queries";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Clock, LogOut } from "lucide-react";

export default function PendingPage() {
  const { data: me, isLoading } = useMe();
  const router = useRouter();
  const logout = useLogout();

  useEffect(() => {
    if (!isLoading && !me) router.replace("/login");
    else if (me && me.status === "active") router.replace("/records");
  }, [me, isLoading, router]);

  if (!me) return null;

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-body px-4">
      <div className="w-full max-w-lg rounded-xl border border-surface-border bg-white p-10 text-center shadow-md">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-pastel-yellow">
          <Clock className="h-8 w-8 text-warn" />
        </div>
        <h1 className="mb-3 text-2xl font-bold">관리자 승인 대기 중</h1>
        <p className="mb-8 text-sm leading-relaxed text-ink-gray">
          <b>{me.name}</b> ({me.email}) 님의 가입 요청이 접수되었습니다.
          <br />
          학교 관리자의 승인 후 시스템을 사용하실 수 있습니다.
          <br />
          승인 처리는 보통 1영업일 이내에 완료됩니다.
        </p>

        <div className="mb-6 rounded-md bg-pastel-mint p-4 text-left text-[13px] leading-relaxed text-ink-gray">
          <b className="text-ink-dark">확인 사항</b>
          <ul className="mt-2 list-disc pl-5 space-y-1">
            <li>학교 도메인 이메일로 가입했는지 확인해 주세요.</li>
            <li>교직원 번호·담당 학급/교과가 정확해야 빠르게 승인됩니다.</li>
            <li>문의: 학교 교무부 또는 시스템 관리자</li>
          </ul>
        </div>

        <button
          onClick={() => logout.mutate()}
          className="btn inline-flex items-center gap-2 text-ink-gray"
        >
          <LogOut className="h-4 w-4" />
          로그아웃
        </button>
      </div>
    </div>
  );
}
