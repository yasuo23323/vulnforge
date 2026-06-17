import React, { useEffect, useState, useCallback } from "react";
import { Card, Typography, Descriptions, Tag, Spin, Button, Alert, Space, Divider } from "antd";
import { CheckCircleOutlined, CloseCircleOutlined, ApiOutlined } from "@ant-design/icons";
import { api } from "../api/client";
import type { AppSettings } from "../types";

const { Title, Text } = Typography;

interface TestResult {
  success: boolean;
  message?: string;
  reply?: string;
}

const Settings: React.FC = () => {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<TestResult | null>(null);

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
              description={testResult.message || testResult.reply || "No details"}
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

export default Settings;
