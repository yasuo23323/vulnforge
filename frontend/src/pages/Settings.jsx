import React, { useEffect, useState } from "react";
import { Card, Descriptions, Tag, Button, Typography, message, Alert } from "antd";
import { CheckCircleOutlined, CloseCircleOutlined, ReloadOutlined } from "@ant-design/icons";
import { getSettings, testLLM } from "../api";

const { Title } = Typography;

function Settings() {
  const [settings, setSettings] = useState(null);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  useEffect(() => {
    getSettings().then((res) => setSettings(res.data)).catch(() => message.error("Failed to load settings"));
  }, []);

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await testLLM();
      setTestResult(res.data);
      if (res.data.status === "ok") message.success("LLM connection OK!");
      else message.error("LLM test failed: " + (res.data.detail || "unknown error"));
    } catch (e) {
      setTestResult({ status: "error", detail: e.response?.data?.detail || e.message });
      message.error("LLM test failed");
    }
    setTesting(false);
  };

  if (!settings) return <div>Loading...</div>;

  return (
    <div>
      <Title level={3}>Settings</Title>
      <Card title="Configuration" style={{ marginBottom: 16 }}>
        <Descriptions column={2} size="small" bordered>
          <Descriptions.Item label="Database">{settings.database_type}</Descriptions.Item>
          <Descriptions.Item label="LLM Provider">{settings.llm_default_provider}</Descriptions.Item>
          <Descriptions.Item label="LLM Model">{settings.llm_default_model}</Descriptions.Item>
          <Descriptions.Item label="OpenAI Key">{settings.openai_key_set ? <Tag color="green">Configured</Tag> : <Tag color="red">Missing</Tag>}</Descriptions.Item>
          <Descriptions.Item label="Anthropic Key">{settings.anthropic_key_set ? <Tag color="green">Configured</Tag> : <Tag color="red">Missing</Tag>}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="LLM Connection Test" extra={<Button icon={<ReloadOutlined />} onClick={handleTest} loading={testing}>Test Connection</Button>}>
        {testResult && (
          <Alert
            type={testResult.status === "ok" ? "success" : "error"}
            message={testResult.status === "ok" ? `Connection OK (${testResult.provider})` : "Connection Failed"}
            description={testResult.detail || ""}
          />
        )}
        {!testResult && <p>Click "Test Connection" to verify your LLM API key works.</p>}
      </Card>
    </div>
  );
}

export default Settings;