import os

def w(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  {os.path.basename(path)}")

root = "D:\\大论文\\frontend\\src"

# utils/export.ts
w(f"{root}/utils/export.ts", """export function exportToCSV(data: Record<string, unknown>[], filename: string): void {
  if (!data.length) return;
  const headers = Object.keys(data[0]);
  const csv = [
    headers.join(","),
    ...data.map(r => headers.map(h => {
      const v = r[h];
      if (v == null) return "";
      const s = String(v);
      return /[,"\\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
    }).join(","))
  ].join("\\n");
  const blob = new Blob(["\\ufeff" + csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${filename}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}
""")

# Settings.tsx
w(f"{root}/pages/Settings.tsx", """import React, { useEffect, useState, useCallback } from "react";
import { Card, Typography, Descriptions, Tag, Spin, Button, Alert, Space } from "antd";
import { CheckCircleOutlined, CloseCircleOutlined, ApiOutlined } from "@ant-design/icons";
import { api } from "../api/client";
import type { AppSettings } from "../types";

const { Title, Text } = Typography;

const Settings: React.FC = () => {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  useEffect(() => {
    api.getSettings().then(setSettings).catch(() => setSettings(null)).finally(() => setLoading(false));
  }, []);

  const handleTest = useCallback(async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await api.testConnection();
      setTestResult(res);
    } catch (e: unknown) {
      setTestResult({ success: false, message: e instanceof Error ? e.message : "Connection failed" });
    }
    setTesting(false);
  }, []);

  if (loading) return <Spin size="large" style={{ display: "block", marginTop: 120 }} />;

  return (
    <div>
      <Title level={3}>Settings</Title>
      <Card title="LLM Configuration" style={{ maxWidth: 700 }}>
        <Descriptions bordered column={1}>
          <Descriptions.Item label="Provider">
            <Tag color="blue">{settings?.llm_provider || "Not configured"}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Model">{settings?.llm_model || "Not configured"}</Descriptions.Item>
          <Descriptions.Item label="API Base URL">
            <Text code>{settings?.llm_provider === "openai" ? "api.openai.com" : "api.anthropic.com"}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="OpenAI/DeepSeek Key">
            <Tag color={settings?.openai_key_set ? "green" : "red"}>
              {settings?.openai_key_set ? "Configured" : "Not set"}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Anthropic Key">
            <Tag color={settings?.anthropic_key_set ? "green" : "red"}>
              {settings?.anthropic_key_set ? "Configured" : "Not set"}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Database">{settings?.database_type || "N/A"}</Descriptions.Item>
        </Descriptions>

        <Divider style={{ margin: "16px 0" }} />

        <Title level={5}>Test LLM Connection</Title>
        <Space direction="vertical" style={{ width: "100%" }}>
          <Button type="primary" icon={<ApiOutlined />} loading={testing} onClick={handleTest}
            disabled={!settings?.openai_key_set && !settings?.anthropic_key_set}>
            {testing ? "Testing..." : "Test Connection"}
          </Button>
          {testResult && (
            <Alert
              type={testResult.success ? "success" : "error"}
              message={testResult.success ? "Connection Successful" : "Connection Failed"}
              description={testResult.message}
              showIcon
            />
          )}
        </Space>

        <div style={{ marginTop: 16, padding: 12, background: "#fffbe6", borderRadius: 6 }}>
          <Text type="secondary">
            To update LLM settings, edit the <Text code>backend/.env</Text> file directly and restart the server.
          </Text>
        </div>
      </Card>
    </div>
  );
};

const Divider: React.FC<{ style?: React.CSSProperties }> = ({ style }) => (
  <div style={{ borderTop: "1px solid #f0f0f0", ...style }} />
);

export default Settings;
""")

# ScanList.tsx
w(f"{root}/pages/ScanList.tsx", """import React, { useEffect, useState } from "react";
import { Table, Button, Tag, Typography, Modal, Form, Input, Select, Space, message, Spin, Tooltip } from "antd";
import { PlusOutlined, DeleteOutlined, EyeOutlined, DownloadOutlined, ReloadOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { ScanTask, ScanCreateRequest } from "../types";
import { exportToCSV } from "../utils/export";

const { Title } = Typography;

const statusColors: Record<string, string> = { pending: "default", running: "processing", completed: "success", failed: "error", cancelled: "warning" };

const statusOptions = [
  { value: "", label: "All" },
  { value: "pending", label: "Pending" },
  { value: "running", label: "Running" },
  { value: "completed", label: "Completed" },
  { value: "failed", label: "Failed" },
  { value: "cancelled", label: "Cancelled" },
];

const scannerOptions = [
  { value: "", label: "All" },
  { value: "nuclei", label: "Nuclei" },
  { value: "sqlmap", label: "Sqlmap" },
  { value: "dalfox", label: "Dalfox" },
  { value: "ffuf", label: "Ffuf" },
];

const ScanList: React.FC = () => {
  const [scans, setScans] = useState<ScanTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [scannerFilter, setScannerFilter] = useState<string>("");
  const [form] = Form.useForm();
  const navigate = useNavigate();

  const fetchScans = async () => {
    setLoading(true);
    try {
      const params: { page_size?: number; status?: string } = { page_size: 50 };
      if (statusFilter) params.status = statusFilter;
      const res = await api.listScans(params);
      setScans(res.items);
    } catch { message.error("Failed to load scans"); }
    setLoading(false);
  };

  useEffect(() => { fetchScans(); }, [statusFilter]);

  const handleCreate = async (values: ScanCreateRequest) => {
    setCreating(true);
    try {
      await api.createScan({ ...values, scanners: values.scanners || ["nuclei"] });
      message.success("Scan created");
      setModalOpen(false);
      form.resetFields();
      fetchScans();
    } catch { message.error("Failed to create scan"); }
    setCreating(false);
  };

  const handleDelete = async (id: string) => {
    try { await api.deleteScan(id); message.success("Scan deleted"); fetchScans(); }
    catch { message.error("Failed to delete scan"); }
  };

  const handleExport = () => {
    const data = scans.map(s => ({
      Name: s.name, Target: s.target_url, Status: s.status,
      Scanners: s.scanners.join(", "), Findings: s.findings_count ?? 0,
      Created: new Date(s.created_at).toLocaleDateString(),
    }));
    exportToCSV(data, "vulnforge_scans");
    message.success("Exported to CSV");
  };

  const filteredScans = scannerFilter
    ? scans.filter(s => s.scanners.includes(scannerFilter))
    : scans;

  const columns = [
    { title: "Name", dataIndex: "name", key: "name",
      render: (name: string, r: ScanTask) => <a onClick={() => navigate(`/scans/${r.id}`)}>{name}</a> },
    { title: "Target", dataIndex: "target_url", key: "target", ellipsis: true },
    { title: "Scanners", dataIndex: "scanners", key: "scanners",
      render: (s: string[]) => s.map(sc => <Tag key={sc}>{sc}</Tag>) },
    { title: "Status", dataIndex: "status", key: "status",
      render: (s: string) => <Tag color={statusColors[s]}>{s}</Tag> },
    { title: "Findings", dataIndex: "findings_count", key: "findings", width: 80,
      render: (n: number) => (n > 0 ? <Tag color="red">{n}</Tag> : "-") },
    { title: "Created", dataIndex: "created_at", key: "created_at", width: 100,
      render: (d: string) => new Date(d).toLocaleDateString() },
    { title: "", key: "actions", width: 100,
      render: (_: unknown, r: ScanTask) => (
        <Space>
          <Tooltip title="View"><Button icon={<EyeOutlined />} size="small" onClick={() => navigate(`/scans/${r.id}`)} /></Tooltip>
          <Tooltip title="Delete"><Button icon={<DeleteOutlined />} size="small" danger onClick={() => handleDelete(r.id)} /></Tooltip>
        </Space>
      ) },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16, flexWrap: "wrap", gap: 8 }}>
        <Space>
          <Title level={3} style={{ margin: 0 }}>Scan Tasks</Title>
          <Select value={statusFilter} onChange={setStatusFilter} style={{ width: 120 }}
            options={statusOptions} />
          <Select value={scannerFilter} onChange={setScannerFilter} style={{ width: 120 }}
            options={scannerOptions} />
          <Tooltip title="Refresh"><Button icon={<ReloadOutlined />} onClick={fetchScans} /></Tooltip>
        </Space>
        <Space>
          <Button icon={<DownloadOutlined />} onClick={handleExport} disabled={!scans.length}>
            Export CSV
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
            New Scan
          </Button>
        </Space>
      </div>

      <Spin spinning={loading}>
        <Table dataSource={filteredScans} columns={columns} rowKey="id"
          pagination={{ pageSize: 20, showTotal: (t) => `${t} total` }} />
      </Spin>

      <Modal title="Create New Scan" open={modalOpen} onCancel={() => setModalOpen(false)} footer={null}>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="Scan Name" rules={[{ required: true, message: "Enter a scan name" }]}>
            <Input placeholder="e.g. Juice Shop Scan" />
          </Form.Item>
          <Form.Item name="target_url" label="Target URL"
            rules={[{ required: true, type: "url", message: "Enter a valid URL" }]}>
            <Input placeholder="http://localhost:3001" />
          </Form.Item>
          <Form.Item name="target_name" label="Target Name">
            <Input placeholder="e.g. OWASP Juice Shop" />
          </Form.Item>
          <Form.Item name="scanners" label="Scanners" initialValue={["nuclei"]}
            rules={[{ required: true, message: "Select at least one scanner" }]}>
            <Select mode="multiple" placeholder="Select scanners">
              <Select.Option value="nuclei">Nuclei (CVE/Config)</Select.Option>
              <Select.Option value="sqlmap">SQLMap (SQL Injection)</Select.Option>
              <Select.Option value="dalfox">Dalfox (XSS)</Select.Option>
              <Select.Option value="ffuf">Ffuf (Directory)</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={creating} block>
              Create Scan
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};
export default ScanList;
""")

print("Batch 1 done")