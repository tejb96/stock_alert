import type { Alert, AlertCreate, AlertUpdate, Health, Ratio } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type FetchOptions = {
  signal?: AbortSignal;
};

async function request<T>(
  path: string,
  init?: RequestInit & FetchOptions,
): Promise<T> {
  const { signal, ...rest } = init ?? {};
  const response = await fetch(`${API_URL}${path}`, {
    ...rest,
    signal,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...rest.headers,
    },
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(detail, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export function messageFromError(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return "Something went wrong";
}

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

export { isAbortError };

export async function getHealth(options?: FetchOptions): Promise<Health> {
  const data = await request<{ status: string }>("/health", {
    signal: options?.signal,
  });
  return { ok: data.status === "ok" };
}

export async function getRatio(options?: FetchOptions): Promise<Ratio> {
  return request<Ratio>("/ratio", { signal: options?.signal });
}

export async function listAlerts(options?: FetchOptions): Promise<Alert[]> {
  return request<Alert[]>("/alerts", { signal: options?.signal });
}

export async function createAlert(body: AlertCreate): Promise<Alert> {
  return request<Alert>("/alerts", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function updateAlert(
  id: number,
  body: AlertUpdate,
): Promise<Alert> {
  return request<Alert>(`/alerts/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export async function deleteAlert(id: number): Promise<void> {
  await request<void>(`/alerts/${id}`, { method: "DELETE" });
}

export async function testAlert(id: number): Promise<void> {
  await request<{ status: string }>(`/alerts/${id}/test`, {
    method: "POST",
  });
}
