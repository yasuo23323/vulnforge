import React, { useEffect, useState } from "react";
import { Row, Col, Card, Statistic, Table, Tag, Typography } from "antd";
import {
  ScanOutlined,
  BugOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from "@ant-design/icons";
import { getScans, getFindings } from "../api";

const { Title } = Typography;

const severityColors = {
  critical: "red",
  high: "orange",
  medium: "gold",
  low: "blue",
  info: "default",
};

function Dashboard() {
  const [stats, setStats] = useState({ scans: 0, findings: 0, completed: 0, failed: 0 });
  const [recentScans, setRecentScans] = useState([]);

  useEffect(() => {
    const load = async () => {
      try {
        const [scansRes, findingsRes] = await Promise.all([
          getScans(1, 10),
          getFindings({ page: 1, page_size: 100 }),
        ]);
        const scans = scansRes.data.items || [];
        const findings = findingsRes.data.items || [];
        setStats({
          scans: scansRes.data.total || 0,
          findings: findingsRes.data.total || 0,
          completed: scans.filter((s) => s.status === "completed").length,
          failed: scans.filter((s) => s.status === "failed").length,
        });
        setRecentScans(scans.slice(0, 5));
      } catch (e) {
        console.error("Dashboard load error:", e);
      }
    };
    load();
    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, []);

  const columns = [
    { title: "Target", dataIndex: "target_url", key: "target_url", ellipsis: true },
    { title: "Status", dataIndex: "status", key: "status", render: (s) => (
      <Tag color={s === "completed" ? "green" : s === "failed" ? "red" : "blue"}>{s}</Tag>
    )},
    { title: "Findings", dataIndex: "findings_count", key: "findings_count" },
    { title: "Created", dataIndex: "created_at", key: "created_at", render: (d) => d ? new Date(d).toLocaleString() : "" },
  ];

  return (
    <div>
      <Title level={3}>Dashboard</Title>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card><Statistic title="Total Scans" value={stats.scans} prefix={<ScanOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="Total Findings" value={stats.findings} prefix={<BugOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="Completed" value={stats.completed} prefix={<CheckCircleOutlined />} valueStyle={{ color: "#3f8600" }} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="Failed" value={stats.failed} prefix={<CloseCircleOutlined />} valueStyle={{ color: "#cf1322" }} /></Card>
        </Col>
      </Row>
      <Card title="Recent Scans">
        <Table dataSource={recentScans} columns={columns} rowKey="id" pagination={false} size="small" />
      </Card>
    </div>
  );
}

export default Dashboard;