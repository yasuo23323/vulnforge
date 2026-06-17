export interface ScanTask {
  id: string; name: string; target_url: string; target_name: string | null;
  scanners: string[]; status: string; parameters: Record<string, unknown> | null;
  created_at: string; updated_at: string; started_at: string | null;
  completed_at: string | null; error_message: string | null; findings_count: number;
}

export interface ScanCreateRequest {
  name: string; target_url: string; target_name?: string;
  scanners?: string[]; parameters?: Record<string, unknown>; cookies?: string;
}

export interface LLMAnalysisResult {
  id: string; provider: string; model_name: string;
  strategy: "zero_shot" | "few_shot" | "chain_of_thought";
  verdict: "true_positive" | "false_positive" | "uncertain";
  confidence: number | null; reasoning: string | null;
  severity_reassessment: string | null;
  prompt_tokens: number | null; completion_tokens: number | null;
  latency_ms: number | null; created_at: string;
}

export interface Finding {
  id: string; scan_task_id: string; scanner_name: string;
  vulnerability_type: string; severity: string; url: string;
  request_data: string | null; response_data: string | null;
  raw_evidence: string | null; description: string | null;
  extra_data: Record<string, unknown> | null; created_at: string;
  llm_analyses: LLMAnalysisResult[];
}

export interface PaginatedResponse<T> { items: T[]; total: number; }

export interface ExperimentResults {
  dataset_size: number;
  ground_truth_distribution: { true_positive: number; false_positive: number };
  vulnerability_types: string[];
  results: Record<string, {
    confusion_matrix: { tp: number; fp: number; fn: number; tn: number };
    metrics: Record<string, number>;
    avg_latency: number; avg_tokens: number;
  }>;
}

export interface AppSettings {
  llm_provider: string; llm_model: string; database_type: string;
  openai_key_set: boolean; anthropic_key_set: boolean;
}

