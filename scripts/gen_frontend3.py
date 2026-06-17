import os

def w(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  {os.path.basename(path)}")

root = "D:\\大论文\\frontend\\src"

# ScanDetail with LLM strategy comparison
w(f"{root}/pages/ScanDetail.tsx", """import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, Descriptions, Tag, Typography, Table, Spin, Button, Space, Divider, Progress } from "antd";
import { ArrowLeftOutlined } from "@ant-design/icons";
import { api } from "../api/client";
import type { ScanTask, Finding, LLMAnalysisResult } from "../types";

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

  useEffect(() => {
    if (!id) return;
    Promise.all([api.getScan(id), api.listFindings({ scan_task_id: id, page_size: 200 })])
      .then(([scanRes, findingsRes]) => { setScan(scanRes); setFindings(findingsRes.items); setLoading(false); })
      .catch(() => setLoading(false));
  }, [id]);

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
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate("/scans")}>Back to Scans</Button>
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
      <Title level={4}>Findings & LLM Analysis</Title>
      <Paragraph type="secondary">
        Each finding is analyzed by three prompting strategies. Columns show the verdict (TP=true positive, FP=false positive, ?=uncertain) with confidence percentage.
      </Paragraph>
      <Table dataSource={findings} columns={findingsColumns} rowKey="id"
        expandable={{
          expandedRowRender: (record) => {
            const strategies = ["zero_shot", "few_shot", "chain_of_thought"];
            return (
              <div style={{ maxWidth: 900 }}>
                <Text strong>Evidence:</Text>
                <Paragraph code copyable style={{ whiteSpace: "pre-wrap", fontSize: 12 }}>
                  {record.raw_evidence || "No evidence captured"}
                </Paragraph>
                {strategies.map(s => {
                  const a = getAnalysis(record, s);
                  if (!a) return null;
                  return (
                    <div key={s} style={{ marginBottom: 12, padding: 8, background: "#fafafa", borderRadius: 4 }}>
                      <Space>
                        <Text strong>{strategyLabels[s]}:</Text>
                        <Tag color={verdictColors[a.verdict]}>{a.verdict.replace("_", " ")}</Tag>
                        <Text type="secondary">confidence: {a.confidence != null ? `${(a.confidence * 100).toFixed(0)}%` : "-"}</Text>
                        <Text type="secondary">tokens: {a.prompt_tokens || 0}+{a.completion_tokens || 0}</Text>
                        <Text type="secondary">latency: {a.latency_ms ? `${(a.latency_ms / 1000).toFixed(1)}s` : "-"}</Text>
                      </Space>
                      <Paragraph style={{ marginTop: 4, marginBottom: 0, whiteSpace: "pre-wrap", fontSize: 12 }}>
                        {a.reasoning || "No reasoning"}
                      </Paragraph>
                    </div>
                  );
                })}
              </div>
            );
          },
        }}
        pagination={{ pageSize: 20 }} />
    </div>
  );
};
export default ScanDetail;
""")

# Results page
w(f"{root}/pages/Results.tsx", """import React, { useEffect, useState } from "react";
import { Card, Table, Tag, Typography, Spin, Row, Col, Statistic, Descriptions } from "antd";
import { ExperimentOutlined, CheckCircleOutlined, CloseCircleOutlined, WarningOutlined } from "@ant-design/icons";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { api } from "../api/client";
import type { ExperimentResults } from "../types";

const { Title, Paragraph, Text } = Typography;

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

  if (error) {
    return (
      <div>
        <Title level={3}>Experiment Results</Title>
        <Card>
          <div style={{ textAlign: "center", padding: 40 }}>
            <WarningOutlined style={{ fontSize: 48, color: "#faad14" }} />
            <Title level={4}>No Results Available</Title>
            <Paragraph>
              Run the experiment framework from <code>scripts/experiment/runner.py</code> first,
              then start the backend server to see results here.
            </Paragraph>
            <pre style={{ background: "#f5f5f5", padding: 12, borderRadius: 4, textAlign: "left", fontSize: 12 }}>
              {error}
            </pre>
          </div>
        </Card>
      </div>
    );
  }

  if (!results) return null;

  const strategies = ["zero_shot", "few_shot", "chain_of_thought"];

  const metricsTableData = strategies.map(s => ({
    key: s, strategy: s === "zero_shot" ? "Zero-shot" : s === "few_shot" ? "Few-shot" : "Chain-of-Thought",
    tp: results.results[s]?.confusion_matrix?.tp || 0,
    fp: results.results[s]?.confusion_matrix?.fp || 0,
    fn: results.results[s]?.confusion_matrix?.fn || 0,
    tn: results.results[s]?.confusion_matrix?.tn || 0,
    precision: (results.results[s]?.metrics?.Precision || 0) * 100,
    recall: (results.results[s]?.metrics?.Recall || 0) * 100,
    f1: (results.results[s]?.metrics?.["F1"] || 0) * 100,
    accuracy: (results.results[s]?.metrics?.Accuracy || 0) * 100,
    fpr: (results.results[s]?.metrics?.FPR || 0) * 100,
    specificity: (results.results[s]?.metrics?.Specificity || 0) * 100,
    npv: (results.results[s]?.metrics?.NPV || 0) * 100,
    latency: results.results[s]?.avg_latency?.toFixed(2) || "-",
    tokens: results.results[s]?.avg_tokens?.toFixed(0) || "-",
  }));

  const chartData = metricsTableData.map(d => ({
    name: d.strategy, Precision: d.precision, Recall: d.recall,
    F1: d.f1, Accuracy: d.accuracy,
  }));

  const getF1Color = (v: number) => v >= 90 ? "green" : v >= 70 ? "orange" : "red";

  return (
    <div>
      <Title level={3}>Experiment Results</Title>
      <Paragraph>Comprehensive evaluation of LLM prompting strategies for vulnerability verification.</Paragraph>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={8}><Card><Statistic title="Dataset Size" value={results.dataset_size} prefix={<ExperimentOutlined />} /></Card></Col>
        <Col xs={24} sm={8}><Card><Statistic title="True Positives" value={results.ground_truth_distribution.true_positive} prefix={<CheckCircleOutlined />} valueStyle={{ color: "#3f8600" }} /></Card></Col>
        <Col xs={24} sm={8}><Card><Statistic title="False Positives" value={results.ground_truth_distribution.false_positive} prefix={<CloseCircleOutlined />} valueStyle={{ color: "#cf1322" }} /></Card></Col>
      </Row>

      <Card title="Overall Performance Metrics" style={{ marginTop: 24 }}>
        <Table dataSource={metricsTableData} pagination={false} size="small"
          columns={[
            { title: "Strategy", dataIndex: "strategy", key: "strategy", fixed: "left" },
            { title: "TP", dataIndex: "tp", key: "tp" },
            { title: "FP", dataIndex: "fp", key: "fp" },
            { title: "FN", dataIndex: "fn", key: "fn" },
            { title: "TN", dataIndex: "tn", key: "tn" },
            { title: "Precision%", dataIndex: "precision", key: "precision", render: (v: number) => <Tag color={getF1Color(v)}>{v.toFixed(1)}</Tag> },
            { title: "Recall%", dataIndex: "recall", key: "recall", render: (v: number) => <Tag color={getF1Color(v)}>{v.toFixed(1)}</Tag> },
            { title: "F1%", dataIndex: "f1", key: "f1", render: (v: number) => <Tag color={getF1Color(v)}>{v.toFixed(1)}</Tag> },
            { title: "Accuracy%", dataIndex: "accuracy", key: "accuracy", render: (v: number) => <Tag color={getF1Color(v)}>{v.toFixed(1)}</Tag> },
            { title: "FPR%", dataIndex: "fpr", key: "fpr", render: (v: number) => <Tag color={v < 10 ? "green" : v < 20 ? "orange" : "red"}>{v.toFixed(1)}</Tag> },
            { title: "Avg Lat(s)", dataIndex: "latency", key: "latency" },
            { title: "Avg Tokens", dataIndex: "tokens", key: "tokens" },
          ]}
          scroll={{ x: 900 }} />
      </Card>

      <Card title="Strategy Performance Comparison" style={{ marginTop: 24 }}>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={chartData} margin={{ top: 20, right: 30, left: 40, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis domain={[0, 100]} unit="%" />
            <Tooltip formatter={(v: number) => `${v.toFixed(1)}%`} />
            <Legend />
            <Bar dataKey="Precision" fill="#1677ff" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Recall" fill="#52c41a" radius={[4, 4, 0, 0]} />
            <Bar dataKey="F1" fill="#faad14" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Accuracy" fill="#722ed1" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      <Card title="Confusion Matrices" style={{ marginTop: 24 }}>
        <Row gutter={[16, 16]}>
          {metricsTableData.map(d => (
            <Col xs={24} md={8} key={d.key}>
              <Card size="small" title={d.strategy} style={{ textAlign: "center" }}>
                <table style={{ margin: "0 auto", borderCollapse: "collapse" }}>
                  <tbody>
                    <tr>
                      <td style={{ padding: "4px 12px", border: "1px solid #d9d9d9", background: "#f6ffed" }}>
                        <Text strong>TP</Text><br /><Text style={{ fontSize: 20 }}>{d.tp}</Text>
                      </td>
                      <td style={{ padding: "4px 12px", border: "1px solid #d9d9d9", background: "#fff2f0" }}>
                        <Text strong>FN</Text><br /><Text style={{ fontSize: 20 }}>{d.fn}</Text>
                      </td>
                    </tr>
                    <tr>
                      <td style={{ padding: "4px 12px", border: "1px solid #d9d9d9", background: "#fff7e6" }}>
                        <Text strong>FP</Text><br /><Text style={{ fontSize: 20 }}>{d.fp}</Text>
                      </td>
                      <td style={{ padding: "4px 12px", border: "1px solid #d9d9d9", background: "#f0f5ff" }}>
                        <Text strong>TN</Text><br /><Text style={{ fontSize: 20 }}>{d.tn}</Text>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </Card>
            </Col>
          ))}
        </Row>
      </Card>
    </div>
  );
};
export default Results;
""")

print("Done - ScanDetail and Results pages")