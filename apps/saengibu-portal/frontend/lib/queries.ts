"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "./api";
import type {
  ApprovalItem,
  DashboardStats,
  Guideline,
  MeResponse,
  SchoolDecision,
} from "@/types/record";
import type {
  AchievementLevel,
  AchievementStandard,
  CurriculumMatrixEntry,
  DomainLevel,
  StandardsListPage,
} from "@/types/standards";

export function useMe() {
  return useQuery<MeResponse | null>({
    queryKey: ["me"],
    queryFn: async () => {
      try {
        return await apiFetch<MeResponse>("/auth/me");
      } catch {
        return null;
      }
    },
    staleTime: 60_000,
  });
}

export function useDashboardStats() {
  return useQuery<DashboardStats>({
    queryKey: ["dashboard", "stats"],
    queryFn: () => apiFetch<DashboardStats>("/dashboard/teacher"),
  });
}

export function useApprovals(status?: string) {
  const qs = status ? `?status=${encodeURIComponent(status)}` : "";
  return useQuery<ApprovalItem[]>({
    queryKey: ["approvals", status ?? "all"],
    queryFn: () => apiFetch<ApprovalItem[]>(`/reviews/assigned${qs}`),
  });
}

export function useApprove() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ reviewId, stepNo }: { reviewId: string; stepNo: number }) =>
      apiFetch(`/reviews/${reviewId}/steps/${stepNo}/decide`, {
        method: "POST",
        body: JSON.stringify({ decision: "approved" }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["approvals"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useReject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      reviewId,
      stepNo,
      comment,
    }: {
      reviewId: string;
      stepNo: number;
      comment: string;
    }) =>
      apiFetch(`/reviews/${reviewId}/steps/${stepNo}/decide`, {
        method: "POST",
        body: JSON.stringify({ decision: "rejected", comment }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["approvals"] }),
  });
}

export function useGuidelines() {
  return useQuery<Guideline[]>({
    queryKey: ["guidelines"],
    queryFn: () => apiFetch<Guideline[]>("/guidelines"),
  });
}

export function useSchoolDecisions() {
  return useQuery<SchoolDecision[]>({
    queryKey: ["school-decisions"],
    queryFn: () => apiFetch<SchoolDecision[]>("/school-decisions"),
  });
}

export function useLogout() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => apiFetch("/auth/logout", { method: "POST" }),
    onSuccess: () => {
      qc.clear();
      window.location.href = "/login";
    },
  });
}

export function useGoogleLogin() {
  return useMutation<MeResponse, Error, { credential: string }>({
    mutationFn: ({ credential }) =>
      apiFetch<MeResponse>("/auth/google", {
        method: "POST",
        body: JSON.stringify({ credential }),
      }),
  });
}

// ===== Sprint 1: Standards / Levels / Domain levels / Curricula =====

interface StandardsFilter {
  schoolLevel?: string;
  grade?: number;
  subject?: string;
  search?: string;
  cursor?: string;
  limit?: number;
}

function standardsQs(f: StandardsFilter): string {
  const params = new URLSearchParams();
  if (f.schoolLevel) params.set("school_level", f.schoolLevel);
  if (f.grade != null) params.set("grade", String(f.grade));
  if (f.subject) params.set("subject", f.subject);
  if (f.search) params.set("search", f.search);
  if (f.cursor) params.set("cursor", f.cursor);
  if (f.limit) params.set("limit", String(f.limit));
  const q = params.toString();
  return q ? `?${q}` : "";
}

export function useStandards(filter: StandardsFilter = {}) {
  return useQuery<StandardsListPage>({
    queryKey: ["standards", filter],
    queryFn: () => apiFetch<StandardsListPage>(`/standards${standardsQs(filter)}`),
    staleTime: 10 * 60 * 1000,
  });
}

export function useStandard(standardId: number | undefined) {
  return useQuery<AchievementStandard>({
    queryKey: ["standard", standardId],
    queryFn: () => apiFetch<AchievementStandard>(`/standards/${standardId}`),
    enabled: standardId != null,
    staleTime: 10 * 60 * 1000,
  });
}

export function useStandardLevels(standardId: number | undefined) {
  return useQuery<AchievementLevel[]>({
    queryKey: ["standard-levels", standardId],
    queryFn: () => apiFetch<AchievementLevel[]>(`/standards/${standardId}/levels`),
    enabled: standardId != null,
    staleTime: 10 * 60 * 1000,
  });
}

interface DomainLevelsFilter {
  schoolLevel?: string;
  grade?: number;
  subject?: string;
  domain?: string;
}

export function useDomainLevels(filter: DomainLevelsFilter = {}) {
  const params = new URLSearchParams();
  if (filter.schoolLevel) params.set("school_level", filter.schoolLevel);
  if (filter.grade != null) params.set("grade", String(filter.grade));
  if (filter.subject) params.set("subject", filter.subject);
  if (filter.domain) params.set("domain", filter.domain);
  const q = params.toString();
  return useQuery<DomainLevel[]>({
    queryKey: ["domain-levels", filter],
    queryFn: () => apiFetch<DomainLevel[]>(`/domain-levels${q ? `?${q}` : ""}`),
    staleTime: 10 * 60 * 1000,
  });
}

export function useCurricula() {
  return useQuery<CurriculumMatrixEntry[]>({
    queryKey: ["curricula"],
    queryFn: () => apiFetch<CurriculumMatrixEntry[]>("/curricula"),
    staleTime: 30 * 60 * 1000,
  });
}
