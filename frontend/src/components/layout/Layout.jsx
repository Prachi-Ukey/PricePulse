import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

export default function Layout() {
  const [refreshKey, setRefreshKey] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = () => {
    setIsRefreshing(true);
    setRefreshKey((prev) => prev + 1);
    setTimeout(() => {
      setIsRefreshing(false);
    }, 500);
  };

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-800 font-sans">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Header onRefresh={handleRefresh} isRefreshing={isRefreshing} />
        <main className="flex-1 p-6 overflow-y-auto max-w-7xl w-full mx-auto">
          {/* Global Synthetic Data Disclaimer Banner */}
          <div className="mb-5 px-4 py-2.5 rounded-lg bg-indigo-50/70 border border-indigo-100 flex items-center justify-between text-xs text-indigo-950">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-brand-700">Environment Active:</span>
              <span>Connected to local PricePulse analytics server with deterministic synthetic retail catalog.</span>
            </div>
            <a
              href="/methodology"
              className="text-brand-700 hover:text-brand-900 font-semibold underline underline-offset-2 ml-4 shrink-0"
            >
              View Methodology & Formula QA →
            </a>
          </div>

          <Outlet key={refreshKey} />
        </main>
      </div>
    </div>
  );
}
