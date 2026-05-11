"use client";

import { AppShell } from "@/components/layout/AppShell";
import { useMe } from "@/lib/queries";

export default function SettingsPage() {
  const { data: me } = useMe();
  return (
    <AppShell title="환경 설정">
      <div className="card p-6">
        <h2 className="mb-4 text-lg font-bold">내 정보</h2>
        {me && (
          <dl className="grid grid-cols-[120px_1fr] gap-y-3 text-sm">
            <dt className="text-ink-gray">이름</dt>
            <dd>{me.name}</dd>
            <dt className="text-ink-gray">이메일</dt>
            <dd>{me.email}</dd>
            <dt className="text-ink-gray">학교</dt>
            <dd>{me.school.name}</dd>
            <dt className="text-ink-gray">역할</dt>
            <dd>{me.roles.join(", ") || "-"}</dd>
            <dt className="text-ink-gray">담임</dt>
            <dd>
              {me.homeroom_of.length
                ? me.homeroom_of.map((c) => c.label).join(", ")
                : "-"}
            </dd>
          </dl>
        )}
      </div>
    </AppShell>
  );
}
