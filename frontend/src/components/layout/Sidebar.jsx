import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  PackageSearch,
  Tag,
  TrendingDown,
  Sliders,
  Lightbulb,
  UploadCloud,
  BookOpen,
  Activity,
  Database
} from 'lucide-react';

const navItems = [
  { path: '/', label: 'Executive Dashboard', icon: LayoutDashboard },
  { path: '/products', label: 'Product Explorer', icon: PackageSearch },
  { path: '/pricing', label: 'Pricing & Margin Analysis', icon: Tag },
  { path: '/elasticity', label: 'Price Elasticity Engine', icon: TrendingDown },
  { path: '/simulator', label: 'What-If Simulator', icon: Sliders },
  { path: '/insights', label: 'Profit Insights', icon: Lightbulb },
  { path: '/data-import', label: 'CSV Import & Data', icon: UploadCloud },
  { path: '/methodology', label: 'Methodology & QA', icon: BookOpen },
];

export default function Sidebar() {
  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col shrink-0 border-r border-slate-800 select-none min-h-screen">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-5 gap-3 border-b border-slate-800/80">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center text-white shadow-md shadow-brand-500/20">
          <Activity className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center gap-1.5">
            <span className="font-bold text-white text-base tracking-tight">PricePulse</span>
            <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-brand-500/20 text-brand-300 border border-brand-500/30">
              v1.0
            </span>
          </div>
          <p className="text-[11px] text-slate-400 font-medium">Pricing & Profit Analytics</p>
        </div>
      </div>

      {/* Navigation List */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
          Analytics & Scenarios
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-brand-600 text-white shadow-sm shadow-brand-600/30'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span className="truncate">{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Data Environment Footer */}
      <div className="p-3.5 border-t border-slate-800/80 bg-slate-950/40">
        <div className="rounded-lg bg-slate-800/70 p-2.5 border border-slate-700/60 text-xs">
          <div className="flex items-center justify-between text-slate-300 mb-1">
            <span className="flex items-center gap-1.5 font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-400 pulse-live"></span>
              Live Engine
            </span>
            <span className="text-[10px] text-slate-400 flex items-center gap-1 font-mono">
              <Database className="w-3 h-3 text-slate-400" />
              SQLite
            </span>
          </div>
          <div className="text-[11px] text-slate-400 leading-tight">
            Deterministic synthetic catalog (~100 SKUs, 14 mos history).
          </div>
        </div>
      </div>
    </aside>
  );
}
