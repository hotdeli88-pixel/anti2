"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { useState, type ReactNode } from "react";

export function Providers({ children }: { children: ReactNode }) {
  const [qc] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            refetchOnWindowFocus: false,
            retry: 1,
          },
        },
      }),
  );
  // M-7: Google Client ID 미설정 시 silent fail 방지.
  const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
  if (!googleClientId && typeof window !== "undefined") {
    // eslint-disable-next-line no-console
    console.error(
      "[saengibu] NEXT_PUBLIC_GOOGLE_CLIENT_ID 환경 변수가 설정되지 않았습니다. " +
        "구글 로그인이 비활성화됩니다.",
    );
  }

  const tree = (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );

  if (!googleClientId) {
    return tree;
  }
  return <GoogleOAuthProvider clientId={googleClientId}>{tree}</GoogleOAuthProvider>;
}
