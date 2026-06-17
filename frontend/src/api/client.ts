import type { ScanTask, ScanCreateRequest, Finding, PaginatedResponse, ExperimentResults, AppSettings } from "../types";

const API_BASE = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API error ${res.status}: ${err}`);
  }
  if (res.status === 204) return undefined as unknown as T;
  return res.json() as Promise<T>;
}

export const api = {
  testConnection: () => request<{ success: boolean; message?: string; reply?: string }>("/settings/test", { method: "POST" }),
  health: () => request<{ status: string; version: string }>("/health"),

  listScans: (params?: { page?: number; page_size?: number; status?: string }) => {
    const q = new URLSearchParams();
    if (params?.page) q.set("page", String(params.page));
    if (params?.page_size) q.set("page_size", String(params.page_size));
    if (params?.status) q.set("status", params.status);
    const qs = q.toString();
    return request<PaginatedResponse<ScanTask>>(`/scans${qs ? `?${qs}` : ""}`);
  },
  getScan: (id: string) => request<ScanTask>(`/scans/${id}`),
  createScan: (data: ScanCreateRequest) =>
    request<ScanTask>("/scans", { method: "POST", body: JSON.stringify(data) }),
  deleteScan: (id: string) => request<void>(`/scans/${id}`, { method: "DELETE" }),

  listFindings: (params?: { page?: number; page_size?: number; scan_task_id?: string; scanner_name?: string; vulnerability_type?: string; severity?: string }) => {
    const q = new URLSearchParams();
    if (params?.page) q.set("page", String(params.page));
    if (params?.page_size) q.set("page_size", String(params.page_size));
    if (params?.scan_task_id) q.set("scan_task_id", params.scan_task_id);
    if (params?.scanner_name) q.set("scanner_name", params.scanner_name);
    if (params?.vulnerability_type) q.set("vulnerability_type", params.vulnerability_type);
    if (params?.severity) q.set("severity", params.severity);
    const qs = q.toString();
    return request<PaginatedResponse<Finding>>(`/findings${qs ? `?${qs}` : ""}`);
  },
  getFinding: (id: string) => request<Finding>(`/findings/${id}`),
  analyzeFinding: (id: string, strategy: string) =>
    request<{ id: string; verdict: string; confidence: number; reasoning: string }>(`/findings/${id}/analyze?strategy=${strategy}`, { method: "POST" }),

  getExperimentResults: () => request<ExperimentResults>("/experiment/results"),
  getSettings: () => request<AppSettings>("/settings"),
};
