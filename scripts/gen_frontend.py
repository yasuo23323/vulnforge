import os, json

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  Written: {path}")

root = "D:\\大论文\\frontend\\src"

f = open("D:\\大论文\\scripts\\experiment\\results.json")
EXPERIMENT_RESULTS = json.load(f)
RESULTS_JSON = json.dumps(EXPERIMENT_RESULTS, indent=2)

# === 1. types/index.ts ===
write_file(f"{root}/types/index.ts", """export interface ScanTask {
  id: string; name: string; target_url: string; target_name: string | null;
  scanners: string[]; status: string; parameters: Record<string, unknown> | null;
  created_at: string; updated_at: string; started_at: string | null;
  completed_at: string | null; error_message: string | null; findings_count: number;
}

export interface ScanCreateRequest {
  name: string; target_url: string; target_name?: string;
  scanners?: string[]; parameters?: Record<string, unknown>;
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
""")

# === 2. App.tsx ===
write_file(f"{root}/App.tsx", """import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import AppLayout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import ScanList from "./pages/ScanList";
import ScanDetail from "./pages/ScanDetail";
import Results from "./pages/Results";
import Settings from "./pages/Settings";

const App: React.FC = () => (
  <AppLayout>
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/scans" element={<ScanList />} />
      <Route path="/scans/:id" element={<ScanDetail />} />
      <Route path="/results" element={<Results />} />
      <Route path="/settings" element={<Settings />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  </AppLayout>
);
export default App;
""")

# === 3. components/Layout.tsx ===
write_file(f"{root}/components/Layout.tsx", """import React from "react";
import { Layout, Menu } from "antd";
import { useNavigate, useLocation } from "react-router-dom";
import {
  DashboardOutlined, SecurityScanOutlined, ExperimentOutlined,
  SettingOutlined, BugOutlined,
} from "@ant-design/icons";

const { Header, Sider, Content } = Layout;

const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { key: "/", icon: <DashboardOutlined />, label: "Dashboard" },
    { key: "/scans", icon: <SecurityScanOutlined />, label: "Scan Tasks" },
    { key: "/results", icon: <ExperimentOutlined />, label: "Experiment" },
    { key: "/settings", icon: <SettingOutlined />, label: "Settings" },
  ];

  const findSelected = () => {
    for (const item of menuItems) {
      if (location.pathname.startsWith(item.key) && item.key !== "/") return item.key;
      if (item.key === "/" && location.pathname === "/") return "/";
    }
    return "/";
  };

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider breakpoint="lg" collapsedWidth={0} theme="dark">
        <div style={{ height: 64, display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontWeight: 700, fontSize: 18, letterSpacing: 1 }}>
          <BugOutlined style={{ marginRight: 8 }} />VulnForge
        </div>
        <Menu theme="dark" mode="inline" selectedKeys={[findSelected()]}
          items={menuItems} onClick={({ key }) => navigate(key)} />
      </Sider>
      <Layout>
        <Header style={{ padding: "0 24px", background: "#fff", borderBottom: "1px solid #f0f0f0", display: "flex", alignItems: "center", fontSize: 16, fontWeight: 500 }}>
          AI-Enhanced Web Vulnerability Scanner
        </Header>
        <Content style={{ margin: 24 }}>{children}</Content>
      </Layout>
    </Layout>
  );
};
export default AppLayout;
""")

# === 4. Settings.tsx ===
write_file(f"{root}/pages/Settings.tsx", """import React, { useEffect, useState } from "react";
import { Card, Form, Input, Select, Typography, message, Spin, Descriptions, Tag } from "antd";
import { api } from "../api/client";
import type { AppSettings } from "../types";

const { Title, Text } = Typography;

const Settings: React.FC = () => {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getSettings().then(setSettings).catch(() => setSettings(null)).finally(() => setLoading(false));
  }, []);

  if (loading) return <Spin size="large" style={{ display: "block", marginTop: 120 }} />;

  return (
    <div>
      <Title level={3}>Settings</Title>
      <Card title="LLM Configuration" style={{ maxWidth: 600 }}>
        <Descriptions bordered column={1}>
          <Descriptions.Item label="Provider">
            <Tag color="blue">{settings?.llm_provider || "Not configured"}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Model">{settings?.llm_model || "Not configured"}</Descriptions.Item>
          <Descriptions.Item label="OpenAI API Key">
            <Tag color={settings?.openai_key_set ? "green" : "red"}>
              {settings?.openai_key_set ? "Configured" : "Not set"}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Anthropic API Key">
            <Tag color={settings?.anthropic_key_set ? "green" : "red"}>
              {settings?.anthropic_key_set ? "Configured" : "Not set"}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Database">{settings?.database_type || "N/A"}</Descriptions.Item>
        </Descriptions>
        <div style={{ marginTop: 16, padding: 12, background: "#fffbe6", borderRadius: 6 }}>
          <Text type="secondary">
            To update LLM settings, edit the <code>backend/.env</code> file directly and restart the server.
          </Text>
        </div>
      </Card>
    </div>
  );
};
export default Settings;
""")

print("Generator script done")