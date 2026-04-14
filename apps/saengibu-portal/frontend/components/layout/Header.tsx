"use client";

import { useLogout } from "@/lib/queries";
import { LogOut } from "lucide-react";

interface HeaderProps {
  title: string;
  userName: string;
}

export function Header({ title, userName }: HeaderProps) {
  const logout = useLogout();
  const initial = userName.slice(0, 1);

  return (
    <header className="sticky top-0 z-[5] flex h-[72px] items-center justify-between px-10 backdrop-blur-md bg-surface-body/80">
      <h1 className="text-xl font-bold">{title}</h1>
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium">{userName} 선생님</span>
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-brand font-semibold text-white">
          {initial}
        </div>
        <button
          onClick={() => logout.mutate()}
          className="ml-2 flex h-9 w-9 items-center justify-center rounded-full text-ink-gray hover:bg-surface-body hover:text-ink-dark transition"
          title="로그아웃"
          aria-label="로그아웃"
        >
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    </header>
  );
}
