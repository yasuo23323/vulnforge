import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 30000,
});

export const getScans = (page = 1, pageSize = 20) =>
  api.get("/scans", { params: { page, page_size: pageSize } });

export const createScan = (data) => api.post("/scans", data);

export const getScan = (id) => api.get(`/scans/${id}`);

export const deleteScan = (id) => api.delete(`/scans/${id}`);

export const getFindings = (params = {}) =>
  api.get("/findings", { params });

export const getFinding = (id) => api.get(`/findings/${id}`);

export const analyzeFinding = (id, strategy = "zero_shot") =>
  api.post(`/findings/${id}/analyze`, null, { params: { strategy } });

export const getSettings = () => api.get("/settings");

export const testLLM = () => api.post("/settings/test");

export const getHealth = () => api.get("/health");

export default api;