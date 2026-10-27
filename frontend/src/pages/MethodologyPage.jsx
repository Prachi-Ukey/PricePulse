import React from 'react';
import { BookOpen, ShieldCheck, AlertCircle, Info, Calculator, FileCheck, HelpCircle, Layers } from 'lucide-react';

export default function MethodologyPage() {
  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Title */}
      <div className="card-enterprise p-6 bg-white">
        <div className="flex items-center gap-3 pb-4 border-b border-slate-100">
          <div className="p-2.5 rounded-lg bg-brand-50 text-brand-600">
            <BookOpen className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900 tracking-tight">
              Analytical Methodology, Econometric Specifications & Mathematical Formulations
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Exact definitions, accounting identities, log-log OLS regressions, data sufficiency gates, and causal limitations.
            </p>
          </div>
        </div>

        {/* Synthetic Dataset Transparency Box */}
        <div className="mt-5 p-4 rounded-xl bg-amber-50/80 border border-amber-200/90 text-xs text-amber-950 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            <strong className="font-bold text-amber-900 block mb-0.5">
              Synthetic Data Transparency Notice
            </strong>
            The default dataset pre-loaded in this platform consists of <strong>100 products</strong> and exactly{' '}
            <strong>4,948 sales transaction records (sales lines)</strong> across 14 months, generated
            deterministically for testing, benchmarking, and econometric algorithm validation. PricePulse never
            misrepresents fabricated or synthetic numbers as actual company financials. User-uploaded CSV datasets
            are flagged and managed separately from synthetic seed records.
          </div>
        </div>
      </div>

      {/* Section 1: Core Financial Formulations */}
      <div className="card-enterprise p-6 bg-white space-y-4">
        <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <Calculator className="w-4 h-4 text-brand-600" />
          1. Core Accounting & Pricing Formulas
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-1.5">
            <span className="font-bold text-slate-900 block">Actual Realized Selling Price (ASP)</span>
            <div className="font-mono text-brand-700 bg-white p-2 rounded border border-slate-200 text-center font-bold">
              ASP = UnitPrice · (1 - DiscountPct / 100)
            </div>
            <p className="text-slate-500 text-[11px] leading-relaxed">
              Price realized at transaction time after deducting promotional or contract discounts.
              Clamped within boundary conditions: DiscountPct ∈ [0, 100]%, UnitPrice ≥ 0.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-1.5">
            <span className="font-bold text-slate-900 block">Realized Revenue</span>
            <div className="font-mono text-brand-700 bg-white p-2 rounded border border-slate-200 text-center font-bold">
              Revenue = Quantity · ASP
            </div>
            <p className="text-slate-500 text-[11px] leading-relaxed">
              Gross dollar inflow derived strictly from unit volume multiplied by actual discounted selling price.
              Quantity ≥ 0, ASP ≥ 0.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-1.5">
            <span className="font-bold text-slate-900 block">Gross Profit (COGS Match)</span>
            <div className="font-mono text-brand-700 bg-white p-2 rounded border border-slate-200 text-center font-bold">
              GrossProfit = Revenue - (Quantity · COGS)
            </div>
            <p className="text-slate-500 text-[11px] leading-relaxed">
              Computed exclusively where valid unit cost data exists. Returns null if COGS is missing.
              Allows negative values when items are sold at a loss below unit cost. Excludes overhead and opex.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-1.5">
            <span className="font-bold text-slate-900 block">Gross Margin %</span>
            <div className="font-mono text-brand-700 bg-white p-2 rounded border border-slate-200 text-center font-bold">
              GrossMargin = GrossProfit / Revenue (if Revenue &gt; 0)
            </div>
            <p className="text-slate-500 text-[11px] leading-relaxed">
              Ratio of gross profit dollars to realized revenue. Safely clamped to 0.0 when revenue is zero to prevent division-by-zero.
              Returns negative percentage when sold below unit cost.
            </p>
          </div>
        </div>

        {/* Portfolio Aggregation Sub-card */}
        <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 text-xs space-y-2">
          <span className="font-bold text-slate-900 block">Portfolio Aggregated Metrics & COGS Treatment</span>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-[11px]">
            <div className="bg-white p-2.5 rounded border border-slate-200">
              <strong className="block text-slate-700 mb-0.5">Weighted Catalog ASP:</strong>
              <div className="font-mono text-brand-700 text-center my-1 font-bold">ASP<sub>weighted</sub> = Σ(Rev) / Σ(Qty)</div>
              <span className="text-slate-500">Volume-weighted average realized price across transactions.</span>
            </div>
            <div className="bg-white p-2.5 rounded border border-slate-200">
              <strong className="block text-slate-700 mb-0.5">Portfolio Gross Margin:</strong>
              <div className="font-mono text-brand-700 text-center my-1 font-bold">Margin = Σ(GrossProfit) / Σ(EligibleRev)</div>
              <span className="text-slate-500">
                CRITICAL INTEGRITY RULE: Revenue from records lacking valid COGS is strictly excluded from
                <strong> both the numerator (GrossProfit) and denominator (EligibleRev)</strong> to prevent artificial margin dilution.
              </span>
            </div>
            <div className="bg-white p-2.5 rounded border border-slate-200">
              <strong className="block text-slate-700 mb-0.5">Average Discount %:</strong>
              <div className="font-mono text-brand-700 text-center my-1 font-bold">Disc% = Σ(Qty·(P<sub>list</sub>-ASP)) / Σ(Qty·P<sub>list</sub>)</div>
              <span className="text-slate-500">List-value-weighted promotional discount percentage across portfolio.</span>
            </div>
            <div className="bg-white p-2.5 rounded border border-slate-200">
              <strong className="block text-slate-700 mb-0.5">Price Variance vs. MSRP:</strong>
              <div className="font-mono text-brand-700 text-center my-1 font-bold">Var% = ((ASP - MSRP) / MSRP) · 100</div>
              <span className="text-slate-500">
                Measures realized ASP relative to catalog MSRP. When ASP &gt; MSRP (Var% &gt; 0), the product realizes a <strong>Net Price Premium</strong>, clearly distinguished from promotional line discounts.
              </span>
            </div>
          </div>
        </div>

        {/* CSV Import Contracts & Metadata Conflict Safeguards */}
        <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 text-xs space-y-2">
          <span className="font-bold text-slate-900 block">CSV Import Contracts & Metadata Integrity Safeguards</span>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-[11px] leading-relaxed">
            <div className="bg-white p-3 rounded border border-slate-200 space-y-1">
              <strong className="text-slate-800 block font-semibold">1. List Price Mode (Default — MSRP Contract):</strong>
              <p className="text-slate-600">
                CSV <code>unit_price</code> represents pre-discount catalog list price (P<sub>list</sub>). Realized selling price is derived as:
              </p>
              <div className="font-mono text-brand-700 bg-slate-50 p-1.5 rounded text-center">
                ASP = UnitPrice · (1 - DiscountPct / 100), &emsp; Revenue = Quantity · ASP
              </div>
              <p className="text-slate-500 text-[10px]">
                Applied when source files record catalog list prices alongside separate discount percentages.
              </p>
            </div>

            <div className="bg-white p-3 rounded border border-slate-200 space-y-1">
              <strong className="text-slate-800 block font-semibold">2. Net Selling Price Mode (ASP Contract — No Double-Discounting):</strong>
              <p className="text-slate-600">
                CSV <code>unit_price</code> represents the realized net selling price (ASP). Realized revenue is computed directly:
              </p>
              <div className="font-mono text-brand-700 bg-slate-50 p-1.5 rounded text-center">
                ASP = UnitPrice, &emsp; Revenue = Quantity · UnitPrice
              </div>
              <p className="text-slate-500 text-[10px]">
                Pre-discount list price is reconstructed if discount percentage is supplied: P<sub>list</sub> = ASP / (1 - Disc% / 100). Prevents double-discounting when POS/ERP data exports post-discount prices.
              </p>
            </div>
          </div>

          <div className="p-3 bg-amber-50/60 border border-amber-200 rounded text-[11px] text-amber-950 space-y-1">
            <strong className="font-semibold block text-amber-900">Trusted Catalog Metadata Safeguard (Conflict Policy):</strong>
            <p>
              Existing product catalog names and categories are trusted primary master records. When importing transactions for an existing SKU, any conflicting product name or category is <strong>never silently overwritten or ignored</strong>. Conflicting rows are flagged as row-level validation errors and rejected during pre-validation to prevent catalog corruption.
            </p>
          </div>
        </div>
      </div>

      {/* Section 2: Price Elasticity Econometric Model */}
      <div className="card-enterprise p-6 bg-white space-y-4">
        <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-brand-600" />
          2. Price Elasticity of Demand (PED) Econometric Specification
        </h3>

        <div className="text-xs text-slate-700 leading-relaxed space-y-3">
          <p>
            Price elasticity is estimated using a <strong>Log-Log Ordinary Least Squares (OLS)</strong> regression model.
            To eliminate single-basket transaction bias (where individual receipts often capture 1–2 items regardless of price),
            the engine aggregates sales into <strong>product-by-day active sales observations</strong>:
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono text-xs">
            <div className="p-2.5 bg-slate-50 border border-slate-200 rounded text-center">
              <span className="text-slate-500 block text-[10px] uppercase font-sans font-semibold">Total Daily Demand</span>
              <strong className="text-slate-800">Q<sub>d</sub> = Σ Quantity<sub>d,i</sub></strong>
            </div>
            <div className="p-2.5 bg-slate-50 border border-slate-200 rounded text-center">
              <span className="text-slate-500 block text-[10px] uppercase font-sans font-semibold">Volume-Weighted Realized Price</span>
              <strong className="text-slate-800">P<sub>d</sub> = Σ(Quantity<sub>d,i</sub> · Price<sub>d,i</sub>) / Q<sub>d</sub></strong>
            </div>
          </div>

          <div className="p-3 bg-slate-900 text-slate-100 rounded-lg font-mono text-center font-bold text-sm">
            ln(Q<sub>d</sub>) = α + β · ln(P<sub>d</sub>) + ε<sub>d</sub>
          </div>

          <p>
            Because both variables are log-transformed, the slope coefficient <strong>β</strong> equals the constant point elasticity of demand:
          </p>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg font-mono text-center text-xs">
            β = d(ln Q) / d(ln P) = (% Δ Quantity) / (% Δ Price) = SS<sub>xy</sub> / SS<sub>xx</sub>
          </div>

          {/* 4 Mutually Exclusive Elasticity Categories */}
          <span className="font-bold text-slate-900 block pt-1">
            Mutually Exclusive Classification Categories:
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="p-3 rounded-lg border border-indigo-200 bg-indigo-50/50">
              <span className="font-bold text-brand-800 block mb-1">1. Elastic (β &lt; -1.1)</span>
              <p className="text-[11px] text-slate-600">
                |% ΔQ| &gt; |% ΔP|. Demand is highly responsive to price concessions. Price reductions expand revenue if unit contribution covers promotional markdown.
              </p>
            </div>

            <div className="p-3 rounded-lg border border-sky-200 bg-sky-50/50">
              <span className="font-bold text-sky-800 block mb-1">2. Unitary (-1.1 ≤ β ≤ -0.9)</span>
              <p className="text-[11px] text-slate-600">
                |% ΔQ| ≈ |% ΔP|. Demand changes approximately proportionally to price adjustments within empirical tolerance band centered at -1.0.
              </p>
            </div>

            <div className="p-3 rounded-lg border border-emerald-200 bg-emerald-50/50">
              <span className="font-bold text-emerald-800 block mb-1">3. Inelastic (-0.9 &lt; β &lt; 0.0)</span>
              <p className="text-[11px] text-slate-600">
                |% ΔQ| &lt; |% ΔP|. Demand is insensitive to price changes. Selective price hikes expand gross profit without proportional volume loss.
              </p>
            </div>

            <div className="p-3 rounded-lg border border-amber-200 bg-amber-50/50">
              <span className="font-bold text-amber-800 block mb-1">4. Anomalous Elasticity (β ≥ 0.0)</span>
              <p className="text-[11px] text-slate-600">
                β = 0 indicates unresponsive observed demand. β &gt; 0 represents an anomalous positive price–demand relationship in observational data, which may reflect promotions, seasonality, product mix changes, limited price variation, confounding variables, data quality issues, or statistical noise. These are possible explanations, not established causes.
              </p>
            </div>
          </div>
        </div>

        {/* Statistical Hygiene & Sufficient Data Rules */}
        <div className="mt-4 p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-2">
          <span className="font-bold text-slate-900 block">Statistical Validation, Sufficiency Gates & Confidence Bounds</span>
          <ul className="list-disc pl-5 text-slate-600 space-y-1.5 text-[11px] leading-relaxed">
            <li>
              <strong>Observation Unit & Zero-Sales Treatment:</strong> Active product-by-day sales observations form the sample.
              Zero-sales periods are excluded because ln(0) is mathematically undefined in log-log OLS specifications,
              and unobserved off-market reservation prices during non-sale periods cannot be inferred from historical sales logs.
            </li>
            <li>
              <strong>Minimum Sample Threshold (N ≥ 8):</strong> When a product has fewer than 8 distinct daily observations, regression is aborted with status <code className="text-amber-800 font-mono">INSUFFICIENT_DATA</code> to prevent spurious overfitting on underpowered samples.
            </li>
            <li>
              <strong>Price Variance Requirement (StdDev(P) ≥ 0.01, Var(P) ≥ 0.0001, SS<sub>xx</sub> &gt; 10<sup>-12</sup>):</strong> If a product has only sold at static prices without variation, elasticity is flagged as <code className="text-slate-800 font-mono">NO_PRICE_VARIATION</code> because elasticity cannot mathematically be identified without price movement.
            </li>
            <li>
              <strong>Degrees of Freedom & Standard Errors:</strong> With two estimated parameters (intercept α, slope β), residual degrees of freedom are <code>df = N - 2</code>. Residual variance is <code>s² = RSS / (N - 2)</code>. Standard error of slope is <code>SE(β) = √(s² / SS<sub>xx</sub>)</code>.
            </li>
            <li>
              <strong>95% Confidence Intervals:</strong> Derived from the two-tailed Student’s t-distribution: <code>CI = β ± t<sub>0.975, df</sub> · SE(β)</code> where <code>t = β / SE(β)</code> and <code>p = 2 · (1 - F<sub>t</sub>(|t|, df))</code>.
            </li>
            <li>
              <strong>Confidence Interval Boundary Crossover Behavior:</strong> When the 95% CI spans across classification thresholds (-1.1, -0.9, or 0.0), the platform sets <code>ci_crosses_boundary: true</code> and attaches an explicit diagnostic warning. If the CI contains zero (CI<sub>lower</sub> ≤ 0 ≤ CI<sub>upper</sub>), the price effect is not statistically distinguishable from zero at α = 0.05 (p ≥ 0.05).
            </li>
          </ul>
        </div>

        {/* Prominent Observational vs Causal Notice */}
        <div className="p-4 rounded-xl bg-rose-50/70 border border-rose-200 text-xs text-rose-950 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            <strong className="font-bold text-rose-900 block mb-0.5">
              Important Econometric Notice: Observational Elasticity is NOT Causal
            </strong>
            Historical price elasticity estimates computed by PricePulse reflect observational correlations in transaction data,
            <strong>not guaranteed causal demand responses</strong>. In real-world retail, historical prices are rarely randomized;
            they often correlate with unobserved confounding variables—including seasonal demand surges, marketing spend,
            competitor stockouts, and bundle promotions. An anomalous positive estimate (β ≥ 0) in observational data may reflect
            promotions, seasonality, product mix changes, limited price variation, unmodeled confounders, data quality issues, or
            statistical noise (possible explanations, not established causes), and does not demonstrate an upward-sloping demand curve.
            True causal estimation requires randomized A/B price experiments or valid instrumental variables.
          </div>
        </div>
      </div>

      {/* Section 3: Scenario Simulator & Break-Even Derivation */}
      <div className="card-enterprise p-6 bg-white space-y-4">
        <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <FileCheck className="w-4 h-4 text-brand-600" />
          3. What-If Simulator, Break-Even Derivation & Edge Cases
        </h3>

        <div className="text-xs text-slate-700 leading-relaxed space-y-3">
          <p>
            The what-if simulator interprets price adjustments as <strong>fractional changes</strong>:
            Δp = PriceChangePct / 100 and Δc = CostChangePct / 100. New prices and costs are:
          </p>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg font-mono text-center text-xs">
            P<sub>1</sub> = P<sub>0</sub> · (1 + Δp), &emsp; C<sub>1</sub> = C<sub>0</sub> · (1 + Δc)
          </div>

          <p>
            Projected unit volume is modeled using the constant-elasticity power demand curve:
          </p>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg font-mono text-center text-xs">
            V<sub>1</sub> = V<sub>0</sub> · (1 + Δp)<sup>β</sup> = V<sub>0</sub> · (P<sub>1</sub> / P<sub>0</sub>)<sup>β</sup>
          </div>

          <p className="text-slate-500 text-[11px]">
            To prevent runaway mathematical artifacts, price factors are safeguarded (P<sub>1</sub>/P<sub>0</sub> ≥ 0.01) and volume multipliers are bounded (0 ≤ V<sub>1</sub> ≤ 10·V<sub>0</sub>).
          </p>

          <p>
            Unit contribution margins and gross profit dollars share exact rounded scenario figures:
          </p>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg font-mono text-center text-xs">
            CM<sub>0</sub> = P<sub>0</sub> - C<sub>0</sub>, &emsp; CM<sub>1</sub> = P<sub>1</sub> - C<sub>1</sub>
          </div>

          <p>
            The <strong>Break-Even Volume Requirement (V<sub>BE</sub>)</strong> calculates the unit sales volume necessary
            to sustain baseline gross profit dollars (GP<sub>0</sub> = V<sub>0</sub> · CM<sub>0</sub>):
          </p>

          <div className="p-3 bg-slate-900 text-slate-100 rounded-lg font-mono text-center font-bold text-xs space-y-1">
            <div>V<sub>BE</sub> = GP<sub>0</sub> / CM<sub>1</sub> = V<sub>0</sub> · (CM<sub>0</sub> / CM<sub>1</sub>)</div>
            <div className="text-brand-300">ΔV<sub>BE</sub>% = [(CM<sub>0</sub> / CM<sub>1</sub>) - 1] · 100% = {`[((P₀ - C₀) / (P₁ - C₁)) - 1]`} · 100%</div>
          </div>

          {/* Edge Cases Callout */}
          <div className="p-3.5 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-900 space-y-2">
            <strong className="font-semibold block text-amber-950">
              Contribution Margin Edge Cases & Handling:
            </strong>
            <ul className="list-disc pl-5 space-y-1 text-[11px] leading-relaxed">
              <li>
                <strong>Zero or Negative Proposed Margin (CM<sub>1</sub> ≤ 0):</strong> If proposed price fails to exceed unit cost, break-even volume is <strong>mathematically impossible</strong> (V<sub>BE</sub> = null, ΔV<sub>BE</sub>% = null). Every additional unit sold yields zero profit or compounds financial losses. The simulator issues an immediate margin dilution alert.
              </li>
              <li>
                <strong>Negative Baseline Gross Profit (GP<sub>0</sub> &lt; 0):</strong> When the baseline product is already operating at a gross loss (CM<sub>0</sub> &lt; 0), break-even volume to match a loss baseline is economically undefined (V<sub>BE</sub> = null).
              </li>
              <li>
                <strong>Zero Baseline Gross Profit (GP<sub>0</sub> = 0):</strong> If baseline profit is exactly zero, achieving zero gross profit under a positive proposed contribution margin requires 0 units (V<sub>BE</sub> = 0, ΔV<sub>BE</sub>% = -100%).
              </li>
              <li>
                <strong>Input Sanitization:</strong> Baseline prices are bounded at P<sub>0</sub> ≥ 0.01, volumes at V<sub>0</sub> ≥ 0, and cost/price change percentages are clamped to [-90%, +500%] to prevent division-by-zero or imaginary solutions.
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Section 4: Pricing Health Classification Engine & Decision Precedence */}
      <div className="card-enterprise p-6 bg-white space-y-5">
        <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <Layers className="w-4 h-4 text-brand-600" />
          4. Pricing Health Classification Engine, Decision Precedence & Tripartite Architecture
        </h3>

        <div className="text-xs text-slate-700 leading-relaxed space-y-4">
          <p>
            PricePulse employs a deterministic, hierarchical classification engine that evaluates catalog SKUs across
            profitability, discounting intensity, and econometric demand responsiveness. Every SKU is assigned exactly
            <strong> one mutually exclusive pricing health status</strong> according to a strict priority hierarchy.
          </p>

          {/* Tripartite Analytical Architecture */}
          <div className="p-4 rounded-xl bg-indigo-50/60 border border-indigo-200/80 space-y-2">
            <span className="font-bold text-brand-900 block text-xs">
              Tripartite Analytical Architecture: Separation of Concerns
            </span>
            <p className="text-[11px] text-slate-600 leading-relaxed">
              To maintain statistical integrity, the platform strictly separates three distinct operational layers:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
              <div className="bg-white p-3 rounded-lg border border-indigo-100 space-y-1">
                <strong className="text-brand-800 text-[11px] block">Layer 1: Statistical Eligibility</strong>
                <span className="text-[10px] text-slate-500 block leading-tight">
                  Econometric identification criteria (N ≥ 8 daily observations, price variance StdDev ≥ 0.01, SS<sub>xx</sub> &gt; 10<sup>-12</sup>). Determines whether an empirical OLS regression can mathematically be estimated.
                </span>
              </div>
              <div className="bg-white p-3 rounded-lg border border-indigo-100 space-y-1">
                <strong className="text-brand-800 text-[11px] block">Layer 2: Pricing-Health Status</strong>
                <span className="text-[10px] text-slate-500 block leading-tight">
                  Portfolio classification rule engine. Evaluates gross margin hurdle rates, discount leakage, and confidence intervals to label current catalog performance into 7 mutually exclusive categories.
                </span>
              </div>
              <div className="bg-white p-3 rounded-lg border border-indigo-100 space-y-1">
                <strong className="text-brand-800 text-[11px] block">Layer 3: Business Alerts & Scenarios</strong>
                <span className="text-[10px] text-slate-500 block leading-tight">
                  Downstream actionable notifications (e.g. Profit Insights upside projections, discount cannibalization alerts, and what-if simulations). Bound strictly to validated Layer 2 statuses.
                </span>
              </div>
            </div>
          </div>

          {/* Decision Precedence Order Table */}
          <div>
            <span className="font-bold text-slate-900 block mb-2">
              Hierarchical Decision Precedence (Top-Down Evaluation Order):
            </span>
            <div className="overflow-x-auto border border-slate-200 rounded-lg">
              <table className="w-full text-left text-[11px]">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="py-2.5 px-3">Priority</th>
                    <th className="py-2.5 px-3">Pricing Health Status</th>
                    <th className="py-2.5 px-4">Exact Code Criteria & Thresholds</th>
                    <th className="py-2.5 px-3">Economic Rationale & Prescribed Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  <tr className="hover:bg-slate-50/50">
                    <td className="py-2.5 px-3 font-mono font-bold text-rose-600">1 (Highest)</td>
                    <td className="py-2.5 px-3 font-bold text-rose-700">NEGATIVE_MARGIN</td>
                    <td className="py-2.5 px-4 font-mono text-[10px] text-slate-800">
                      gross_margin &lt; 0.0 (ASP &lt; COGS)
                    </td>
                    <td className="py-2.5 px-3 text-slate-600">
                      Operational loss on every unit sold. Takes highest precedence. Issues an urgent Diagnostic Warning to audit realized ASP, unit COGS, data entry errors, missing/incorrect costs, and transaction records before choosing between repricing, cost renegotiation, or discount adjustments, rather than prescribing a price increase as the sole solution.
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-50/50">
                    <td className="py-2.5 px-3 font-mono font-bold text-amber-600">2</td>
                    <td className="py-2.5 px-3 font-bold text-amber-700">LOW_MARGIN</td>
                    <td className="py-2.5 px-4 font-mono text-[10px] text-slate-800">
                      0.0 ≤ gross_margin &lt; 0.15 (15% Hurdle Rate)
                    </td>
                    <td className="py-2.5 px-3 text-slate-600">
                      Gross margin fails corporate 15% hurdle rate. Prescribes elimination of discretionary markdowns and list price realignment before volume expansion.
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-50/50">
                    <td className="py-2.5 px-3 font-mono font-bold text-purple-600">3</td>
                    <td className="py-2.5 px-3 font-bold text-purple-700">REVIEW_REQUIRED</td>
                    <td className="py-2.5 px-4 font-mono text-[10px] text-slate-800">
                      status == "ESTIMATED" and (β ≥ 0.0 or CI includes 0)
                    </td>
                    <td className="py-2.5 px-3 text-slate-600">
                      Review Required: observed correlation is non-negative (β ≥ 0.0) or 95% confidence interval includes zero (CI<sub>lower</sub> ≤ 0 ≤ CI<sub>upper</sub>). If β &gt; 0 and CI strictly positive, flags an anomalous positive association for investigation without claiming causal pricing power. If CI includes zero, the estimate is statistically inconclusive (p ≥ 0.05). Never labeled OPTIMAL or UNDERPRICED.
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-50/50">
                    <td className="py-2.5 px-3 font-mono font-bold text-slate-500">4</td>
                    <td className="py-2.5 px-3 font-bold text-slate-700">NOT_ENOUGH_DATA</td>
                    <td className="py-2.5 px-4 font-mono text-[10px] text-slate-800">
                      status in ("INSUFFICIENT_DATA", "NO_PRICE_VARIATION") or β is null or margin is null
                    </td>
                    <td className="py-2.5 px-3 text-slate-600">
                      Data completeness safeguard: missing catalog COGS, &lt; 8 observations, or static prices without variance. Algorithmic pricing recommendations are withheld until data is supplied.
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-50/50">
                    <td className="py-2.5 px-3 font-mono font-bold text-orange-600">5</td>
                    <td className="py-2.5 px-3 font-bold text-orange-700">HEAVILY_DISCOUNTED</td>
                    <td className="py-2.5 px-4 font-mono text-[10px] text-slate-800">
                      avg_discount_pct ≥ 18.0%
                    </td>
                    <td className="py-2.5 px-3 text-slate-600">
                      Severe promotional leakage across sales transactions. Requires discount floor guardrails and markdown approval limits before pricing power can be captured.
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-50/50">
                    <td className="py-2.5 px-3 font-mono font-bold text-emerald-600">6</td>
                    <td className="py-2.5 px-3 font-bold text-emerald-700">UNDERPRICED</td>
                    <td className="py-2.5 px-4 font-mono text-[10px] text-slate-800">
                      -0.9 &lt; β &lt; 0.0 &amp; CI<sub>upper</sub> &lt; 0.0 &amp; gross_margin ≥ 0.35 &amp; disc &lt; 18%
                    </td>
                    <td className="py-2.5 px-3 text-slate-600">
                      True pricing power: statistically validated inelastic demand (95% CI strictly below zero) with healthy gross margin (≥ 35%). Eligible for modeled profit upside simulations (+5% to +10% hike).
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-50/50">
                    <td className="py-2.5 px-3 font-mono font-bold text-brand-600">7</td>
                    <td className="py-2.5 px-3 font-bold text-brand-700">OPTIMAL</td>
                    <td className="py-2.5 px-4 font-mono text-[10px] text-slate-800">
                      β &lt; 0.0 &amp; CI<sub>upper</sub> &lt; 0.0 &amp; gross_margin ≥ 0.15 &amp; avg_discount_pct &lt; 18.0%
                    </td>
                    <td className="py-2.5 px-3 text-slate-600">
                      Balanced price realization: confirmed negative demand slope with statistically validated confidence interval strictly below zero, sustainable margin above 15% hurdle, and disciplined discounting. Prescribes maintaining current price point.
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-50/50 bg-slate-50/30">
                    <td className="py-2.5 px-3 font-mono text-slate-400">Fallback</td>
                    <td className="py-2.5 px-3 font-bold text-purple-700">REVIEW_REQUIRED</td>
                    <td className="py-2.5 px-4 font-mono text-[10px] text-slate-800">
                      β &lt; 0 but CI includes zero (CI<sub>lower</sub> ≤ 0 ≤ CI<sub>upper</sub>)
                    </td>
                    <td className="py-2.5 px-3 text-slate-600">
                      Statistical inconclusive gate: if the 95% CI includes zero, demand responsiveness is not statistically distinguishable from zero at α = 0.05. The estimate cannot be labeled OPTIMAL or UNDERPRICED; price changes are withheld.
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Data Quality & Edge-Case Safeguards Detail */}
          <div className="space-y-2 pt-1">
            <span className="font-bold text-slate-900 block">
              Treatment of Missing Data, Cost Semantics & Statistical Edge Cases:
            </span>
            <ul className="list-disc pl-5 text-slate-600 space-y-1.5 text-[11px] leading-relaxed">
              <li>
                <strong>Missing COGS (Completely Uncosted Products):</strong> If a product has no catalog COGS and no transaction COGS, gross margin cannot be evaluated. The product is assigned <code className="text-slate-800 font-mono">NOT_ENOUGH_DATA</code> in Pricing Analysis, issues an informational <code className="text-sky-800 font-mono">DATA_QUALITY</code> alert in Profit Insights, and is strictly excluded from both the numerator and denominator of portfolio gross margin calculations. It is never falsely labeled as zero-margin.
              </li>
              <li>
                <strong>Partially Costed Products:</strong> If a product contains both costed and uncosted transactions (e.g. from incremental CSV imports), gross margin is evaluated strictly over the cost-eligible transactions: <code>GrossMargin = EligibleProfit / EligibleRevenue</code>. In Profit Insights, revenue at margin risk includes only the cost-eligible revenue, and a diagnostic alert details the exact costed-vs-uncosted transaction split.
              </li>
              <li>
                <strong>Confidence Interval Crossing Zero:</strong> In classical econometrics, an elasticity point estimate of β = -0.30 carries no statistical weight if its 95% confidence interval is [-0.75, +0.15]. Because the interval contains zero, we cannot reject the null hypothesis of zero price responsiveness at α = 0.05. PricePulse withholds the <code className="text-emerald-800 font-mono">UNDERPRICED</code> label and assigns <code className="text-purple-800 font-mono">REVIEW_REQUIRED</code>, preventing ungrounded price increases.
              </li>
              <li>
                <strong>Exploratory Simulator Benchmark vs Empirical Estimate:</strong> The What-If Simulator requires an explicit elasticity parameter. When a product has valid empirical elasticity (β &lt; 0 and status "ESTIMATED"), it initializes with the empirical estimate and metadata <code className="text-emerald-800 font-mono">is_estimated: true</code>. For unestimated or static-price products, it loads the industry benchmark default (β = -1.20) with explicit metadata <code className="text-amber-800 font-mono">is_estimated: false</code> and source <code className="text-amber-800 font-mono">benchmark_default</code>, labeling the scenario as an exploratory assumption.
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

