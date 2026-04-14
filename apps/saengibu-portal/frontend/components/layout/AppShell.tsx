"use client";

import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { useMe } from "@/lib/queries";
import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

export function AppShell({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  const router = useRouter();
  const { data: me, isLoading } = useMe();

  useEffect(() => {
    if (!isLoading && !me) router.replace("/login");
    else if (me && me.status === "pending") router.replace("/pending");
  }, [me, isLoading, router]);

  if (isLoading || !me) {
    return (
      <div className="flex h-screen items-center justify-center text-ink-gray">
        로딩 중…
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar schoolName={me.school.name} />
      <main className="relative flex flex-1 flex-col overflow-y-auto">
        <Header title={title} userName={me.name} />
        <div className="mx-auto w-full max-w-[1200px] px-10 pb-[60px] pt-6">
          {children}
        </div>
      </main>
    </div>
  );
}
