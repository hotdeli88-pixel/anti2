"use client";

import { cn } from "@/lib/cn";
import {
  BookOpen,
  Home,
  CheckCheck,
  Settings,
  PenLine,
  Users,
  Megaphone,
  BookMarked,
  type LucideIcon,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
  section?: string;
}

const NAV: NavItem[] = [
  { href: "/dashboard", label: "홈", icon: Home, section: "overview" },
  { href: "/records", label: "결재 대기열", icon: CheckCheck, section: "overview" },
  { href: "/writer", label: "세특 작성", icon: PenLine, section: "write" },
  { href: "/homeroom", label: "담임 전용", icon: Users, section: "write" },
  { href: "/library", label: "라이브러리", icon: BookMarked, section: "reference" },
  { href: "/board", label: "공지·게시판", icon: Megaphone, section: "reference" },
  { href: "/settings", label: "환경 설정", icon: Settings, section: "system" },
];

const SECTION_LABELS: Record<string, string> = {
  overview: "대시보드",
  write: "작성",
  reference: "참고",
  system: "시스템",
};

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
        {renderSections(pathname)}
      </nav>
    </aside>
  );
}

function renderSections(pathname: string) {
  const groups = NAV.reduce<Record<string, NavItem[]>>((acc, item) => {
    const key = item.section ?? "other";
    (acc[key] ??= []).push(item);
    return acc;
  }, {});
  const order = ["overview", "write", "reference", "system"];
  return order
    .filter((s) => groups[s]?.length)
    .map((s, idx) => (
      <div key={s} className={idx === 0 ? "" : "mt-4"}>
        <div className="px-4 py-1 text-[11px] font-semibold uppercase tracking-wider text-ink-light">
          {SECTION_LABELS[s]}
        </div>
        {groups[s].map((item) => {
          const active =
            pathname === item.href ||
            (item.href !== "/" && pathname.startsWith(item.href));
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-4 py-3 text-body-lg font-medium transition-colors duration-quick",
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
      </div>
    ));
}
