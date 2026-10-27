import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Lightbulb,
  AlertTriangle,
  TrendingDown,
  Sparkles,
  ShieldAlert,
  ArrowRight,
  Sliders,
  DollarSign,
  Package,
  Layers
} from 'lucide-react';
import { getProfitInsights } from '../api/client';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorState from '../components/common/ErrorState';
import Badge from '../components/common/Badge';

export default function InsightsPage() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterType, setFilterType] = useState('ALL');

  const fetchInsights = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getProfitInsights();
      setData(res);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to query profitability diagnostics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInsights();
  }, []);

  if (loading && !data) {
    return <LoadingSpinner message="Scanning transaction records for margin leakage and pricing anomalies..." />;
  }

  if (error && !data) {
    return <ErrorState message={error} onRetry={fetchInsights} />;
  }

  const filteredAlerts = (data?.alerts || []).filter((a) => {
    if (filterType === 'ALL') return true;
    return a.type === filterType;
  });

  return (
    <div className="space-y-6">
      {/* Top Diagnostics Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card-enterprise p-5 bg-white border-rose-200">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-rose-700">
              Revenue at Margin Risk
            </span>
            <AlertTriangle className="w-4 h-4 text-rose-600" />
          </div>
          <div className="text-2xl font-bold text-rose-600 font-mono">
            ${(data?.summary_stats?.revenue_at_margin_risk || 0).toLocaleString('en-US', { maximumFractionDigits: 0 })}
          </div>
          <div className="text-xs text-slate-400 mt-1">Products operating under 15% margin</div>
        </div>

        <div className="card-enterprise p-5 bg-white border-amber-200">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-amber-700">
              Discount Cannibalization
            </span>
            <TrendingDown className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl font-bold text-amber-600 font-mono">
            ${(data?.summary_stats?.discount_leakage_dollars || 0).toLocaleString('en-US', { maximumFractionDigits: 0 })}
          </div>
          <div className="text-xs text-slate-400 mt-1">Concessions given on inelastic demand</div>
        </div>

        <div className="card-enterprise p-5 bg-white border-emerald-200">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-700">
              Annual Margin Upside
            </span>
            <Sparkles className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-bold text-emerald-600 font-mono">
            +${(data?.summary_stats?.estimated_annual_margin_upside || 0).toLocaleString('en-US', { maximumFractionDigits: 0 })}
          </div>
          <div className="text-xs text-slate-400 mt-1">Modeled projection (+4% test on validated inelastic SKUs)</div>
        </div>

        <div className="card-enterprise p-5 bg-white">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-600">
              Active Strategy Alerts
            </span>
            <ShieldAlert className="w-4 h-4 text-brand-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900 font-mono">
            {data?.summary_stats?.total_active_alerts || 0}
          </div>
          <div className="text-xs text-slate-400 mt-1">
            {data?.summary_stats?.critical_alerts_count || 0} requiring priority action
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 pb-3">
        <button
          onClick={() => setFilterType('ALL')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
            filterType === 'ALL'
              ? 'bg-slate-900 text-white'
              : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
          }`}
        >
          All Issues ({data?.alerts?.length || 0})
        </button>
        <button
          onClick={() => setFilterType('CRITICAL_MARGIN')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
            filterType === 'CRITICAL_MARGIN'
              ? 'bg-rose-600 text-white'
              : 'bg-white text-rose-700 border border-rose-200 hover:bg-rose-50'
          }`}
        >
          Critical Margin Risks
        </button>
        <button
          onClick={() => setFilterType('INEFFECTIVE_DISCOUNT')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
            filterType === 'INEFFECTIVE_DISCOUNT'
              ? 'bg-amber-600 text-white'
              : 'bg-white text-amber-700 border border-amber-200 hover:bg-amber-50'
          }`}
        >
          Discount Cannibalization
        </button>
        <button
          onClick={() => setFilterType('UNEXPLOITED_INELASTICITY')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
            filterType === 'UNEXPLOITED_INELASTICITY'
              ? 'bg-emerald-600 text-white'
              : 'bg-white text-emerald-700 border border-emerald-200 hover:bg-emerald-50'
          }`}
        >
          Pricing Power Upside
        </button>
        <button
          onClick={() => setFilterType('DATA_QUALITY')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
            filterType === 'DATA_QUALITY'
              ? 'bg-indigo-600 text-white'
              : 'bg-white text-indigo-700 border border-indigo-200 hover:bg-indigo-50'
          }`}
        >
          Elasticity Anomalies
        </button>
      </div>

      {/* Flagged Item Cards */}
      <div className="space-y-4">
        {filteredAlerts.map((alert) => (
          <div
            key={alert.id}
            className={`card-enterprise p-5 bg-white border-l-4 ${
              alert.severity === 'high'
                ? 'border-l-rose-500'
                : alert.severity === 'medium'
                ? 'border-l-amber-500'
                : 'border-l-brand-500'
            }`}
          >
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <Badge label={alert.severity.toUpperCase()} variant={alert.severity} size="xs" />
                  <span className="text-xs font-mono font-semibold text-slate-500">
                    {alert.sku}
                  </span>
                  <span className="text-xs text-slate-400">• {alert.category}</span>
                </div>
                <h3 className="text-base font-bold text-slate-900 mt-1">{alert.title}</h3>
              </div>

              <div className="flex items-center gap-3">
                <div className="text-right">
                  <span className="text-xs font-mono font-bold text-slate-900 block">
                    {alert.metric_value}
                  </span>
                  <span className="text-[11px] text-slate-400 block">{alert.benchmark_value}</span>
                </div>
                {alert.product_id && (
                  <button
                    onClick={() => navigate(`/simulator?product_id=${alert.product_id}`)}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-brand-50 hover:text-brand-700 text-slate-700 text-xs font-semibold transition-colors border border-slate-200"
                  >
                    <Sliders className="w-3.5 h-3.5" />
                    Simulate
                  </button>
                )}
              </div>
            </div>

            <p className="text-xs text-slate-600 mt-3 leading-relaxed">{alert.description}</p>

            <div className="mt-3 p-2.5 rounded-lg bg-slate-50 border border-slate-200/80 flex items-start gap-2 text-xs">
              <span className="font-semibold text-slate-900 shrink-0">Recommendation:</span>
              <span className="text-slate-700">{alert.recommendation}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Category Risk Map */}
      <div className="card-enterprise p-5 bg-white">
        <div className="pb-3 mb-4 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <Layers className="w-4 h-4 text-brand-600" />
              Category Portfolio Profitability Risk Matrix
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Aggregated margin distribution and vulnerability assessment across active product families.
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-400 font-semibold uppercase">
              <tr>
                <th className="py-2.5 px-3">Category</th>
                <th className="py-2.5 px-3 text-right">Category Revenue</th>
                <th className="py-2.5 px-3 text-right">Gross Profit</th>
                <th className="py-2.5 px-3 text-right">Category Margin %</th>
                <th className="py-2.5 px-3 text-center">Low-Margin SKUs</th>
                <th className="py-2.5 px-3 text-center">Risk Level</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {data?.category_risk_map?.map((cat) => (
                <tr key={cat.category} className="hover:bg-slate-50">
                  <td className="py-2.5 px-3 font-semibold text-slate-800">{cat.category}</td>
                  <td className="py-2.5 px-3 text-right font-mono text-slate-900">
                    ${cat.revenue.toLocaleString()}
                  </td>
                  <td className="py-2.5 px-3 text-right font-mono text-emerald-600 font-semibold">
                    ${cat.profit.toLocaleString()}
                  </td>
                  <td className="py-2.5 px-3 text-right font-mono font-bold">
                    {(cat.margin * 100).toFixed(1)}%
                  </td>
                  <td className="py-2.5 px-3 text-center font-mono">
                    <span
                      className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                        cat.low_margin_skus > 0 ? 'bg-rose-50 text-rose-700' : 'bg-slate-100 text-slate-600'
                      }`}
                    >
                      {cat.low_margin_skus} / {cat.total_skus} SKUs
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-center">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-[11px] font-semibold ${
                        cat.risk_level === 'High'
                          ? 'bg-rose-50 text-rose-700 border border-rose-200'
                          : cat.risk_level === 'Moderate'
                          ? 'bg-amber-50 text-amber-700 border border-amber-200'
                          : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      }`}
                    >
                      {cat.risk_level}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
