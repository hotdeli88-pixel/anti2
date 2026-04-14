"use client";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "/api/v1";

export class ApiError extends Error {
  constructor(
    public status: number,
    public problem: { type?: string; title?: string; detail?: string } = {},
  ) {
    super(problem.title ?? `HTTP ${status}`);
  }
}

async function getCsrfToken(): Promise<string | null> {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}

export async function apiFetch<T = unknown>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  if (!headers.has("content-type") && init.body) {
    headers.set("content-type", "application/json");
  }
  const method = (init.method ?? "GET").toUpperCase();
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    const csrf = await getCsrfToken();
    if (csrf) headers.set("x-csrf-token", csrf);
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
    credentials: "include", // httpOnly 쿠키 세션
  });

  if (!res.ok) {
    let problem: { type?: string; title?: string; detail?: string } = {};
    try {
      problem = await res.json();
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, problem);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
