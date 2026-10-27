import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Tag,
  AlertTriangle,
  TrendingDown,
  Sparkles,
  Sliders,
  DollarSign,
  Filter,
  ArrowRight,
  HelpCircle,
  Layers,
  CheckCircle2
} from 'lucide-react';
import { getPricingAnalysis, getCategories } from '../api/client';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorState from '../components/common/ErrorState';
import Badge from '../components/common/Badge';

export default function PricingAnalysisPage() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [category, setCategory] = useState('');
  const [healthStatus, setHealthStatus] = useState('');

  const fetchPricing = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getPricingAnalysis({
        category: category || undefined,
        health_status: healthStatus || undefined,
      });
      setData(res);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load pricing analysis.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getCategories().then(setCategories).catch(() => {});
  }, []);

  useEffect(() => {
    fetchPricing();
  }, [category, healthStatus]);

  if (loading && !data) {
    return <LoadingSpinner message="Auditing catalog discount realization and price variance..." />;
  }

  if (error && !data) {
    return <ErrorState message={error} onRetry={fetchPricing} />;
  }

  return (
    <div className="space-y-6">
      {/* Scope Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Pricing Realization & Discount Analysis</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Audit realized ASP, promotional discount leakage, margin health, and empirical price elasticity across catalog products.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
            {category ? `Category Scope: ${category}` : 'Catalog Scope (All Categories)'}
          </span>
          {healthStatus && (
            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-brand-50 text-brand-700 border border-brand-200">
              Filter: {healthStatus.replace('_', ' ')} ({data?.total_items} items)
            </span>
          )}
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="card-enterprise p-4 bg-white">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider">Average Discount</span>
            <Tag className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900 font-mono">
            {data?.summary?.catalog_average_discount_pct?.toFixed(1)}%
          </div>
          <div className="text-xs text-slate-400 mt-0.5">Weighted markdown ({category || 'Catalog'})</div>
        </div>

        <div className="card-enterprise p-4 bg-white">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider">Discount Spend</span>
            <DollarSign className="w-4 h-4 text-slate-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900 font-mono">
            ${(data?.summary?.total_discount_dollars_given || 0).toLocaleString('en-US', { maximumFractionDigits: 0 })}
          </div>
          <div className="text-xs text-slate-400 mt-0.5">Total concessions ({category || 'Catalog'})</div>
        </div>

        <div className="card-enterprise p-4 bg-white">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider">Margin Threats</span>
            <AlertTriangle className="w-4 h-4 text-rose-600" />
          </div>
          <div className="text-2xl font-bold text-rose-600 font-mono">
            {data?.summary?.low_margin_skus_count || 0}
          </div>
          <div className="text-xs text-rose-500 mt-0.5 font-medium">
            {data?.summary?.negative_margin_skus_count
              ? `${data.summary.negative_margin_skus_count} negative (<0%)`
              : '< 15% Gross Margin'}
          </div>
        </div>

        <div className="card-enterprise p-4 bg-white">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider">Review Required</span>
            <HelpCircle className="w-4 h-4 text-purple-600" />
          </div>
          <div className="text-2xl font-bold text-purple-700 font-mono">
            {data?.summary?.review_required_skus_count || 0}
          </div>
          <div className="text-xs text-slate-400 mt-0.5">β ≥ 0 or CI spans 0</div>
        </div>

        <div className="card-enterprise p-4 bg-white">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider">Data Incomplete</span>
            <Layers className="w-4 h-4 text-slate-500" />
          </div>
          <div className="text-2xl font-bold text-slate-700 font-mono">
            {data?.summary?.not_enough_data_skus_count || 0}
          </div>
          <div className="text-xs text-slate-400 mt-0.5">Static price / low data</div>
        </div>

        <div className="card-enterprise p-4 bg-white">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider">Pricing Power</span>
            <Sparkles className="w-4 h-4 text-brand-600" />
          </div>
          <div className="text-2xl font-bold text-brand-600 font-mono">
            {data?.summary?.underpriced_skus_count || 0}
          </div>
          <div className="text-xs text-slate-400 mt-0.5">Inelastic & high margin</div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="card-enterprise p-4 bg-white flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-700">
          <Filter className="w-4 h-4 text-brand-600" />
          <span>PRICING SEGMENT FILTERS:</span>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>

          <select
            value={healthStatus}
            onChange={(e) => setHealthStatus(e.target.value)}
            className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option value="">All Health Statuses</option>
            <option value="NEGATIVE_MARGIN">Negative Margin (&lt;0%)</option>
            <option value="LOW_MARGIN">Low Margin (&lt;15%)</option>
            <option value="HEAVILY_DISCOUNTED">Heavily Discounted (≥18%)</option>
            <option value="REVIEW_REQUIRED">Review Required (β ≥ 0 or CI Spans 0)</option>
            <option value="UNDERPRICED">Underpriced (Pricing Power)</option>
            <option value="OPTIMAL">Optimal</option>
            <option value="NOT_ENOUGH_DATA">Not Enough Data</option>
          </select>

          {(category || healthStatus) && (
            <button
              onClick={() => {
                setCategory('');
                setHealthStatus('');
              }}
              className="text-xs text-brand-600 hover:text-brand-800 font-semibold px-2 py-1"
            >
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Pricing Analysis Table */}
      <div className="card-enterprise bg-white overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-400 font-semibold uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">Product / SKU</th>
                <th className="py-3 px-3">Category</th>
                <th className="py-3 px-3 text-right">MSRP</th>
                <th className="py-3 px-3 text-right">Realized ASP</th>
                <th className="py-3 px-3 text-right">Price Variance</th>
                <th className="py-3 px-3 text-right">Avg Discount</th>
                <th className="py-3 px-3 text-right">Margin %</th>
                <th className="py-3 px-3 text-center">Elasticity</th>
                <th className="py-3 px-3 text-center">Health Status</th>
                <th className="py-3 px-4">Business Recommendation & Rationale</th>
                <th className="py-3 px-3 text-center">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {data?.items?.map((item) => (
                <tr key={item.product_id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3 px-4">
                    <div className="font-semibold text-slate-900 leading-tight">
                      {item.name}
                    </div>
                    <div className="text-[11px] font-mono text-slate-400 mt-0.5">
                      {item.sku}
                    </div>
                  </td>
                  <td className="py-3 px-3 text-slate-600">
                    <span className="inline-block px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[11px]">
                      {item.category}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-right font-mono text-slate-700">
                    ${item.base_price.toFixed(2)}
                  </td>
                  <td className="py-3 px-3 text-right font-mono text-slate-900 font-semibold">
                    ${item.asp.toFixed(2)}
                  </td>
                  <td className="py-3 px-3 text-right font-mono">
                    {item.price_variance_pct > 0 ? (
                      <span className="inline-block px-1.5 py-0.5 rounded text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        +{item.price_variance_pct.toFixed(1)}% Premium
                      </span>
                    ) : (
                      <span
                        className={
                          item.price_variance_pct < -15
                            ? 'text-rose-600 font-semibold'
                            : item.price_variance_pct < 0
                            ? 'text-amber-600'
                            : 'text-slate-700'
                        }
                      >
                        {item.price_variance_pct.toFixed(1)}%
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-3 text-right font-mono text-slate-700">
                    <div>{item.avg_discount_pct.toFixed(1)}%</div>
                    {(item.is_above_msrp || item.price_variance_pct > 0) && (
                      <div className="text-[9px] text-emerald-600 font-sans font-medium">
                        (Net Premium ASP)
                      </div>
                    )}
                  </td>
                  <td className="py-3 px-3 text-right">
                    {item.gross_margin === null ? (
                      <span className="text-slate-400 font-mono italic text-[11px]">Missing Cost</span>
                    ) : (
                      <div>
                        <span
                          className={`inline-block px-1.5 py-0.5 rounded text-[11px] font-semibold ${
                            item.gross_margin < 0
                              ? 'bg-rose-100 text-rose-800 border border-rose-300 font-bold'
                              : item.gross_margin >= 0.4
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              : item.gross_margin >= 0.2
                              ? 'bg-brand-50 text-brand-700 border border-brand-200'
                              : 'bg-rose-50 text-rose-700 border border-rose-200'
                          }`}
                        >
                          {(item.gross_margin * 100).toFixed(1)}%
                        </span>
                        {item.gross_margin < 0 && (
                          <div className="text-[9px] text-rose-600 font-sans font-bold uppercase tracking-tight mt-0.5">
                            Negative Margin Alert
                          </div>
                        )}
                      </div>
                    )}
                  </td>
                  <td className="py-3 px-3 text-center">
                    {item.elasticity !== null ? (
                      <div>
                        <div className="font-mono font-semibold text-slate-800 text-[11px]">
                          β = {item.elasticity.toFixed(2)}
                        </div>
                        {item.confidence_interval_95 && (
                          <div className="text-[10px] font-mono text-slate-400">
                            [{item.confidence_interval_95[0].toFixed(2)}, {item.confidence_interval_95[1].toFixed(2)}]
                          </div>
                        )}
                        {item.ci_crosses_zero && (
                          <span className="inline-block mt-0.5 px-1.5 py-0.2 rounded text-[9px] font-medium bg-amber-50 text-amber-700 border border-amber-200">
                            CI spans 0 (Inconclusive)
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="text-[10px] text-slate-400 italic">
                        {item.elasticity_status === 'NO_PRICE_VARIATION' ? 'Static Price' : 'Low Data'}
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-3 text-center">
                    <Badge label={item.pricing_health} variant={item.pricing_health} size="xs" />
                  </td>
                  <td className="py-3 px-4 max-w-sm">
                    {item.pricing_health === 'NEGATIVE_MARGIN' && (
                      <div className="mb-1">
                        <span className="inline-block px-1.5 py-0.5 rounded text-[9px] font-bold bg-rose-100 text-rose-800 border border-rose-300 uppercase tracking-wider">
                          Diagnostic Audit Required
                        </span>
                      </div>
                    )}
                    <div className="font-semibold text-slate-800 leading-tight">
                      {item.recommendation || '—'}
                    </div>
                    {item.recommendation_reason && (
                      <div className="text-[11px] text-slate-500 mt-1 leading-snug">
                        {item.recommendation_reason}
                      </div>
                    )}
                  </td>
                  <td className="py-3 px-3 text-center">
                    <button
                      onClick={() => navigate(`/simulator?product_id=${item.product_id}`)}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-100 hover:bg-brand-50 hover:text-brand-700 text-slate-700 text-xs font-semibold transition-colors border border-slate-200"
                    >
                      <Sliders className="w-3.5 h-3.5" />
                      Simulate
                    </button>
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
