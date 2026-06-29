import React from "react";
import { Routes, Route, Link, useLocation } from "react-router-dom";
import { Layout, Menu } from "antd";
import {
  DashboardOutlined,
  ScanOutlined,
  BugOutlined,
  SettingOutlined,
  ExperimentOutlined,
} from "@ant-design/icons";
import Dashboard from "./pages/Dashboard";
import Scans from "./pages/Scans";
import Results from "./pages/Results";
import Settings from "./pages/Settings";
import ExperimentResults from "./pages/ExperimentResults";

const { Header, Sider, Content } = Layout;

const menuItems = [
  { key: "/", icon: <DashboardOutlined />, label: <Link to="/">Dashboard</Link> },
  { key: "/scans", icon: <ScanOutlined />, label: <Link to="/scans">Scans</Link> },
  { key: "/results", icon: <BugOutlined />, label: <Link to="/results">Findings</Link> },
  { key: "/experiment/results", icon: <ExperimentOutlined />, label: <Link to="/experiment/results">Experiment</Link> },
  { key: "/settings", icon: <SettingOutlined />, label: <Link to="/settings">Settings</Link> },
];

function App() {
  const location = useLocation();

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider breakpoint="lg" collapsedWidth="0">
        <div style={{ height: 32, margin: 16, color: "#fff", fontWeight: "bold", fontSize: 16 }}>
          VulnForge
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
        />
      </Sider>
      <Layout>
        <Content style={{ margin: 24 }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/scans" element={<Scans />} />
            <Route path="/results" element={<Results />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/experiment/results" element={<ExperimentResults />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}

export default App;