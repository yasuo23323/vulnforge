import os, json

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  Written: {path}")

root = "D:\\大论文\\frontend\\src"

# Load experiment results for the Results page
try:
    with open("D:\\大论文\\scripts\\experiment\\results.json") as f:
        results_data = json.load(f)
    results_json_str = json.dumps(results_data, indent=2)
except:
    results_json_str = "null"

# === API Client ===
write_file(f"{root}/api/client.ts", """import type { ScanTask, ScanCreateRequest, Finding, PaginatedResponse, ExperimentResults, AppSettings } from "../types";

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
""")

# === Dashboard ===
write_file(f"{root}/pages/Dashboard.tsx", """import React, { useEffect, useState } from "react";
import { Card, Row, Col, Statistic, Typography, Spin, Table, Tag } from "antd";
import { SecurityScanOutlined, CheckCircleOutlined, CloseCircleOutlined, WarningOutlined, ExperimentOutlined } from "@ant-design/icons";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { api } from "../api/client";
import type { ScanTask, ExperimentResults } from "../types";

const { Title } = Typography;
const COLORS = ["#cf1322", "#fa541c", "#faad14", "#1677ff", "#52c41a"];

const Dashboard: React.FC = () => {
  const [scans, setScans] = useState<ScanTask[]>([]);
  const [results, setResults] = useState<ExperimentResults | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.listScans({ page_size: 100 }).catch(() => ({ items: [], total: 0 })),
      api.getExperimentResults().catch(() => null)
    ]).then(([scanRes, expRes]) => {
      setScans(scanRes.items);
      setResults(expRes);
      setLoading(false);
    });
  }, []);

  if (loading) return <Spin size="large" style={{ display: "block", marginTop: 120 }} />;

  const completedScans = scans.filter(s => s.status === "completed").length;
  const runningScans = scans.filter(s => s.status === "running").length;
  const failedScans = scans.filter(s => s.status === "failed").length;
  const totalFindings = scans.reduce((acc, s) => acc + (s.findings_count || 0), 0);

  // Vulnerability type metrics from experiment results
  const vulnTypeData = results ? Object.entries(results.results).flatMap(([strategy, data]) => [{ strategy, ...data.metrics }]) : [];

  // Strategy comparison for chart
  const strategyChartData = results ? ["zero_shot", "few_shot", "chain_of_thought"].map(s => ({
    name: s === "zero_shot" ? "Zero-shot" : s === "few_shot" ? "Few-shot" : "CoT",
    Precision: results.results[s]?.metrics?.Precision || 0,
    Recall: results.results[s]?.metrics?.Recall || 0,
    F1: results.results[s]?.metrics?.["F1"] || 0,
    Accuracy: results.results[s]?.metrics?.Accuracy || 0,
  })) : [];

  // Scan distribution
  const scanStatusData = [
    { name: "Completed", value: completedScans, color: "#52c41a" },
    { name: "Running", value: runningScans, color: "#1677ff" },
    { name: "Failed", value: failedScans, color: "#cf1322" },
    { name: "Pending", value: scans.length - completedScans - runningScans - failedScans, color: "#d9d9d9" },
  ];

  const findingsColumns = [
    { title: "Scanner", dataIndex: "scanner_name", key: "scanner" },
    { title: "Type", dataIndex: "vulnerability_type", key: "type" },
    { title: "URL", dataIndex: "url", key: "url", ellipsis: true },
    { title: "Severity", dataIndex: "severity", key: "severity" },
  ];

  return (
    <div>
      <Title level={3}>Dashboard</Title>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card hoverable>
            <Statistic title="Total Scans" value={scans.length} prefix={<SecurityScanOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card hoverable>
            <Statistic title="Completed" value={completedScans} prefix={<CheckCircleOutlined />} valueStyle={{ color: "#3f8600" }} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card hoverable>
            <Statistic title="Total Findings" value={totalFindings} prefix={<CloseCircleOutlined />} valueStyle={{ color: "#cf1322" }} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card hoverable>
            <Statistic title="Dataset Size" value={results?.dataset_size || "-"} prefix={<ExperimentOutlined />} valueStyle={{ color: "#1677ff" }} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="Strategy Performance Comparison">
            {strategyChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={strategyChartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis domain={[0, 1]} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="Precision" fill="#1677ff" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="Recall" fill="#52c41a" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="F1" fill="#faad14" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p style={{ color: "#999", textAlign: "center", padding: 40 }}>Run an experiment to see strategy comparison charts</p>
            )}
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Scan Status Distribution">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={scanStatusData.filter(d => d.value > 0)} cx="50%" cy="50%" outerRadius={100}
                  dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                  {scanStatusData.filter(d => d.value > 0).map((entry, index) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {results && (
        <Card title="LLM Strategy Overview" style={{ marginTop: 24 }}>
          <Table dataSource={["zero_shot", "few_shot", "chain_of_thought"].map(s => ({
            key: s, strategy: s === "zero_shot" ? "Zero-shot" : s === "few_shot" ? "Few-shot" : "Chain-of-Thought",
            tp: results.results[s]?.confusion_matrix?.tp || 0,
            fp: results.results[s]?.confusion_matrix?.fp || 0,
            fn: results.results[s]?.confusion_matrix?.fn || 0,
            tn: results.results[s]?.confusion_matrix?.tn || 0,
            precision: (results.results[s]?.metrics?.Precision || 0).toFixed(3),
            recall: (results.results[s]?.metrics?.Recall || 0).toFixed(3),
            f1: (results.results[s]?.metrics?.["F1"] || 0).toFixed(3),
            accuracy: (results.results[s]?.metrics?.Accuracy || 0).toFixed(3),
            latency: results.results[s]?.avg_latency?.toFixed(2) || "-",
          }))} columns={[
            { title: "Strategy", dataIndex: "strategy", key: "strategy" },
            { title: "TP", dataIndex: "tp", key: "tp" },
            { title: "FP", dataIndex: "fp", key: "fp" },
            { title: "FN", dataIndex: "fn", key: "fn" },
            { title: "TN", dataIndex: "tn", key: "tn" },
            { title: "Precision", dataIndex: "precision", key: "precision" },
            { title: "Recall", dataIndex: "recall", key: "recall" },
            { title: "F1", dataIndex: "f1", key: "f1", render: (v: string) => <Tag color={parseFloat(v) >= 0.9 ? "green" : parseFloat(v) >= 0.7 ? "orange" : "red"}>{v}</Tag> },
            { title: "Accuracy", dataIndex: "accuracy", key: "accuracy" },
            { title: "Avg Lat (s)", dataIndex: "latency", key: "latency" },
          ]} pagination={false} size="small" />
        </Card>
      )}

      {scans.length > 0 && (
        <Card title="Recent Scans" style={{ marginTop: 24 }}>
          <Table dataSource={scans.slice(0, 10)} rowKey="id" pagination={false} size="small"
            columns={[
              { title: "Name", dataIndex: "name", key: "name" },
              { title: "Target", dataIndex: "target_url", key: "target", ellipsis: true },
              { title: "Status", dataIndex: "status", key: "status", render: (s: string) => <Tag>{s}</Tag> },
              { title: "Findings", dataIndex: "findings_count", key: "findings", render: (n: number) => n || "-" },
            ]} />
        </Card>
      )}
    </div>
  );
};
export default Dashboard;
""")

print("Complex pages generated")