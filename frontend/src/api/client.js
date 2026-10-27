import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// System & Health
export const getHealth = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};

// Dashboard
export const getDashboardMetrics = async (params = {}) => {
  const response = await apiClient.get('/dashboard', { params });
  return response.data;
};

// Products
export const getProducts = async (params = {}) => {
  const response = await apiClient.get('/products', { params });
  return response.data;
};

export const getProductDetail = async (id) => {
  const response = await apiClient.get(`/products/${id}`);
  return response.data;
};

export const getCategories = async () => {
  const response = await apiClient.get('/products/categories');
  return response.data;
};

export const getChannels = async () => {
  const response = await apiClient.get('/products/channels');
  return response.data;
};

export const getExportCsvUrl = (params = {}) => {
  const query = new URLSearchParams(params).toString();
  return `${API_BASE_URL}/products/export${query ? `?${query}` : ''}`;
};

// Pricing Analysis
export const getPricingAnalysis = async (params = {}) => {
  const response = await apiClient.get('/pricing', { params });
  return response.data;
};

// Elasticity Engine
export const getElasticityOverview = async (params = {}) => {
  const response = await apiClient.get('/elasticity', { params });
  return response.data;
};

export const getProductElasticity = async (id) => {
  const response = await apiClient.get(`/elasticity/${id}`);
  return response.data;
};

// Simulator
export const runSimulator = async (payload) => {
  const response = await apiClient.post('/simulator/run', payload);
  return response.data;
};

export const getSimulatorDefaults = async (productId) => {
  const response = await apiClient.get(`/simulator/defaults/${productId}`);
  return response.data;
};

// Profit Insights
export const getProfitInsights = async () => {
  const response = await apiClient.get('/insights');
  return response.data;
};

// Data Management & CSV Import
export const previewCsvFile = async (formData) => {
  const response = await apiClient.post('/data/preview', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const importCsvFile = async (formData) => {
  const response = await apiClient.post('/data/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const getSampleTemplateUrl = () => {
  return `${API_BASE_URL}/data/sample-template`;
};

export const resetSyntheticData = async () => {
  const response = await apiClient.post('/data/reset-synthetic');
  return response.data;
};

export const getImportLogs = async () => {
  const response = await apiClient.get('/data/logs');
  return response.data;
};

export default apiClient;
