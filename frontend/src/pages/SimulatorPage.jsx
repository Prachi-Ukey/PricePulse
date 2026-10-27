import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Sliders,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  HelpCircle,
  DollarSign,
  Package,
  Percent,
  CheckCircle2,
  RefreshCw
} from 'lucide-react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';
import { runSimulator, getSimulatorDefaults, getProducts } from '../api/client';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorState from '../components/common/ErrorState';

export default function SimulatorPage() {
  const [searchParams] = useSearchParams();

  // Catalog products for pre-filling
  const [productsList, setProductsList] = useState([]);
  const [selectedProductId, setSelectedProductId] = useState('');
  const [productMeta, setProductMeta] = useState(null);

  // Simulator Inputs
  const [baselinePrice, setBaselinePrice] = useState(50.0);
  const [baselineVolume, setBaselineVolume] = useState(1000);
  const [baselineCogs, setBaselineCogs] = useState(25.0);
  const [elasticity, setElasticity] = useState(-1.2);
  const [priceChangePct, setPriceChangePct] = useState(-10.0);
  const [costChangePct, setCostChangePct] = useState(0.0);

  // Elasticity Metadata & Provenance
  const [isEstimated, setIsEstimated] = useState(false);
  const [elasticitySource, setElasticitySource] = useState('benchmark_default');
  const [elasticityStatus, setElasticityStatus] = useState(null);
  const [elasticityMessage, setElasticityMessage] = useState(null);

  // Simulation output
  const [simulationResult, setSimulationResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load catalog on mount
  useEffect(() => {
    getProducts({ page: 1, page_size: 100 })
      .then((data) => {
        setProductsList(data.items || []);
        const urlId = searchParams.get('product_id');
        const rawUrlElas = searchParams.get('elasticity');
        let validUrlElas = null;
        if (rawUrlElas !== null && rawUrlElas !== '') {
          const parsed = Number(rawUrlElas);
          if (Number.isFinite(parsed) && parsed < 0) {
            validUrlElas = parsed;
          }
        }
        if (urlId) {
          setSelectedProductId(urlId);
          loadProductDefaults(Number(urlId), validUrlElas);
        } else if (data.items?.length) {
          // Default to first product
          setSelectedProductId(String(data.items[0].id));
          loadProductDefaults(data.items[0].id, validUrlElas);
        }
      })
      .catch((err) => console.error(err));
  }, []);

  const loadProductDefaults = async (productId, requestedUrlElas = null) => {
    try {
      const defs = await getSimulatorDefaults(productId);
      setProductMeta(defs);
      setBaselinePrice(defs.baseline_price);
      setBaselineVolume(defs.baseline_volume);
      setBaselineCogs(defs.baseline_cogs);

      if (requestedUrlElas !== null && Number.isFinite(requestedUrlElas) && requestedUrlElas < 0) {
        setElasticity(requestedUrlElas);
        // A query parameter only confers empirical mode if product is actually estimated and matches coefficient
        if (defs.is_estimated && defs.estimated_elasticity != null && Math.abs(defs.estimated_elasticity - requestedUrlElas) < 0.01) {
          setIsEstimated(true);
          setElasticitySource('empirical_estimate');
        } else {
          setIsEstimated(false);
          setElasticitySource('manual');
          setElasticityMessage(`Custom scenario: Using parameter β = ${requestedUrlElas.toFixed(2)} (exploratory assumption).`);
        }
      } else if (defs.is_estimated && defs.estimated_elasticity != null && defs.estimated_elasticity < 0) {
        setElasticity(defs.estimated_elasticity);
        setIsEstimated(true);
        setElasticitySource('empirical_estimate');
      } else {
        const fallback = defs.default_elasticity ?? defs.fallback_elasticity ?? -1.2;
        setElasticity(fallback);
        setIsEstimated(false);
        setElasticitySource('benchmark_default');
      }
      setElasticityStatus(defs.elasticity_status || null);
      if (requestedUrlElas === null || (defs.is_estimated && Math.abs((defs.estimated_elasticity ?? 0) - requestedUrlElas) < 0.01)) {
        setElasticityMessage(defs.elasticity_message || null);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleProductSelect = (e) => {
    const val = e.target.value;
    setSelectedProductId(val);
    if (val) {
      loadProductDefaults(Number(val));
    } else {
      setProductMeta(null);
      setIsEstimated(false);
      setElasticitySource('benchmark_default');
      setElasticityMessage('Custom scenario: Using benchmark assumption (β = -1.20).');
    }
  };

  const handleElasticitySliderChange = (newVal) => {
    setElasticity(newVal);
    if (productMeta?.is_estimated && newVal === productMeta.estimated_elasticity) {
      setIsEstimated(true);
      setElasticitySource('empirical_estimate');
    } else if (!productMeta?.is_estimated && newVal === (productMeta?.fallback_elasticity ?? -1.2)) {
      setIsEstimated(false);
      setElasticitySource('benchmark_default');
    } else {
      setIsEstimated(false);
      setElasticitySource('manual');
    }
  };

  // Re-run simulation when inputs change
  const executeSimulation = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        baseline_price: Number(baselinePrice),
        baseline_volume: Number(baselineVolume),
        baseline_cogs: Number(baselineCogs),
        elasticity: Number(elasticity),
        price_change_pct: Number(priceChangePct),
        elasticity_source: Number(elasticity) >= 0 ? (elasticitySource === 'benchmark_default' ? 'benchmark_default' : 'manual') : elasticitySource,
        is_estimated: isEstimated && elasticitySource === 'empirical_estimate' && Number(elasticity) < 0,
        product_id: selectedProductId ? Number(selectedProductId) : null,
      };
      const res = await runSimulator(payload);
      setSimulationResult(res);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Simulation execution failed.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (baselinePrice > 0 && baselineVolume > 0) {
      executeSimulation();
    }
  }, [baselinePrice, baselineVolume, baselineCogs, elasticity, priceChangePct, costChangePct, elasticitySource, isEstimated]);

  return (
    <div className="space-y-6">
      {/* Header & Product Preset Selector */}
      <div className="card-enterprise p-4 bg-white flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2.5">
          <Sliders className="w-5 h-5 text-brand-600" />
          <div>
            <h2 className="text-sm font-bold text-slate-900 leading-none">
              What-If Pricing & Margin Simulator
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Model price alterations, demand sensitivity response, unit contribution, and profit break-evens
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <label htmlFor="product-defaults-select" className="font-semibold text-slate-600">Pre-fill SKU:</label>
          <select
            id="product-defaults-select"
            value={selectedProductId}
            onChange={handleProductSelect}
            className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 font-medium text-slate-800 max-w-xs truncate focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option value="">-- Custom Scenario --</option>
            {productsList.map((p) => (
              <option key={p.id} value={p.id}>
                {p.sku} — {p.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Simulator Inputs Card */}
      <div className="card-enterprise p-5 bg-white">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4 pb-2 border-b border-slate-100">
          Simulation Parameters & Model Inputs
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Column 1: Financial Baselines */}
          <div className="space-y-3">
            <span className="text-xs font-semibold text-slate-800 block">Baseline Financials</span>
            <div>
              <label htmlFor="baseline-price-input" className="text-[11px] text-slate-500 font-medium">Baseline Realized Price ($)</label>
              <input
                id="baseline-price-input"
                type="number"
                step="0.01"
                min="0.10"
                value={baselinePrice}
                onChange={(e) => setBaselinePrice(Number(e.target.value))}
                className="w-full mt-1 px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg font-mono font-semibold"
              />
            </div>
            <div>
              <label htmlFor="baseline-volume-input" className="text-[11px] text-slate-500 font-medium">Baseline Volume (Units)</label>
              <input
                id="baseline-volume-input"
                type="number"
                min="1"
                value={baselineVolume}
                onChange={(e) => setBaselineVolume(Number(e.target.value))}
                className="w-full mt-1 px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg font-mono font-semibold"
              />
            </div>
            <div>
              <label htmlFor="baseline-cogs-input" className="text-[11px] text-slate-500 font-medium">Baseline Unit COGS ($)</label>
              <input
                id="baseline-cogs-input"
                type="number"
                step="0.01"
                min="0"
                value={baselineCogs}
                onChange={(e) => setBaselineCogs(Number(e.target.value))}
                className="w-full mt-1 px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg font-mono font-semibold"
              />
            </div>
          </div>

          {/* Column 2: Price Change Slider */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <label htmlFor="price-change-range" className="text-xs font-semibold text-slate-800">Proposed Price Adjustment</label>
              <span
                className={`font-mono text-xs font-bold px-2 py-0.5 rounded ${
                  priceChangePct > 0
                    ? 'bg-emerald-50 text-emerald-700'
                    : priceChangePct < 0
                    ? 'bg-indigo-50 text-indigo-700'
                    : 'bg-slate-100 text-slate-700'
                }`}
              >
                {priceChangePct > 0 ? `+${priceChangePct}%` : `${priceChangePct}%`}
              </span>
            </div>

            <input
              id="price-change-range"
              type="range"
              min="-40"
              max="40"
              step="1"
              value={priceChangePct}
              onChange={(e) => setPriceChangePct(Number(e.target.value))}
              className="w-full accent-brand-600 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-400 font-mono">
              <span>-40% Discount</span>
              <span>0% Baseline</span>
              <span>+40% Hike</span>
            </div>

            <div className="pt-2">
              <div className="flex items-center justify-between mb-1">
                <label htmlFor="cost-change-range" className="text-xs font-semibold text-slate-700">COGS Inflation / Shift (%)</label>
                <span className="font-mono text-xs text-slate-600 font-medium">{costChangePct}%</span>
              </div>
              <input
                id="cost-change-range"
                type="range"
                min="-20"
                max="20"
                step="1"
                value={costChangePct}
                onChange={(e) => setCostChangePct(Number(e.target.value))}
                className="w-full accent-slate-600 cursor-pointer"
              />
            </div>
          </div>

          {/* Column 3: Elasticity Parameter Slider */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label htmlFor="elasticity-range" className="text-xs font-semibold text-slate-800">
                Price Elasticity (β)
              </label>
              <div className="flex items-center gap-1.5">
                {elasticitySource === 'empirical_estimate' ? (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                    Empirical Estimate
                  </span>
                ) : elasticitySource === 'benchmark_default' ? (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200">
                    Benchmark Assumption
                  </span>
                ) : (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                    Custom Parameter
                  </span>
                )}
                <span className="font-mono text-xs font-bold text-brand-700 bg-brand-50 px-2 py-0.5 rounded border border-brand-200">
                  β = {elasticity.toFixed(2)}
                </span>
              </div>
            </div>

            <input
              id="elasticity-range"
              type="range"
              min="-3.0"
              max="-0.1"
              step="0.05"
              value={elasticity}
              onChange={(e) => handleElasticitySliderChange(Number(e.target.value))}
              className="w-full accent-brand-600 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-400 font-mono">
              <span>-3.0 (Highly Elastic)</span>
              <span>-1.0 (Unitary)</span>
              <span>-0.1 (Inelastic)</span>
            </div>

            {/* Benchmark vs Empirical Callout */}
            {elasticitySource === 'benchmark_default' && (
              <div className="p-2.5 rounded-lg bg-amber-50/80 border border-amber-200 text-[11px] text-amber-900 leading-tight space-y-1">
                <div className="flex items-center gap-1.5 font-semibold text-amber-800">
                  <AlertCircle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                  <span>Benchmark Assumption (Unestimated SKU)</span>
                </div>
                <p className="text-amber-700">
                  {elasticityMessage || 'Historical sales data is insufficient or static for this product. Projections use an exploratory benchmark default (β = -1.20), NOT an empirical demand forecast.'}
                </p>
              </div>
            )}

            {elasticitySource === 'empirical_estimate' && (
              <div className="p-2.5 rounded-lg bg-emerald-50/80 border border-emerald-200 text-[11px] text-emerald-900 leading-tight space-y-1">
                <div className="flex items-center gap-1.5 font-semibold text-emerald-800">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  <span>Empirically Estimated Parameter</span>
                </div>
                <p className="text-emerald-700">
                  {elasticityMessage || `Modeled from observed historical sales transactions (β = ${elasticity.toFixed(2)}). Observational estimates reflect correlational sensitivity.`}
                </p>
              </div>
            )}

            {elasticitySource === 'manual' && (
              <div className="p-2 rounded-lg bg-slate-50 border border-slate-200 text-[11px] text-slate-600 leading-tight">
                <span className="font-semibold text-slate-700">Custom Sensitivity: </span>
                User-adjusted elasticity parameter for exploratory what-if scenario testing.
              </div>
            )}

            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-[11px] text-slate-600 leading-tight">
              {elasticity < -1.1
                ? 'Elastic Demand (β < -1.1): Price cuts generate disproportionate volume increases.'
                : elasticity >= 0.0
                ? 'Anomalous Elasticity — Review Required (β ≥ 0.0): Positive or zero slope in observational data may reflect promotions, seasonality, mix shifts, or noise; review required.'
                : elasticity > -0.9
                ? 'Inelastic Demand (-0.9 < β < 0.0): Volume is insensitive; price increases expand net margin.'
                : 'Unitary Elasticity (-1.1 ≤ β ≤ -0.9): Volume shifts proportionally to price changes.'}
            </div>
          </div>
        </div>
      </div>

      {/* Scenario Comparison Grid */}
      {simulationResult && (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          {/* 1. Baseline */}
          <div className="card-enterprise p-5 bg-white border-slate-300">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
              {simulationResult.baseline.label}
            </span>
            <div className="mt-2 space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-slate-500">Price:</span>
                <span className="font-mono font-semibold">${simulationResult.baseline.price.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-500">Volume:</span>
                <span className="font-mono font-semibold">{simulationResult.baseline.volume.toLocaleString()} units</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-500">Revenue:</span>
                <span className="font-mono font-semibold">${simulationResult.baseline.revenue.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-500">Gross Profit:</span>
                <span className="font-mono font-semibold text-emerald-600">
                  ${simulationResult.baseline.gross_profit.toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between text-xs pt-1 border-t border-slate-100">
                <span className="text-slate-500 font-semibold">Gross Margin:</span>
                <span className="font-mono font-bold text-slate-900">
                  {(simulationResult.baseline.gross_margin * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>

          {/* 2. Proposed Strategy (Hero Card) */}
          <div className="card-enterprise p-5 bg-indigo-50/40 border-brand-300 ring-2 ring-brand-500/20 shadow-md">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase tracking-wider text-brand-700">
                {simulationResult.proposed.label}
              </span>
              <div className="flex items-center gap-1.5">
                {simulationResult.is_estimated ? (
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-600 text-white">
                    Empirical Model
                  </span>
                ) : simulationResult.elasticity_source === 'benchmark_default' ? (
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-600 text-white">
                    Benchmark Assumption
                  </span>
                ) : (
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-brand-600 text-white">
                    Scenario Modeled
                  </span>
                )}
              </div>
            </div>
            <div className="mt-2 space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-slate-600">Projected Price:</span>
                <span className="font-mono font-bold text-slate-900">
                  ${simulationResult.proposed.price.toFixed(2)} ({simulationResult.proposed.price_change_pct > 0 ? `+${simulationResult.proposed.price_change_pct}%` : `${simulationResult.proposed.price_change_pct}%`})
                </span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-600">Projected Units:</span>
                <span className="font-mono font-bold text-slate-900">
                  {simulationResult.proposed.volume.toLocaleString()} ({simulationResult.proposed.volume_change_pct > 0 ? `+${simulationResult.proposed.volume_change_pct}%` : `${simulationResult.proposed.volume_change_pct}%`})
                </span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-600">Projected Revenue:</span>
                <span className="font-mono font-bold text-slate-900">
                  ${simulationResult.proposed.revenue.toLocaleString()} ({simulationResult.proposed.revenue_change_pct > 0 ? `+${simulationResult.proposed.revenue_change_pct}%` : `${simulationResult.proposed.revenue_change_pct}%`})
                </span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-600 font-semibold">Gross Profit:</span>
                <span
                  className={`font-mono font-bold ${
                    simulationResult.proposed.gross_profit >= simulationResult.baseline.gross_profit
                      ? 'text-emerald-700'
                      : 'text-rose-700'
                  }`}
                >
                  ${simulationResult.proposed.gross_profit.toLocaleString()} ({simulationResult.proposed.gross_profit_change_pct > 0 ? `+${simulationResult.proposed.gross_profit_change_pct}%` : `${simulationResult.proposed.gross_profit_change_pct}%`})
                </span>
              </div>
              <div className="flex justify-between text-xs pt-1 border-t border-brand-200">
                <span className="text-brand-900 font-semibold">Gross Margin:</span>
                <span className="font-mono font-bold text-brand-900">
                  {(simulationResult.proposed.gross_margin * 100).toFixed(1)}% ({simulationResult.proposed.gross_margin_change_pct > 0 ? `+${simulationResult.proposed.gross_margin_change_pct} pts` : `${simulationResult.proposed.gross_margin_change_pct} pts`})
                </span>
              </div>
            </div>
          </div>

          {/* 3. Alternative Lower */}
          <div className="card-enterprise p-5 bg-white border-slate-200">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
              {simulationResult.alternative_lower.label}
            </span>
            <div className="mt-2 space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500">Price:</span>
                <span className="font-mono font-semibold">${simulationResult.alternative_lower.price.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Volume:</span>
                <span className="font-mono font-semibold">{simulationResult.alternative_lower.volume.toLocaleString()} units</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Revenue:</span>
                <span className="font-mono font-semibold">${simulationResult.alternative_lower.revenue.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Profit:</span>
                <span className="font-mono font-semibold">${simulationResult.alternative_lower.gross_profit.toLocaleString()}</span>
              </div>
              <div className="flex justify-between pt-1 border-t border-slate-100">
                <span className="text-slate-500 font-semibold">Margin:</span>
                <span className="font-mono font-bold">{(simulationResult.alternative_lower.gross_margin * 100).toFixed(1)}%</span>
              </div>
            </div>
          </div>

          {/* 4. Alternative Higher */}
          <div className="card-enterprise p-5 bg-white border-slate-200">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
              {simulationResult.alternative_higher.label}
            </span>
            <div className="mt-2 space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500">Price:</span>
                <span className="font-mono font-semibold">${simulationResult.alternative_higher.price.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Volume:</span>
                <span className="font-mono font-semibold">{simulationResult.alternative_higher.volume.toLocaleString()} units</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Revenue:</span>
                <span className="font-mono font-semibold">${simulationResult.alternative_higher.revenue.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Profit:</span>
                <span className="font-mono font-semibold text-emerald-600">${simulationResult.alternative_higher.gross_profit.toLocaleString()}</span>
              </div>
              <div className="flex justify-between pt-1 border-t border-slate-100">
                <span className="text-slate-500 font-semibold">Margin:</span>
                <span className="font-mono font-bold">{(simulationResult.alternative_higher.gross_margin * 100).toFixed(1)}%</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Break-Even Volume Analysis Card */}
      {simulationResult && (
        <div className="card-enterprise p-5 bg-white">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-4 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-brand-600" />
                Profit Break-Even Volume Requirement
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Calculates the precise unit sales expansion required to maintain baseline gross profit dollars ($
                {simulationResult.baseline.gross_profit.toLocaleString()}).
              </p>
            </div>

            <div className="flex items-center gap-4 text-xs font-mono">
              <div className="bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200">
                <span className="text-slate-400 block text-[10px] uppercase font-sans">Unit Contribution (Baseline)</span>
                <span className="font-bold text-slate-800">${simulationResult.unit_contribution_baseline.toFixed(2)} / unit</span>
              </div>
              <div className="bg-indigo-50 px-3 py-1.5 rounded-lg border border-indigo-200">
                <span className="text-brand-700 block text-[10px] uppercase font-sans font-bold">Unit Contribution (Proposed)</span>
                <span className="font-bold text-brand-900">${simulationResult.unit_contribution_proposed.toFixed(2)} / unit</span>
              </div>
            </div>
          </div>

          <div className="mt-4 p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-wrap items-center justify-between gap-6">
            <div>
              <span className="text-xs uppercase font-bold text-slate-400">Required Volume Change</span>
              <div className="text-2xl font-bold font-mono text-slate-900 mt-1">
                {simulationResult.break_even_volume_change_pct != null
                  ? (simulationResult.break_even_volume_change_pct > 0
                    ? `+${simulationResult.break_even_volume_change_pct.toFixed(1)}%`
                    : `${simulationResult.break_even_volume_change_pct.toFixed(1)}%`)
                  : 'N/A (Impossible)'}
              </div>
              <div className="text-xs text-slate-500 mt-0.5">
                Target units required:{' '}
                <strong className="font-mono text-slate-800">
                  {simulationResult.break_even_units != null
                    ? simulationResult.break_even_units.toLocaleString()
                    : 'Impossible (≤ $0 CM)'}
                </strong>
              </div>
            </div>

            <div className="max-w-md text-xs text-slate-600 leading-relaxed">
              {simulationResult.unit_contribution_proposed <= 0 ? (
                <div className="flex items-start gap-2 text-rose-800 bg-rose-50 p-3 rounded-lg border border-rose-200">
                  <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                  <span>
                    <strong>Break-even impossible:</strong> Proposed unit contribution margin ($
                    {simulationResult.unit_contribution_proposed.toFixed(2)}) is zero or negative. Additional unit volume
                    will only expand cumulative losses rather than recover baseline gross profit.
                  </span>
                </div>
              ) : simulationResult.break_even_units != null &&
                simulationResult.proposed.volume >= simulationResult.break_even_units ? (
                <div className="flex items-start gap-2 text-emerald-800 bg-emerald-50 p-3 rounded-lg border border-emerald-200">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span>
                    <strong>Break-even satisfied:</strong> Elasticity-modeled volume (
                    {simulationResult.proposed.volume.toLocaleString()} units) exceeds the required threshold (
                    {simulationResult.break_even_units.toLocaleString()} units), expanding total gross profit.
                  </span>
                </div>
              ) : (
                <div className="flex items-start gap-2 text-rose-800 bg-rose-50 p-3 rounded-lg border border-rose-200">
                  <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                  <span>
                    <strong>Profit shortfall warning:</strong> Elasticity-modeled volume (
                    {simulationResult.proposed.volume.toLocaleString()} units) falls short of the{' '}
                    {simulationResult.break_even_units != null
                      ? `${simulationResult.break_even_units.toLocaleString()} units`
                      : 'required volume'}{' '}
                    needed to offset the price reduction.
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Sensitivity Curve Chart */}
      {simulationResult && (
        <div className="card-enterprise p-5 bg-white">
          <div className="pb-3 mb-4 border-b border-slate-100 flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900 tracking-tight">
              Sensitivity Curve Across Price Adjustments (-30% to +30%)
            </h3>
            <span className="text-xs text-slate-400">Projected Revenue & Profit Curves</span>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={simulationResult.curve} margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis
                  dataKey="price_change_pct"
                  tick={{ fontSize: 11, fill: '#64748b' }}
                  tickFormatter={(val) => `${val > 0 ? `+${val}` : val}%`}
                />
                <YAxis
                  yAxisId="left"
                  tick={{ fontSize: 11, fill: '#64748b' }}
                  tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  formatter={(val, name) => [`$${Number(val).toLocaleString()}`, name]}
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    borderColor: '#e2e8f0',
                    borderRadius: '0.5rem',
                    fontSize: '12px',
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="projected_revenue"
                  name="Projected Revenue"
                  stroke="#6366f1"
                  strokeWidth={2}
                  dot={{ r: 2 }}
                />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="projected_profit"
                  name="Projected Profit"
                  stroke="#10b981"
                  strokeWidth={2.5}
                  dot={{ r: 3 }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* Assumptions & Disclaimer */}
          <div className="mt-5 pt-4 border-t border-slate-100 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-500">
            <div>
              <span className="font-semibold text-slate-700 block mb-1">Model Assumptions:</span>
              <ul className="list-disc pl-4 space-y-0.5 text-[11px]">
                {simulationResult.assumptions.map((a, idx) => (
                  <li key={idx}>{a}</li>
                ))}
              </ul>
            </div>
            <div>
              <span className="font-semibold text-amber-700 block mb-1">Limitation Notice:</span>
              <p className="text-[11px] text-slate-500 leading-relaxed">
                {simulationResult.disclaimer}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
