import React, { useEffect, useState } from 'react';
import {
  DollarSign,
  Package,
  Percent,
  TrendingUp,
  Tag,
  Receipt,
  Filter,
  BarChart2
} from 'lucide-react';
import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  BarChart,
  Cell,
  PieChart,
  Pie
} from 'recharts';
import { getDashboardMetrics, getCategories, getChannels } from '../api/client';
import MetricCard from '../components/common/MetricCard';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorState from '../components/common/ErrorState';

export default function DashboardPage() {
  const [metrics, setMetrics] = useState(null);
  const [categories, setCategories] = useState([]);
  const [channels, setChannels] = useState([]);
  const [channelsLoading, setChannelsLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedChannel, setSelectedChannel] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const fetchMetrics = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (selectedCategory) params.category = selectedCategory;
      if (selectedChannel) params.channel = selectedChannel;
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const data = await getDashboardMetrics(params);
      setMetrics(data);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to fetch dashboard metrics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getCategories().then(setCategories).catch(() => {});
    setChannelsLoading(true);
    getChannels()
      .then((data) => setChannels(Array.isArray(data) ? data : []))
      .catch((err) => {
        console.error('Failed to load sales channels', err);
        setChannels([]);
      })
      .finally(() => setChannelsLoading(false));
  }, []);

  useEffect(() => {
    fetchMetrics();
  }, [selectedCategory, selectedChannel, startDate, endDate]);

  if (loading && !metrics) {
    return <LoadingSpinner message="Calculating revenue, margins, and historical trends..." />;
  }

  if (error && !metrics) {
    return <ErrorState message={error} onRetry={fetchMetrics} />;
  }

  const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4'];

  return (
    <div className="space-y-6">
      {/* Filter Bar */}
      <div className="card-enterprise p-4 bg-white flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-slate-700 font-semibold text-xs">
          <Filter className="w-4 h-4 text-brand-600" />
          <span>PORTFOLIO FILTERS:</span>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Category Filter */}
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>

          {/* Channel Filter */}
          <select
            value={selectedChannel}
            onChange={(e) => setSelectedChannel(e.target.value)}
            disabled={channelsLoading}
            className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option value="">All Sales Channels</option>
            {channels.map((chan) => (
              <option key={chan} value={chan}>
                {chan}
              </option>
            ))}
          </select>

          {/* Reset Filters */}
          {(selectedCategory || selectedChannel || startDate || endDate) && (
            <button
              onClick={() => {
                setSelectedCategory('');
                setSelectedChannel('');
                setStartDate('');
                setEndDate('');
              }}
              className="text-xs text-brand-600 hover:text-brand-800 font-medium px-2 py-1"
            >
              Reset Filters
            </button>
          )}
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <MetricCard
          title="Total Revenue"
          value={`$${metrics.total_revenue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          subvalue={`${metrics.total_transactions.toLocaleString()} sales lines`}
          changePct={metrics.revenue_growth_pct}
          changeLabel="prior half"
          icon={DollarSign}
          variant="brand"
        />

        <MetricCard
          title="Units Sold"
          value={metrics.total_units_sold.toLocaleString()}
          subvalue="Total quantity fulfilled"
          changePct={metrics.units_growth_pct}
          changeLabel="prior half"
          icon={Package}
          variant="default"
        />

        <MetricCard
          title="Average Selling Price"
          value={`$${metrics.average_selling_price.toFixed(2)}`}
          subvalue="Weighted Realized ASP"
          icon={Receipt}
          variant="default"
        />

        <MetricCard
          title="Gross Profit"
          value={`$${metrics.total_gross_profit.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          subvalue="Revenue minus COGS"
          changePct={metrics.profit_growth_pct}
          changeLabel="prior half"
          icon={TrendingUp}
          variant="emerald"
        />

        <MetricCard
          title="Gross Margin"
          value={`${(metrics.overall_gross_margin * 100).toFixed(1)}%`}
          subvalue="Gross Profit / Revenue"
          changePct={metrics.margin_diff_pct}
          changeLabel="margin pts"
          icon={Percent}
          variant="brand"
        />

        <MetricCard
          title="Avg Discount Rate"
          value={`${metrics.average_discount_pct.toFixed(1)}%`}
          subvalue="Catalog weighted markdowns"
          icon={Tag}
          variant="amber"
        />
      </div>

      {/* Historical Revenue, Profit, and ASP Trends */}
      <div className="card-enterprise p-5 bg-white">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-4 mb-4 border-b border-slate-100 gap-2">
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <BarChart2 className="w-4 h-4 text-brand-600" />
              Historical Revenue & Profitability Trends (14-Month Run)
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Monthly breakdown of realized revenue, gross profit, and realized average selling price (ASP).
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs font-medium text-slate-600">
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded bg-indigo-500"></span> Revenue
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded bg-emerald-500"></span> Gross Profit
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-0.5 bg-amber-500"></span> ASP ($)
            </span>
          </div>
        </div>

        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={metrics.trends} margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} />
              <YAxis
                yAxisId="left"
                tick={{ fontSize: 11, fill: '#64748b' }}
                tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                tick={{ fontSize: 11, fill: '#f59e0b' }}
                tickFormatter={(val) => `$${val}`}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip
                formatter={(val, name) => {
                  if (name === 'ASP') return [`$${Number(val).toFixed(2)}`, 'ASP'];
                  return [`$${Number(val).toLocaleString()}`, name];
                }}
                contentStyle={{
                  backgroundColor: '#ffffff',
                  borderColor: '#e2e8f0',
                  borderRadius: '0.5rem',
                  fontSize: '12px',
                  boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                }}
              />
              <Bar yAxisId="left" dataKey="revenue" name="Revenue" fill="#6366f1" radius={[4, 4, 0, 0]} maxBarSize={40} />
              <Bar yAxisId="left" dataKey="gross_profit" name="Gross Profit" fill="#10b981" radius={[4, 4, 0, 0]} maxBarSize={40} />
              <Line yAxisId="right" type="monotone" dataKey="asp" name="ASP" stroke="#f59e0b" strokeWidth={2.5} dot={{ r: 3 }} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Category Performance & Channels Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Category Revenue Breakdown */}
        <div className="card-enterprise p-5 bg-white lg:col-span-2">
          <div className="pb-3 mb-4 border-b border-slate-100 flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900 tracking-tight">
              Category Revenue & Margin Performance
            </h3>
            <span className="text-xs text-slate-400">Ranked by Total Revenue</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 text-slate-400 font-semibold uppercase">
                  <th className="pb-2.5">Category</th>
                  <th className="pb-2.5 text-right">Revenue</th>
                  <th className="pb-2.5 text-right">Units</th>
                  <th className="pb-2.5 text-right">Gross Profit</th>
                  <th className="pb-2.5 text-right">Margin %</th>
                  <th className="pb-2.5 text-right">Rev Share</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {metrics.category_breakdown.map((cat, idx) => (
                  <tr key={cat.category} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-2.5 flex items-center gap-2">
                      <span
                        className="w-2.5 h-2.5 rounded-full shrink-0"
                        style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                      />
                      <span className="font-semibold text-slate-800">{cat.category}</span>
                      <span className="text-[10px] text-slate-400">({cat.product_count} SKUs)</span>
                    </td>
                    <td className="py-2.5 text-right font-mono text-slate-900">
                      ${cat.revenue.toLocaleString()}
                    </td>
                    <td className="py-2.5 text-right text-slate-600 font-mono">
                      {cat.units.toLocaleString()}
                    </td>
                    <td className="py-2.5 text-right text-emerald-600 font-mono font-semibold">
                      ${cat.gross_profit.toLocaleString()}
                    </td>
                    <td className="py-2.5 text-right">
                      <span
                        className={`inline-block px-1.5 py-0.5 rounded text-[11px] font-semibold ${
                          cat.gross_margin >= 0.4
                            ? 'bg-emerald-50 text-emerald-700'
                            : cat.gross_margin >= 0.25
                            ? 'bg-brand-50 text-brand-700'
                            : 'bg-rose-50 text-rose-700'
                        }`}
                      >
                        {(cat.gross_margin * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-2.5 text-right text-slate-500 font-mono">
                      {cat.share_of_revenue.toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Sales Channels Distribution */}
        <div className="card-enterprise p-5 bg-white">
          <div className="pb-3 mb-4 border-b border-slate-100">
            <h3 className="text-sm font-bold text-slate-900 tracking-tight">
              Channel Contribution
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">Fulfillment & partner channels</p>
          </div>

          <div className="space-y-4 pt-2">
            {metrics.channel_breakdown.map((chan, idx) => {
              const share = metrics.total_revenue > 0 ? (chan.revenue / metrics.total_revenue) * 100 : 0;
              return (
                <div key={chan.channel} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-800">{chan.channel}</span>
                    <span className="font-mono text-slate-900 font-medium">
                      ${chan.revenue.toLocaleString()} ({share.toFixed(1)}%)
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${share}%`,
                        backgroundColor: COLORS[idx % COLORS.length],
                      }}
                    />
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span>{chan.units.toLocaleString()} units</span>
                    <span className="text-emerald-600 font-medium">
                      Margin: {(chan.gross_margin * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
