import React, { useEffect, useState, useRef } from "react";
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
        api.getScan(id), api.listFindings({ scan_task_id: id, page_size: 100 })
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

