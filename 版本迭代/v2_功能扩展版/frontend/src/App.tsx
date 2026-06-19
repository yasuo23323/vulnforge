import React from "react";
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
