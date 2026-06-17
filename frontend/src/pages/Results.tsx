import React, { useEffect, useState } from "react";
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
