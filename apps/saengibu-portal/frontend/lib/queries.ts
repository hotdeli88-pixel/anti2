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
