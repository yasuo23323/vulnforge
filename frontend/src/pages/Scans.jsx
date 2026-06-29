import React, { useEffect, useState } from "react";
import { Table, Button, Modal, Form, Input, Select, Tag, message, Space, Typography } from "antd";
import { PlusOutlined, DeleteOutlined, ReloadOutlined } from "@ant-design/icons";
import { getScans, createScan, deleteScan } from "../api";

const { Title } = Typography;

function Scans() {
  const [scans, setScans] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  const load = async () => {
    setLoading(true);
    try {
      const res = await getScans(page);
      setScans(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (e) {
      message.error("Failed to load scans");
    }
    setLoading(false);
  };

  useEffect(() => { load(); }, [page]);

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      await createScan(values);
      message.success("Scan created!");
      setModalOpen(false);
      form.resetFields();
      load();
    } catch (e) {
      if (e.response) message.error(e.response.data?.detail || "Failed to create scan");
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteScan(id);
      message.success("Scan deleted");
      load();
    } catch (e) {
      message.error("Failed to delete scan");
    }
  };

  const columns = [
    { title: "Target", dataIndex: "target_url", key: "target_url", ellipsis: true },
    { title: "Name", dataIndex: "target_name", key: "target_name" },
    { title: "Status", dataIndex: "status", key: "status", render: (s) => (
      <Tag color={s === "completed" ? "green" : s === "failed" ? "red" : s === "running" ? "blue" : "default"}>{s}</Tag>
    )},
    { title: "Findings", dataIndex: "findings_count", key: "findings_count" },
    { title: "Error", dataIndex: "error_message", key: "error_message", ellipsis: true },
    { title: "Created", dataIndex: "created_at", key: "created_at", render: (d) => d ? new Date(d).toLocaleString() : "" },
    { title: "Actions", key: "actions", render: (_, record) => (
      <Button danger size="small" icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)} />
    )},
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={3}>Scans</Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={load}>Refresh</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>New Scan</Button>
        </Space>
      </div>

      <Table
        dataSource={scans}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{ current: page, total, pageSize: 20, onChange: setPage }}
        size="small"
      />

      <Modal title="New Scan" open={modalOpen} onOk={handleCreate} onCancel={() => setModalOpen(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="target_url" label="Target URL" rules={[{ required: true, message: "Please enter a URL" }]}>
            <Input placeholder="http://example.com" />
          </Form.Item>
          <Form.Item name="target_name" label="Name (optional)">
            <Input placeholder="My target" />
          </Form.Item>
          <Form.Item name="scanners" label="Scanners" initialValue={["nuclei", "dalfox", "ffuf", "sqlmap"]}>
            <Select mode="multiple" options={[
              { value: "nuclei", label: "Nuclei" },
              { value: "dalfox", label: "Dalfox" },
              { value: "ffuf", label: "FFUF" },
              { value: "sqlmap", label: "SQLMap" },
            ]} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default Scans;