import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  HelpCircle,
  Sliders,
  BarChart,
  Info,
  Layers,
  ArrowRight,
  Activity
} from 'lucide-react';
import {
  ResponsiveContainer,
  ComposedChart,
  Scatter,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';
import { getElasticityOverview, getProductElasticity } from '../api/client';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorState from '../components/common/ErrorState';
import Badge from '../components/common/Badge';
import { formatPValue, getModelFitInfo } from '../utils/formatters';

export default function ElasticityPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const [catalogOverview, setCatalogOverview] = useState([]);
  const [selectedProductId, setSelectedProductId] = useState(null);
  const [elasticityResult, setElasticityResult] = useState(null);
  const [loadingOverview, setLoadingOverview] = useState(true);
  const [loadingProduct, setLoadingProduct] = useState(false);
  const [error, setError] = useState(null);

  // Load catalog overview on mount
  useEffect(() => {
    setLoadingOverview(true);
    getElasticityOverview()
      .then((items) => {
        setCatalogOverview(items);
        // If URL param product_id exists, select it; otherwise pick first item
        const urlId = searchParams.get('product_id');
        const initialId = urlId ? Number(urlId) : items[0]?.product_id;
        if (initialId) {
          setSelectedProductId(initialId);
        }
      })
      .catch((err) => setError(err?.response?.data?.detail || 'Failed to load elasticity catalog.'))
      .finally(() => setLoadingOverview(false));
  }, []);

  // Fetch single product elasticity details when selectedProductId changes
  useEffect(() => {
    if (!selectedProductId) return;
    setLoadingProduct(true);
    getProductElasticity(selectedProductId)
      .then((res) => {
        setElasticityResult(res);
        setSearchParams({ product_id: selectedProductId });
      })
      .catch((err) => console.error(err))
      .finally(() => setLoadingProduct(false));
  }, [selectedProductId]);

  if (loadingOverview && !catalogOverview.length) {
    return <LoadingSpinner message="Calculating log-log OLS elasticity regressions and confidence intervals..." />;
  }

  if (error && !catalogOverview.length) {
    return <ErrorState message={error} onRetry={() => window.location.reload()} />;
  }

  const isEstimated = elasticityResult?.status === 'ESTIMATED';
  const isInsufficient = elasticityResult?.status === 'INSUFFICIENT_DATA';
  const isNoVariance = elasticityResult?.status === 'NO_PRICE_VARIATION';

  return (
    <div className="space-y-6">
      {/* Top Product Selector & Switcher */}
      <div className="card-enterprise p-4 bg-white flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <TrendingDown className="w-5 h-5 text-brand-600" />
          <div>
            <h2 className="text-sm font-bold text-slate-900 leading-none">
              Price Elasticity of Demand (PED) Engine
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Ordinary Least Squares (OLS) Log-Log regression: ln(Quantity) = α + β·ln(Price)
            </p>
          </div>
        </div>

        {/* Product Dropdown Selector */}
        <div className="flex items-center gap-3">
          <label htmlFor="product-select" className="text-xs font-semibold text-slate-600">Select Product:</label>
          <select
            id="product-select"
            value={selectedProductId || ''}
            onChange={(e) => setSelectedProductId(Number(e.target.value))}
            className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 font-medium text-slate-800 max-w-xs truncate focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            {catalogOverview.map((item) => (
              <option key={item.product_id} value={item.product_id}>
                {item.sku} — {item.product_name} ({item.status})
              </option>
            ))}
          </select>
        </div>
      </div>

      {loadingProduct && !elasticityResult ? (
        <LoadingSpinner message="Computing econometric diagnostics..." />
      ) : elasticityResult ? (
        <div className="space-y-6">
          {/* Main Elasticity Hero Card */}
          <div className="card-enterprise p-6 bg-white">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-4 border-b border-slate-100">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-brand-50 text-brand-700 border border-brand-200">
                    {elasticityResult.sku}
                  </span>
                  <span className="text-xs text-slate-500 font-medium">{elasticityResult.category}</span>
                  <Badge label={elasticityResult.status} variant={elasticityResult.status} />
                </div>
                <h3 className="text-lg font-bold text-slate-900 mt-1">
                  {elasticityResult.product_name}
                </h3>
              </div>

              {isEstimated && elasticityResult.elasticity != null && elasticityResult.elasticity < 0 ? (
                <button
                  onClick={() =>
                    navigate(
                      `/simulator?product_id=${elasticityResult.product_id}&elasticity=${elasticityResult.elasticity}`
                    )
                  }
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold transition-colors shadow-xs"
                >
                  <Sliders className="w-4 h-4" />
                  Simulate Strategy with β = {elasticityResult.elasticity}
                </button>
              ) : isEstimated && elasticityResult.elasticity != null && elasticityResult.elasticity >= 0 ? (
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-50 text-amber-800 border border-amber-200 text-xs font-medium">
                  Non-negative β ineligible for empirical strategy simulation
                </span>
              ) : null}
            </div>

            {/* Status-dependent content */}
            {isEstimated ? (
              <div className="mt-6 space-y-6">
                {/* Elasticity Metric Banner */}
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-wrap items-center justify-between gap-6">
                  <div>
                    <span className="text-xs uppercase font-bold tracking-wider text-slate-400">
                      Point Price Elasticity (β)
                    </span>
                    <div className="text-3xl font-extrabold text-brand-700 font-mono mt-1">
                      {elasticityResult.elasticity}
                    </div>
                    <div className="text-xs font-semibold text-slate-700 mt-1">
                      Demand Type: <Badge label={elasticityResult.interpretation} variant={elasticityResult.interpretation} />
                    </div>
                  </div>

                  {/* 95% Confidence Interval */}
                  <div className="border-l border-slate-200 pl-6">
                    <span className="text-xs uppercase font-bold tracking-wider text-slate-400">
                      95% Confidence Interval
                    </span>
                    <div className="text-lg font-bold text-slate-800 font-mono mt-1">
                      [{elasticityResult.confidence_interval_95?.[0]} , {elasticityResult.confidence_interval_95?.[1]}]
                    </div>
                    <div className="text-xs text-slate-500 mt-0.5">
                      Student's t critical bound (df = {elasticityResult.sample_size - 2})
                    </div>
                    {elasticityResult.ci_crosses_boundary && (
                      <span className="inline-block mt-1 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-amber-100 text-amber-800 border border-amber-200">
                        Spans category boundaries
                      </span>
                    )}
                  </div>

                  {/* Goodness of Fit & Significance */}
                  <div className="border-l border-slate-200 pl-6">
                    <span className="text-xs uppercase font-bold tracking-wider text-slate-400">
                      Statistical Significance
                    </span>
                    <div className="text-base font-bold text-slate-900 font-mono mt-1">
                      p-value: {formatPValue(elasticityResult.p_value, elasticityResult.p_value_display)}
                    </div>
                    <div className="text-xs text-slate-500 mt-0.5">
                      {elasticityResult.p_value < 0.05 ? (
                        <span className="text-emerald-600 font-medium">Statistically significant (p &lt; 0.05)</span>
                      ) : (
                        <span className="text-amber-600 font-medium">Marginal significance</span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Model Fit Indicator Card based on R² with Cautious Interpretation */}
                {(() => {
                  const fitInfo = getModelFitInfo(elasticityResult.r_squared);
                  return (
                    <div className="p-4 rounded-xl bg-slate-50/70 border border-slate-200">
                      <div className="flex items-center justify-between gap-3 flex-wrap">
                        <div className="flex items-center gap-2">
                          <Activity className="w-4 h-4 text-brand-600 shrink-0" />
                          <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                            Model-Fit Indicator:
                          </span>
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border ${fitInfo.colorClass}`}>
                            {fitInfo.label} (R² = {elasticityResult.r_squared !== null ? elasticityResult.r_squared.toFixed(4) : '—'})
                          </span>
                        </div>
                        <span className="text-[11px] text-slate-500 font-medium">
                          Active Observations: {elasticityResult.sample_size} days | {elasticityResult.unique_price_points ?? '—'} unique price points
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                        {elasticityResult.model_fit_description || fitInfo.description}
                      </p>
                    </div>
                  );
                })()}

                {/* Warning message if anomalous positive */}
                {elasticityResult.warning_message && (
                  <div className="p-3.5 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-900 flex items-start gap-2.5">
                    <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                    <div>
                      <strong className="font-semibold">Econometric Warning:</strong>{' '}
                      {elasticityResult.warning_message}
                    </div>
                  </div>
                )}

                {/* Econometric Parameters Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-xs">
                  <div className="p-3 bg-white border border-slate-200 rounded-lg">
                    <span className="text-slate-400 font-medium uppercase text-[10px]">Active Obs (N)</span>
                    <div className="text-sm font-bold text-slate-800 font-mono mt-0.5">{elasticityResult.sample_size} days</div>
                  </div>
                  <div className="p-3 bg-white border border-slate-200 rounded-lg">
                    <span className="text-slate-400 font-medium uppercase text-[10px]">Unique Prices</span>
                    <div className="text-sm font-bold text-slate-800 font-mono mt-0.5">{elasticityResult.unique_price_points ?? '—'} prices</div>
                  </div>
                  <div className="p-3 bg-white border border-slate-200 rounded-lg">
                    <span className="text-slate-400 font-medium uppercase text-[10px]">Deg of Freedom</span>
                    <div className="text-sm font-bold text-slate-800 font-mono mt-0.5">df = {elasticityResult.sample_size - 2}</div>
                  </div>
                  <div className="p-3 bg-white border border-slate-200 rounded-lg">
                    <span className="text-slate-400 font-medium uppercase text-[10px]">R² (In-Sample Fit)</span>
                    <div className="text-sm font-bold text-slate-800 font-mono mt-0.5">{elasticityResult.r_squared}</div>
                  </div>
                  <div className="p-3 bg-white border border-slate-200 rounded-lg">
                    <span className="text-slate-400 font-medium uppercase text-[10px]">Std Error (SE)</span>
                    <div className="text-sm font-bold text-slate-800 font-mono mt-0.5">{elasticityResult.standard_error}</div>
                  </div>
                  <div className="p-3 bg-white border border-slate-200 rounded-lg">
                    <span className="text-slate-400 font-medium uppercase text-[10px]">t-Statistic</span>
                    <div className="text-sm font-bold text-slate-800 font-mono mt-0.5">{elasticityResult.t_statistic}</div>
                  </div>
                </div>

                {/* Scatter Plot & Fitted Demand Curve with 95% Confidence Band */}
                <div className="p-4 border border-slate-200 rounded-xl bg-white">
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                    <div>
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                        Empirical Price vs Demand Observations & Fitted Curve
                      </h4>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        Log-log regression curve with 95% point-wise confidence band over realized prices
                      </p>
                    </div>
                    <div className="flex items-center gap-3 text-[11px] font-medium text-slate-500">
                      <span className="flex items-center gap-1.5">
                        <span className="w-2.5 h-2.5 rounded-full bg-indigo-600 inline-block border border-white shadow-xs"></span>
                        Product-Day Sales
                      </span>
                      <span className="flex items-center gap-1.5">
                        <span className="w-4 h-0.5 bg-blue-600 inline-block"></span>
                        Fitted Curve
                      </span>
                      <span className="flex items-center gap-1.5">
                        <span className="w-4 h-2.5 bg-blue-100 border border-blue-300 border-dashed inline-block rounded-xs"></span>
                        95% CI Band
                      </span>
                    </div>
                  </div>

                  <div className="h-80 w-full pt-2">
                    <ResponsiveContainer width="100%" height="100%">
                      <ComposedChart
                        data={elasticityResult.data_points}
                        margin={{ top: 10, right: 25, bottom: 25, left: 20 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                        <XAxis
                          dataKey="price"
                          name="Realized Price"
                          unit="$"
                          tick={{ fontSize: 11, fill: '#64748b' }}
                          tickFormatter={(val) => `$${Number(val).toFixed(2)}`}
                          label={{
                            value: 'Volume-Weighted Realized Price ($ / Unit)',
                            position: 'insideBottom',
                            offset: -15,
                            style: { fontSize: 11, fill: '#64748b', fontWeight: 600 }
                          }}
                        />
                        <YAxis
                          dataKey="quantity"
                          name="Daily Units"
                          tick={{ fontSize: 11, fill: '#64748b' }}
                          tickLine={false}
                          axisLine={false}
                          label={{
                            value: 'Daily Quantity Sold (Units)',
                            angle: -90,
                            position: 'insideLeft',
                            offset: -5,
                            style: { fontSize: 11, fill: '#64748b', fontWeight: 600 }
                          }}
                        />
                        <Tooltip
                          content={({ active, payload }) => {
                            if (!active || !payload || !payload.length) return null;
                            const point = payload[0].payload;
                            return (
                              <div className="bg-white p-3 border border-slate-200 rounded-lg shadow-md text-xs space-y-1.5">
                                <div className="font-bold text-slate-800 border-b border-slate-100 pb-1 flex justify-between gap-4">
                                  <span>Price: ${Number(point.price).toFixed(2)}</span>
                                  <span className="text-slate-400 font-normal">{point.date}</span>
                                </div>
                                <div className="flex items-center justify-between gap-4">
                                  <span className="text-indigo-600 font-medium">Empirical Sales:</span>
                                  <span className="font-mono font-bold text-slate-800">{point.quantity} units</span>
                                </div>
                                <div className="flex items-center justify-between gap-4">
                                  <span className="text-blue-600 font-medium">Fitted Demand (OLS):</span>
                                  <span className="font-mono font-bold text-slate-800">{point.predicted_quantity} units</span>
                                </div>
                                {point.ci_lower_quantity !== undefined && point.ci_upper_quantity !== undefined && (
                                  <div className="flex items-center justify-between gap-4 text-slate-500 pt-1 border-t border-slate-100">
                                    <span>95% Expected CI:</span>
                                    <span className="font-mono text-slate-700">[{point.ci_lower_quantity}, {point.ci_upper_quantity}]</span>
                                  </div>
                                )}
                              </div>
                            );
                          }}
                        />
                        <Area
                          type="monotone"
                          dataKey="ci_range"
                          name="95% Confidence Band"
                          fill="#dbeafe"
                          fillOpacity={0.45}
                          stroke="#93c5fd"
                          strokeDasharray="3 3"
                        />
                        <Line
                          type="monotone"
                          dataKey="predicted_quantity"
                          name="Fitted Curve"
                          stroke="#2563eb"
                          strokeWidth={2.5}
                          dot={false}
                        />
                        <Scatter
                          name="Empirical Sales"
                          dataKey="quantity"
                          fill="#4338ca"
                          stroke="#ffffff"
                          strokeWidth={1.5}
                          r={5}
                        />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            ) : isInsufficient ? (
              <div className="mt-6 p-6 rounded-xl bg-amber-50/70 border border-amber-200 text-center">
                <AlertTriangle className="w-10 h-10 text-amber-600 mx-auto mb-2" />
                <h4 className="text-sm font-bold text-amber-900">
                  Insufficient Data for Statistical Regression
                </h4>
                <p className="text-xs text-amber-800 max-w-lg mx-auto mt-1 mb-4 leading-relaxed">
                  {elasticityResult.warning_message}
                </p>
                <div className="inline-block bg-white px-4 py-2 rounded-lg border border-amber-200 text-xs font-mono text-slate-700">
                  Current Samples: {elasticityResult.sample_size} / 8 required
                </div>
              </div>
            ) : isNoVariance ? (
              <div className="mt-6 p-6 rounded-xl bg-slate-100 border border-slate-200 text-center">
                <Info className="w-10 h-10 text-slate-500 mx-auto mb-2" />
                <h4 className="text-sm font-bold text-slate-800">
                  Zero Historical Price Variation
                </h4>
                <p className="text-xs text-slate-600 max-w-lg mx-auto mt-1 mb-4 leading-relaxed">
                  {elasticityResult.warning_message}
                </p>
                <div className="inline-block bg-white px-4 py-2 rounded-lg border border-slate-200 text-xs font-mono text-slate-700">
                  Observed Price Range: ${elasticityResult.price_min?.toFixed(2)} - ${elasticityResult.price_max?.toFixed(2)} (Std Dev = 0.00)
                </div>
              </div>
            ) : null}

            {/* Methodology Note */}
            <div className="mt-6 pt-4 border-t border-slate-100 text-[11px] text-slate-400 flex items-start gap-2">
              <Info className="w-3.5 h-3.5 shrink-0 mt-0.5 text-slate-400" />
              <span>{elasticityResult.methodology_note}</span>
            </div>
          </div>

          {/* Catalog Elasticity Overview Table */}
          <div className="card-enterprise p-5 bg-white">
            <h3 className="text-sm font-bold text-slate-900 tracking-tight mb-3">
              Full Catalog Elasticity Directory
            </h3>

            <div className="overflow-x-auto max-h-72">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-400 font-semibold uppercase sticky top-0">
                  <tr>
                    <th className="py-2.5 px-3">SKU</th>
                    <th className="py-2.5 px-3">Product Name</th>
                    <th className="py-2.5 px-3">Category</th>
                    <th className="py-2.5 px-3 text-center">Status</th>
                    <th className="py-2.5 px-3 text-right">Elasticity (β)</th>
                    <th className="py-2.5 px-3 text-center">Demand Type</th>
                    <th className="py-2.5 px-3 text-center">Obs (Days / Prices)</th>
                    <th className="py-2.5 px-3 text-right">R²</th>
                    <th className="py-2.5 px-3 text-right">p-value</th>
                    <th className="py-2.5 px-3 text-center">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-medium">
                  {catalogOverview.map((item) => (
                    <tr
                      key={item.product_id}
                      className={`hover:bg-slate-50/80 transition-colors ${
                        item.product_id === selectedProductId ? 'bg-indigo-50/50' : ''
                      }`}
                    >
                      <td className="py-2 px-3 font-mono font-semibold text-slate-800">
                        {item.sku}
                      </td>
                      <td className="py-2 px-3 text-slate-900">{item.product_name}</td>
                      <td className="py-2 px-3 text-slate-500">{item.category}</td>
                      <td className="py-2 px-3 text-center">
                        <Badge label={item.status} variant={item.status} size="xs" />
                      </td>
                      <td className="py-2 px-3 text-right font-mono font-semibold text-brand-700">
                        {item.elasticity !== null ? item.elasticity.toFixed(2) : '—'}
                      </td>
                      <td className="py-2 px-3 text-center">
                        {item.interpretation ? (
                          <Badge label={item.interpretation} variant={item.interpretation} size="xs" />
                        ) : (
                          '—'
                        )}
                      </td>
                      <td className="py-2 px-3 text-center font-mono text-slate-600">
                        {item.sample_size ? `${item.sample_size}d / ${item.unique_price_points ?? '—'}p` : '—'}
                      </td>
                      <td className="py-2 px-3 text-right font-mono text-slate-600">
                        {item.r_squared !== null ? item.r_squared.toFixed(2) : '—'}
                      </td>
                      <td className="py-2 px-3 text-right font-mono text-slate-600">
                        {formatPValue(item.p_value, item.p_value_display)}
                      </td>
                      <td className="py-2 px-3 text-center">
                        <button
                          onClick={() => setSelectedProductId(item.product_id)}
                          className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 hover:bg-brand-50 hover:text-brand-700 text-slate-700"
                        >
                          Select
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
