"use client";

import { AppShell } from "@/components/layout/AppShell";
import { StatsCards } from "@/components/records/StatsCards";
import { ApprovalTable } from "@/components/records/ApprovalTable";
import { GuidelinesPanel } from "@/components/records/GuidelinesPanel";
import { DecisionsPanel } from "@/components/records/DecisionsPanel";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/Tabs";
import { useApprovals } from "@/lib/queries";

export default function RecordsPage() {
  const { data: approvals } = useApprovals("pending");
  const pendingCount = approvals?.length ?? 0;

  return (
    <AppShell title="생기부 통합 관리">
      <StatsCards />

      <Tabs
        defaultValue="approval"
        className="animate-fade-in"
        style={{ animationDelay: "0.2s" } as React.CSSProperties}
      >
        <TabsList>
          <TabsTrigger value="approval">
            승인 대기열 ({pendingCount})
          </TabsTrigger>
          <TabsTrigger value="guidelines">기재요령 안내</TabsTrigger>
          <TabsTrigger value="decisions">학교 결정사항</TabsTrigger>
        </TabsList>

        <TabsContent value="approval">
          <ApprovalTable />
        </TabsContent>
        <TabsContent value="guidelines">
          <GuidelinesPanel />
        </TabsContent>
        <TabsContent value="decisions">
          <DecisionsPanel />
        </TabsContent>
      </Tabs>
    </AppShell>
  );
}
