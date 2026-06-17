import os

def w(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  {os.path.basename(path)}")

root = "D:\\大论文\\frontend\\src"

# Update api/client.ts
p = f"{root}/api/client.ts"
with open(p, "r") as f:
    c = f.read()
if "testConnection" not in c:
    c = c.replace(
        "export const api = {",
        "export const api = {\n  testConnection: () => request<{ success: boolean; message?: string; reply?: string }>(\"/settings/test\", { method: \"POST\" }),"
    )
    with open(p, "w") as f:
        f.write(c)
    print("  client.ts updated")
else:
    print("  client.ts already has testConnection")

# ScanDetail.tsx with auto-refresh and export
w(f"{root}/pages/ScanDetail.tsx", """import React, { useEffect, useState, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, Descriptions, Tag, Typography, Table, Spin, Button, Space, Divider, Progress, message } from "antd";
import { ArrowLeftOutlined, DownloadOutlined } from "@ant-design/icons";
import { api } from "../api/client";
import type { ScanTask, Finding, LLMAnalysisResult } from "../types";
import { exportToCSV } from "../utils/export";

const { Title, Text, Paragraph } = Typography;
const statusColors: Record<string, string> = { pending: "default", running: "processing", completed: "success", failed: "error", cancelled: "warning" };
const severityColors: Record<string, string> = { critical: "red", high: "orange", medium: "gold", low: "blue", info: "default" };
const verdictColors: Record<string, string> = { true_positive: "green", false_positive: "red", uncertain: "orange" };
const strategyLabels: Record<string, string> = { zero_shot: "Zero-shot", few_shot: "Few-shot", chain_of_thought: "CoT" };

const ScanDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [scan, setScan] = useState<ScanTask | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    if (!id) return;
    try {
      const [scanRes, findingsRes] = await Promise.all([
        api.getScan(id), api.listFindings({ scan_task_id: id, page_size: 200 })
      ]);
      setScan(scanRes);
      setFindings(findingsRes.items);
    } catch { /* ignore */ }
  };

  useEffect(() => {
    setLoading(true);
    loadData().finally(() => setLoading(false));
  }, [id]);

  // Auto-refresh for running scans
  const intervalRef = useRef<ReturnType<typeof setInterval>>();
  useEffect(() => {
    if (!id || !scan) return;
    if (scan.status !== "running" && scan.status !== "pending") {
      if (intervalRef.current) clearInterval(intervalRef.current);
      return;
    }
    intervalRef.current = setInterval(loadData, 5000);
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [id, scan?.status]);

  const getAnalysis = (finding: Finding, strategy: string): LLMAnalysisResult | undefined =>
    finding.llm_analyses?.find(a => a.strategy === strategy);

  const renderAnalysis = (finding: Finding, strategy: string) => {
    const a = getAnalysis(finding, strategy);
    if (!a) return <Tag>N/A</Tag>;
    return (
      <div style={{ textAlign: "center" }}>
        <Tag color={verdictColors[a.verdict]} style={{ marginBottom: 2 }}>
          {a.verdict === "true_positive" ? "TP" : a.verdict === "false_positive" ? "FP" : "?"}
        </Tag>
        <div style={{ fontSize: 11, color: "#888" }}>
          {a.confidence != null ? `${(a.confidence * 100).toFixed(0)}%` : "-"}
        </div>
      </div>
    );
  };

  const handleExport = () => {
    const data = findings.map(f => ({
      Scanner: f.scanner_name, Type: f.vulnerability_type, Severity: f.severity, URL: f.url,
      ZeroShot: f.llm_analyses?.find(a=>a.strategy==="zero_shot")?.verdict || "N/A",
      FewShot: f.llm_analyses?.find(a=>a.strategy==="few_shot")?.verdict || "N/A",
      CoT: f.llm_analyses?.find(a=>a.strategy==="chain_of_thought")?.verdict || "N/A",
    }));
    exportToCSV(data, `findings_${id?.slice(0,8)}`);
    message.success("Findings exported to CSV");
  };

  if (loading) return <Spin size="large" style={{ display: "block", marginTop: 120 }} />;
  if (!scan) return <p>Scan not found</p>;

  const findingsColumns = [
    { title: "Scanner", dataIndex: "scanner_name", key: "scanner", width: 80 },
    { title: "Type", dataIndex: "vulnerability_type", key: "type", width: 120 },
    { title: "Severity", dataIndex: "severity", key: "severity", width: 80,
      render: (s: string) => <Tag color={severityColors[s]}>{s}</Tag> },
    { title: "URL", dataIndex: "url", key: "url", ellipsis: true },
    { title: "Zero-shot", key: "z", width: 80, render: (_: unknown, r: Finding) => renderAnalysis(r, "zero_shot") },
    { title: "Few-shot", key: "f", width: 80, render: (_: unknown, r: Finding) => renderAnalysis(r, "few_shot") },
    { title: "CoT", key: "c", width: 80, render: (_: unknown, r: Finding) => renderAnalysis(r, "chain_of_thought") },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate("/scans")}>Back</Button>
        <Button icon={<DownloadOutlined />} onClick={handleExport} disabled={!findings.length}>
          Export CSV
        </Button>
        {(scan.status === "running" || scan.status === "pending") && (
          <Tag color="processing" icon={<Spin size="small" />}>Auto-refreshing every 5s</Tag>
        )}
      </Space>
      <Card>
        <Title level={4}>{scan.name}</Title>
        <Descriptions bordered column={{ xs: 1, sm: 2 }}>
          <Descriptions.Item label="Target URL">{scan.target_url}</Descriptions.Item>
          <Descriptions.Item label="Target Name">{scan.target_name || "-"}</Descriptions.Item>
          <Descriptions.Item label="Status"><Tag color={statusColors[scan.status]}>{scan.status}</Tag></Descriptions.Item>
          <Descriptions.Item label="Scanners">{scan.scanners.join(", ")}</Descriptions.Item>
          <Descriptions.Item label="Created">{new Date(scan.created_at).toLocaleString()}</Descriptions.Item>
          <Descriptions.Item label="Completed">{scan.completed_at ? new Date(scan.completed_at).toLocaleString() : "-"}</Descriptions.Item>
          <Descriptions.Item label="Findings" span={2}>{findings.length}</Descriptions.Item>
        </Descriptions>
      </Card>
      <Divider />
      <Title level={4}>Findings &amp; LLM Analysis
        <Text type="secondary" style={{ fontSize: 14, fontWeight: 400, marginLeft: 8 }}>
          ({findings.length} findings)
        </Text>
      </Title>
      <Paragraph type="secondary">
        Each finding analyzed by three prompting strategies. Colors: green=TP, red=FP, orange=uncertain.
        Click row to expand reasoning.
      </Paragraph>
      <Table dataSource={findings} columns={findingsColumns} rowKey="id"
        expandable={{
          expandedRowRender: (record) => {
            const strategies = ["zero_shot", "few_shot", "chain_of_thought"];
            return (
              <div style={{ maxWidth: 900 }}>
                <Text strong>Evidence:</Text>
                <Paragraph code copyable style={{ whiteSpace: "pre-wrap", fontSize: 12, maxHeight: 100, overflow: "auto" }}>
                  {record.raw_evidence || "No evidence captured"}
                </Paragraph>
                {strategies.map(s => {
                  const a = getAnalysis(record, s);
                  if (!a) return null;
                  return (
                    <div key={s} style={{ marginBottom: 8, padding: 8, background: "#fafafa", borderRadius: 4, border: "1px solid #f0f0f0" }}>
                      <Space>
                        <Text strong>{strategyLabels[s]}:</Text>
                        <Tag color={verdictColors[a.verdict]}>{a.verdict.replace("_", " ")}</Tag>
                        <Text type="secondary">conf: {a.confidence != null ? `${(a.confidence * 100).toFixed(0)}%` : "-"}</Text>
                        <Text type="secondary">tokens: {a.prompt_tokens || 0}+{a.completion_tokens || 0}</Text>
                        <Text type="secondary">{a.latency_ms ? `${(a.latency_ms / 1000).toFixed(1)}s` : "-"}</Text>
                      </Space>
                      <Paragraph style={{ marginTop: 4, marginBottom: 0, whiteSpace: "pre-wrap", fontSize: 12, color: "#555" }}>
                        {a.reasoning || "No reasoning"}
                      </Paragraph>
                    </div>
                  );
                })}
              </div>
            );
          },
        }}
        pagination={{ pageSize: 20, showTotal: (t) => `${t} findings` }} />
    </div>
  );
};
export default ScanDetail;
""")

# Results.tsx with more charts
w(f"{root}/pages/Results.tsx", """import React, { useEffect, useState } from "react";
import { Card, Table, Tag, Typography, Spin, Row, Col, Statistic, Alert } from "antd";
import { ExperimentOutlined, CheckCircleOutlined, CloseCircleOutlined, WarningOutlined } from "@ant-design/icons";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { api } from "../api/client";
import type { ExperimentResults } from "../types";

const { Title, Paragraph } = Typography;
const COLORS = ["#1677ff", "#52c41a", "#faad14", "#722ed1"];

const Results: React.FC = () => {
  const [results, setResults] = useState<ExperimentResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getExperimentResults()
      .then(setResults)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spin size="large" style={{ display: "block", marginTop: 120 }} />;
  if (error) return (
    <div>
      <Title level={3}>Experiment Results</Title>
      <Alert type="warning" message="No Results Available"
        description="Run scripts/experiment/runner.py first, then start the backend." showIcon />
    </div>
  );
  if (!results) return null;

  const strategies = ["zero_shot", "few_shot", "chain_of_thought"];
  const sname = (s: string) => s === "zero_shot" ? "Zero-shot" : s === "few_shot" ? "Few-shot" : "CoT";

  const metricsData = strategies.map(s => ({
    key: s, strategy: sname(s),
    tp: results.results[s]?.confusion_matrix?.tp || 0,
    fp: results.results[s]?.confusion_matrix?.fp || 0,
    fn: results.results[s]?.confusion_matrix?.fn || 0,
    tn: results.results[s]?.confusion_matrix?.tn || 0,
    precision: ((results.results[s]?.metrics?.Precision || 0) * 100).toFixed(1),
    recall: ((results.results[s]?.metrics?.Recall || 0) * 100).toFixed(1),
    f1: ((results.results[s]?.metrics?.["F1"] || 0) * 100).toFixed(1),
    accuracy: ((results.results[s]?.metrics?.Accuracy || 0) * 100).toFixed(1),
    fpr: ((results.results[s]?.metrics?.FPR || 0) * 100).toFixed(1),
    spec: ((results.results[s]?.metrics?.Specificity || 0) * 100).toFixed(1),
    npv: ((results.results[s]?.metrics?.NPV || 0) * 100).toFixed(1),
    latency: results.results[s]?.avg_latency?.toFixed(2) || "-",
    tokens: results.results[s]?.avg_tokens?.toFixed(0) || "-",
  }));

  const mainChartData = metricsData.map(d => ({
    name: d.strategy, Precision: parseFloat(d.precision),
    Recall: parseFloat(d.recall), F1: parseFloat(d.f1), Accuracy: parseFloat(d.accuracy),
  }));

  const costChartData = strategies.map(s => ({
    name: sname(s), "Latency (s)": results.results[s]?.avg_latency || 0,
    "Total Tokens": results.results[s]?.avg_tokens || 0,
  }));

  const fc = (v: number) => v >= 90 ? "green" : v >= 70 ? "orange" : "red";
  const vulnDistData = results.vulnerability_types.map((t, i) => ({ name: t, value: 6, color: COLORS[i % 4] }));

  const metricsCols = [
    { title: "Strategy", dataIndex: "strategy", key: "s", fixed: "left" as const },
    { title: "TP", dataIndex: "tp", key: "tp" }, { title: "FP", dataIndex: "fp", key: "fp" },
    { title: "FN", dataIndex: "fn", key: "fn" }, { title: "TN", dataIndex: "tn", key: "tn" },
    { title: "Precision", dataIndex: "precision", key: "p", render: (v: string) => <Tag color={fc(parseFloat(v))}>{v}%</Tag> },
    { title: "Recall", dataIndex: "recall", key: "r", render: (v: string) => <Tag color={fc(parseFloat(v))}>{v}%</Tag> },
    { title: "F1", dataIndex: "f1", key: "f1", render: (v: string) => <Tag color={fc(parseFloat(v))}>{v}%</Tag> },
    { title: "Acc", dataIndex: "accuracy", key: "a", render: (v: string) => <Tag color={fc(parseFloat(v))}>{v}%</Tag> },
    { title: "FPR", dataIndex: "fpr", key: "fpr", render: (v: string) => <Tag color={parseFloat(v) < 10 ? "green" : "orange"}>{v}%</Tag> },
    { title: "Lat(s)", dataIndex: "latency", key: "l" },
    { title: "Tokens", dataIndex: "tokens", key: "t" },
  ];

  return (
    <div>
      <Title level={3}>Experiment Results</Title>
      <Paragraph>Evaluation of LLM prompting strategies for vulnerability false-positive filtering.</Paragraph>

      <Row gutter={[16, 16]}>
        <Col xs={8}><Card><Statistic title="Dataset" value={results.dataset_size} prefix={<ExperimentOutlined />} /></Card></Col>
        <Col xs={8}><Card><Statistic title="True Positives" value={results.ground_truth_distribution.true_positive} prefix={<CheckCircleOutlined />} valueStyle={{ color: "#3f8600" }} /></Card></Col>
        <Col xs={8}><Card><Statistic title="False Positives" value={results.ground_truth_distribution.false_positive} prefix={<CloseCircleOutlined />} valueStyle={{ color: "#cf1322" }} /></Card></Col>
      </Row>

      <Card title="Performance Metrics" style={{ marginTop: 24 }}>
        <Table dataSource={metricsData} columns={metricsCols} pagination={false} size="small" scroll={{ x: 900 }} />
      </Card>

      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="Strategy Performance Comparison">
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={mainChartData} margin={{ top: 20, right: 20, left: 40, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis domain={[0, 100]} unit="%" />
                <Tooltip formatter={(v: number) => `${v.toFixed(1)}%`} />
                <Legend />
                <Bar dataKey="Precision" fill="#1677ff" radius={[4,4,0,0]} />
                <Bar dataKey="Recall" fill="#52c41a" radius={[4,4,0,0]} />
                <Bar dataKey="F1" fill="#faad14" radius={[4,4,0,0]} />
                <Bar dataKey="Accuracy" fill="#722ed1" radius={[4,4,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Cost Comparison (Latency & Tokens)">
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={costChartData} margin={{ top: 20, right: 20, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Legend />
                <Bar yAxisId="left" dataKey="Latency (s)" fill="#1677ff" radius={[4,4,0,0]} />
                <Bar yAxisId="right" dataKey="Total Tokens" fill="#52c41a" radius={[4,4,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        {metricsData.map(d => (
          <Col xs={24} md={8} key={d.key}>
            <Card size="small" title={d.strategy} style={{ textAlign: "center" }}>
              <table style={{ margin: "0 auto", borderCollapse: "collapse" }}>
                <tbody>
                  <tr><td style={{ padding: "4px 12px", border: "1px solid #d9d9d9", background: "#f6ffed" }}>
                    <b>TP</b><br /><span style={{ fontSize: 20 }}>{d.tp}</span>
                  </td><td style={{ padding: "4px 12px", border: "1px solid #d9d9d9", background: "#fff2f0" }}>
                    <b>FN</b><br /><span style={{ fontSize: 20 }}>{d.fn}</span>
                  </td></tr>
                  <tr><td style={{ padding: "4px 12px", border: "1px solid #d9d9d9", background: "#fff7e6" }}>
                    <b>FP</b><br /><span style={{ fontSize: 20 }}>{d.fp}</span>
                  </td><td style={{ padding: "4px 12px", border: "1px solid #d9d9d9", background: "#f0f5ff" }}>
                    <b>TN</b><br /><span style={{ fontSize: 20 }}>{d.tn}</span>
                  </td></tr>
                </tbody>
              </table>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
};
export default Results;
""")

print("Batch 2 done")