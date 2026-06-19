import React from "react";
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
