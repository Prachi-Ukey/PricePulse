import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Activity, RefreshCw, Upload, Sliders, ShieldCheck, AlertCircle } from 'lucide-react';
import { getHealth } from '../../api/client';

const pageTitles = {
  '/': 'Executive Performance Dashboard',
  '/products': 'Product Explorer & Catalog Metrics',
  '/pricing': 'Pricing Realization & Discount Analysis',
  '/elasticity': 'Price Elasticity Econometric Engine',
  '/simulator': 'What-If Margin & Revenue Simulator',
  '/insights': 'Profit Diagnostics & Margin Risk Alerts',
  '/data-import': 'CSV Data Management & Validation',
  '/methodology': 'Analytical Methodology & Formula Definitions',
};

export default function Header({ onRefresh, isRefreshing = false }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [health, setHealth] = useState(null);

  useEffect(() => {
    let isMounted = true;
    getHealth()
      .then((data) => {
        if (isMounted) setHealth(data);
      })
      .catch(() => {
        if (isMounted) setHealth({ status: 'offline' });
      });
    return () => { isMounted = false; };
  }, []);

  const currentTitle = pageTitles[location.pathname] || 'PricePulse Analytics';

  return (
    <header className="h-16 bg-white border-b border-slate-200/90 px-6 flex items-center justify-between sticky top-0 z-20 shadow-xs">
      {/* Title & Path */}
      <div className="flex items-center gap-3">
        <div>
          <h1 className="text-lg font-bold text-slate-900 tracking-tight leading-none">
            {currentTitle}
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Empirical pricing sensitivity, profit diagnostics, and demand modeling
          </p>
        </div>
      </div>

      {/* Controls & Actions */}
      <div className="flex items-center gap-3">
        {/* Synthetic Notice Tag */}
        <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-50 border border-amber-200/80 text-[11px] font-medium text-amber-800" title="Notice: Analysis is performed on deterministic synthetic retail data for testing and benchmarking purposes.">
          <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
          <span>Synthetic Test Data</span>
        </div>

        {/* Backend Connectivity Status */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-100 border border-slate-200 text-xs font-medium text-slate-700">
          <span
            className={`w-2 h-2 rounded-full ${
              health?.status === 'healthy' ? 'bg-emerald-500' : 'bg-rose-500'
            }`}
          />
          <span className="capitalize">{health?.status === 'healthy' ? 'API Online' : 'Connecting...'}</span>
        </div>

        {/* Action: Simulator */}
        <button
          onClick={() => navigate('/simulator')}
          className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition-colors border border-slate-200"
        >
          <Sliders className="w-3.5 h-3.5" />
          Simulator
        </button>

        {/* Action: Import */}
        <button
          onClick={() => navigate('/data-import')}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-50 hover:bg-brand-100 text-brand-700 text-xs font-semibold transition-colors border border-brand-200"
        >
          <Upload className="w-3.5 h-3.5" />
          Import CSV
        </button>

        {/* Refresh button */}
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors border border-slate-200"
            title="Refresh active view"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-brand-600' : ''}`} />
          </button>
        )}
      </div>
    </header>
  );
}
