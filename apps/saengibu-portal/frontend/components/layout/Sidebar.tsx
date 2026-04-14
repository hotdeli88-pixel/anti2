"use client";

import { cn } from "@/lib/cn";
import { BookOpen, Home, CheckCheck, Settings, type LucideIcon } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
}

const NAV: NavItem[] = [
  { href: "/dashboard", label: "대시보드", icon: Home },
  { href: "/records", label: "생기부 통합 관리", icon: CheckCheck },
  { href: "/settings", label: "환경 설정", icon: Settings },
];

export function Sidebar({ schoolName }: { schoolName: string }) {
  const pathname = usePathname();
  return (
    <aside className="flex w-[260px] flex-col border-r border-surface-border bg-white px-4 py-6 z-10">
      <div className="mb-10 flex items-center gap-2.5 pl-3">
        <BookOpen className="h-5 w-5 text-brand" />
        <span className="text-[17px] font-bold text-ink-dark leading-tight">
          {schoolName}
          <br />
          <span className="text-[15px] font-semibold text-ink-gray">
            학생부 AI 센터
          </span>
        </span>
      </div>
      <nav className="flex flex-col gap-1">
        {NAV.map((item) => {
          const active =
            pathname === item.href ||
            (item.href !== "/" && pathname.startsWith(item.href));
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-4 py-3.5 text-[15px] font-medium transition",
                active
                  ? "bg-brand-light text-brand"
                  : "text-ink-gray hover:bg-surface-body hover:text-ink-dark",
              )}
            >
              <Icon className="h-[18px] w-[18px]" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
