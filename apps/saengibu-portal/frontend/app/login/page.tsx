"use client";

import { GoogleLogin } from "@react-oauth/google";
import { useGoogleLogin } from "@/lib/queries";
import { useRouter } from "next/navigation";
import { BookOpen, ShieldCheck } from "lucide-react";
import { useState } from "react";

export default function LoginPage() {
  const router = useRouter();
  const login = useGoogleLogin();
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-body px-4">
      <div className="w-full max-w-md rounded-xl border border-surface-border bg-white p-10 shadow-md">
        <div className="mb-8 flex items-center gap-3">
          <BookOpen className="h-6 w-6 text-brand" />
          <div className="text-lg font-bold leading-tight">
            학생부 AI 센터
            <br />
            <span className="text-sm font-medium text-ink-gray">
              교사 전용 포털
            </span>
          </div>
        </div>

        <h1 className="mb-2 text-2xl font-bold">로그인</h1>
        <p className="mb-8 text-sm text-ink-gray leading-relaxed">
          학교 구성원 전용 시스템입니다.
          <br />
          학교에서 발급받은 구글 계정으로 로그인해 주세요.
          <br />첫 로그인 시 관리자 승인이 필요합니다.
        </p>

        <div className="flex justify-center">
          <GoogleLogin
            onSuccess={async (res) => {
              setError(null);
              if (!res.credential) {
                setError("구글 인증 정보가 없습니다.");
                return;
              }
              try {
                const me = await login.mutateAsync({ credential: res.credential });
                if (me.status === "pending") {
                  router.push("/pending");
                } else {
                  router.push("/records");
                }
              } catch (e) {
                const msg =
                  e instanceof Error && e.message ? e.message : "로그인 실패";
                setError(msg);
              }
            }}
            onError={() => setError("구글 로그인에 실패했습니다.")}
            useOneTap={false}
            theme="outline"
            size="large"
            shape="pill"
            locale="ko"
          />
        </div>

        {error && (
          <div className="mt-6 rounded-md border border-danger/20 bg-red-50 p-3 text-sm text-danger">
            {error}
          </div>
        )}

        <div className="mt-10 flex items-start gap-2 rounded-md bg-pastel-mint p-4">
          <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-brand" />
          <div className="text-xs leading-relaxed text-ink-gray">
            본 시스템은 학교 외부로 학생 정보를 전송하지 않습니다. 모든 요청은
            학교 도메인 이메일만 허용되며, 접근 기록은 준영구 감사 로그로
            보존됩니다.
          </div>
        </div>
      </div>
    </div>
  );
}
