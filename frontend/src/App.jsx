import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import DashboardPage from './pages/DashboardPage';
import ProductExplorerPage from './pages/ProductExplorerPage';
import PricingAnalysisPage from './pages/PricingAnalysisPage';
import ElasticityPage from './pages/ElasticityPage';
import SimulatorPage from './pages/SimulatorPage';
import InsightsPage from './pages/InsightsPage';
import CsvImportPage from './pages/CsvImportPage';
import MethodologyPage from './pages/MethodologyPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="products" element={<ProductExplorerPage />} />
          <Route path="pricing" element={<PricingAnalysisPage />} />
          <Route path="elasticity" element={<ElasticityPage />} />
          <Route path="simulator" element={<SimulatorPage />} />
          <Route path="insights" element={<InsightsPage />} />
          <Route path="data-import" element={<CsvImportPage />} />
          <Route path="methodology" element={<MethodologyPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
