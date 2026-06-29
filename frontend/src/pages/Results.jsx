import React, { useEffect, useState } from "react";
import { Table, Tag, Button, Modal, Typography, Select, Space, message, Descriptions, Card } from "antd";
import { EyeOutlined, ThunderboltOutlined } from "@ant-design/icons";
import { getFindings, analyzeFinding } from "../api";

const { Title, Text } = Typography;

const severityColors = { critical: "red", high: "orange", medium: "gold", low: "blue", info: "default" };

function Results() {
  const [findings, setFindings] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await getFindings({ page, page_size: 50 });
      setFindings(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (e) {
      message.error("Failed to load findings");
    }
    setLoading(false);
  };

  useEffect(() => { load(); }, [page]);

  const handleAnalyze = async (finding) => {
    setAnalyzing(true);
    try {
      const res = await analyzeFinding(finding.id, "chain_of_thought");
      message.success("Analysis complete!");
      load();
    } catch (e) {
      message.error("Analysis failed: " + (e.response?.data?.detail || e.message));
    }
    setAnalyzing(false);
  };

  const columns = [
    { title: "Scanner", dataIndex: "scanner_name", key: "scanner_name", width: 100 },
    { title: "Type", dataIndex: "vulnerability_type", key: "vulnerability_type", ellipsis: true },
    { title: "Severity", dataIndex: "severity", key: "severity", render: (s) => <Tag color={severityColors[s]}>{s}</Tag> },
    { title: "URL", dataIndex: "url", key: "url", ellipsis: true },
    { title: "LLM", key: "llm", render: (_, r) => {
      const analyses = r.llm_analyses || [];
      if (analyses.length === 0) return <Tag>Not analyzed</Tag>;
      const last = analyses[analyses.length - 1];
      const color = last.verdict === "true_positive" ? "red" : last.verdict === "false_positive" ? "green" : "orange";
      return <Tag color={color}>{last.verdict} ({Math.round(last.confidence * 100)}%)</Tag>;
    }},
    { title: "Actions", key: "actions", width: 160, render: (_, r) => (
      <Space>
        <Button size="small" icon={<EyeOutlined />} onClick={() => { setSelected(r); setDetailOpen(true); }}>View</Button>
        <Button size="small" icon={<ThunderboltOutlined />} loading={analyzing} onClick={() => handleAnalyze(r)}>Analyze</Button>
      </Space>
    )},
  ];

  return (
    <div>
      <Title level={3}>Findings ({total})</Title>
      <Table dataSource={findings} columns={columns} rowKey="id" loading={loading}
        pagination={{ current: page, total, pageSize: 50, onChange: setPage }}
        size="small" />

      <Modal title="Finding Detail" open={detailOpen} onCancel={() => setDetailOpen(false)} footer={null} width={800}>
        {selected && (
          <div>
            <Descriptions column={2} size="small" bordered>
              <Descriptions.Item label="Scanner">{selected.scanner_name}</Descriptions.Item>
              <Descriptions.Item label="Severity"><Tag color={severityColors[selected.severity]}>{selected.severity}</Tag></Descriptions.Item>
              <Descriptions.Item label="Type" span={2}>{selected.vulnerability_type}</Descriptions.Item>
              <Descriptions.Item label="URL" span={2}>{selected.url}</Descriptions.Item>
              <Descriptions.Item label="Description" span={2}>{selected.description || "N/A"}</Descriptions.Item>
            </Descriptions>
            {selected.raw_evidence && (
              <div style={{ marginTop: 16 }}>
                <Text strong>Raw Evidence:</Text>
                <pre style={{ background: "#f5f5f5", padding: 8, borderRadius: 4, fontSize: 12, maxHeight: 200, overflow: "auto" }}>{selected.raw_evidence}</pre>
              </div>
            )}
            {(selected.llm_analyses || []).length > 0 && (
              <div style={{ marginTop: 16 }}>
                <Title level={5}>LLM Analysis</Title>
                {selected.llm_analyses.map((a) => (
                  <Card key={a.id} size="small" style={{ marginBottom: 8 }}>
                    <p><Tag color={a.verdict === "true_positive" ? "red" : a.verdict === "false_positive" ? "green" : "orange"}>{a.verdict}</Tag> Confidence: {Math.round(a.confidence * 100)}% | {a.provider}/{a.model_name} ({a.strategy})</p>
                    <p style={{ fontSize: 12, whiteSpace: "pre-wrap" }}>{a.reasoning}</p>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}

export default Results;