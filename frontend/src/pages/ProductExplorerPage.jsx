import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Filter,
  Download,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  Eye,
  Sliders,
  DollarSign,
  Package,
  TrendingUp,
  Percent
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip
} from 'recharts';
import { getProducts, getCategories, getProductDetail, getExportCsvUrl } from '../api/client';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorState from '../components/common/ErrorState';
import Badge from '../components/common/Badge';
import Modal from '../components/common/Modal';
import { formatPValue } from '../utils/formatters';

export default function ProductExplorerPage() {
  const navigate = useNavigate();
  const [productsData, setProductsData] = useState(null);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters & Pagination
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [sortBy, setSortBy] = useState('revenue');
  const [sortOrder, setSortOrder] = useState('desc');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(15);

  // Detail Modal State
  const [selectedProductId, setSelectedProductId] = useState(null);
  const [productDetail, setProductDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const fetchProducts = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getProducts({
        page,
        page_size: pageSize,
        search: search || undefined,
        category: category || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      setProductsData(data);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load products catalog.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getCategories().then(setCategories).catch(() => {});
  }, []);

  useEffect(() => {
    fetchProducts();
  }, [page, pageSize, category, sortBy, sortOrder]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchProducts();
  };

  const handleViewDetail = async (prodId) => {
    setSelectedProductId(prodId);
    setDetailLoading(true);
    try {
      const detail = await getProductDetail(prodId);
      setProductDetail(detail);
    } catch (err) {
      console.error('Failed to load detail', err);
    } finally {
      setDetailLoading(false);
    }
  };

  return (
    <div className="space-y-5">
      {/* Search, Filter, Sort & Export Header */}
      <div className="card-enterprise p-4 bg-white flex flex-wrap items-center justify-between gap-3">
        {/* Search Input */}
        <form onSubmit={handleSearchSubmit} className="relative min-w-[260px] flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by SKU or product name..."
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </form>

        <div className="flex flex-wrap items-center gap-2.5">
          {/* Category Filter */}
          <select
            value={category}
            onChange={(e) => {
              setCategory(e.target.value);
              setPage(1);
            }}
            className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>

          {/* Sort Column */}
          <select
            value={sortBy}
            onChange={(e) => {
              setSortBy(e.target.value);
              setPage(1);
            }}
            className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option value="revenue">Sort by Revenue</option>
            <option value="units">Sort by Units</option>
            <option value="profit">Sort by Profit</option>
            <option value="base_price">Sort by Base Price</option>
            <option value="cogs">Sort by COGS</option>
            <option value="name">Sort by Name</option>
            <option value="sku">Sort by SKU</option>
          </select>

          {/* Sort Order Toggle */}
          <button
            onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            className="p-1.5 text-xs border border-slate-200 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-700 flex items-center gap-1 font-semibold"
            title="Toggle Sort Direction"
          >
            <ArrowUpDown className="w-3.5 h-3.5" />
            <span className="uppercase">{sortOrder}</span>
          </button>

          {/* Export CSV Button */}
          <a
            href={getExportCsvUrl({ search: search || undefined, category: category || undefined })}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold transition-colors shadow-xs"
          >
            <Download className="w-3.5 h-3.5" />
            Export CSV
          </a>
        </div>
      </div>

      {/* Main Product Table */}
      {loading ? (
        <LoadingSpinner message="Querying product catalog and sales aggregations..." />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchProducts} />
      ) : (
        <div className="card-enterprise bg-white overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-400 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">SKU / Product</th>
                  <th className="py-3 px-3">Category</th>
                  <th className="py-3 px-3 text-right">Base List</th>
                  <th className="py-3 px-3 text-right">Unit COGS</th>
                  <th className="py-3 px-3 text-right">Realized ASP</th>
                  <th className="py-3 px-3 text-right">Units Sold</th>
                  <th className="py-3 px-3 text-right">Total Revenue</th>
                  <th className="py-3 px-3 text-right">Gross Profit</th>
                  <th className="py-3 px-3 text-right">Margin</th>
                  <th className="py-3 px-3 text-right">Avg Disc</th>
                  <th className="py-3 px-4 text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {productsData?.items?.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50/80 transition-colors">
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
                    <td className="py-3 px-3 text-right font-mono text-slate-500">
                      {item.cogs != null ? `$${item.cogs.toFixed(2)}` : <span className="text-slate-400 italic">Missing</span>}
                    </td>
                    <td className="py-3 px-3 text-right font-mono text-slate-900 font-semibold">
                      ${item.asp.toFixed(2)}
                    </td>
                    <td className="py-3 px-3 text-right font-mono text-slate-600">
                      {item.total_units_sold.toLocaleString()}
                    </td>
                    <td className="py-3 px-3 text-right font-mono text-slate-900 font-semibold">
                      ${item.total_revenue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-3 text-right font-mono text-emerald-600 font-semibold">
                      {item.total_gross_profit != null ? `$${item.total_gross_profit.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : <span className="text-slate-400 italic">N/A</span>}
                    </td>
                    <td className="py-3 px-3 text-right">
                      {item.gross_margin != null ? (
                        <span
                          className={`inline-block px-1.5 py-0.5 rounded text-[11px] font-semibold ${
                            item.gross_margin >= 0.4
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              : item.gross_margin >= 0.2
                              ? 'bg-brand-50 text-brand-700 border border-brand-200'
                              : item.gross_margin >= 0.0
                              ? 'bg-amber-50 text-amber-700 border border-amber-200'
                              : 'bg-rose-50 text-rose-700 border border-rose-200'
                          }`}
                        >
                          {(item.gross_margin * 100).toFixed(1)}%
                        </span>
                      ) : (
                        <span className="inline-block px-1.5 py-0.5 rounded text-[11px] font-medium text-slate-500 bg-slate-100 border border-slate-200">
                          Missing Cost
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-right font-mono text-slate-500">
                      {item.avg_discount_pct.toFixed(1)}%
                    </td>
                    <td className="py-3 px-4 text-center">
                      <div className="flex items-center justify-center gap-1.5">
                        <button
                          onClick={() => handleViewDetail(item.id)}
                          className="p-1 rounded hover:bg-slate-100 text-slate-600 hover:text-slate-900 transition-colors"
                          title="View Product Analysis"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => navigate(`/simulator?product_id=${item.id}`)}
                          className="p-1 rounded hover:bg-brand-50 text-brand-600 hover:text-brand-800 transition-colors"
                          title="Open What-If Simulator"
                        >
                          <Sliders className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination Bar */}
          <div className="p-4 border-t border-slate-200/80 bg-slate-50/50 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-600">
            <div className="flex items-center gap-3">
              <span>
                Showing{' '}
                <strong className="text-slate-900">
                  {((page - 1) * pageSize) + 1} - {Math.min(page * pageSize, productsData?.total || 0)}
                </strong>{' '}
                of <strong className="text-slate-900">{productsData?.total || 0}</strong> products
              </span>

              {/* Items per page selector */}
              <select
                value={pageSize}
                onChange={(e) => {
                  setPageSize(Number(e.target.value));
                  setPage(1);
                }}
                className="bg-white border border-slate-200 rounded px-2 py-1 text-xs"
              >
                <option value={10}>10 per page</option>
                <option value={15}>15 per page</option>
                <option value={25}>25 per page</option>
                <option value={50}>50 per page</option>
              </select>
            </div>

            {/* Page buttons */}
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="p-1.5 rounded border border-slate-200 bg-white hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="px-3 py-1 font-semibold text-slate-800">
                Page {page} of {productsData?.total_pages || 1}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(productsData?.total_pages || 1, p + 1))}
                disabled={page >= (productsData?.total_pages || 1)}
                className="p-1.5 rounded border border-slate-200 bg-white hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Product Detail Modal */}
      <Modal
        isOpen={!!selectedProductId}
        onClose={() => {
          setSelectedProductId(null);
          setProductDetail(null);
        }}
        title={productDetail?.product?.name || 'Product Details'}
        maxWidth="max-w-4xl"
      >
        {detailLoading ? (
          <LoadingSpinner message="Loading SKU details, elasticity, and transaction log..." />
        ) : productDetail ? (
          <div className="space-y-6">
            {/* Header Metadata */}
            <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-lg bg-slate-50 border border-slate-200">
              <div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-brand-50 text-brand-700 font-semibold border border-brand-200">
                  {productDetail.product.sku}
                </span>
                <span className="ml-2 text-xs text-slate-500 font-medium">
                  {productDetail.product.category}
                </span>
                <p className="text-xs text-slate-600 mt-2">
                  {productDetail.product.description}
                </p>
              </div>

              <button
                onClick={() => {
                  const id = productDetail.product.id;
                  setSelectedProductId(null);
                  navigate(`/simulator?product_id=${id}`);
                }}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold shadow-xs"
              >
                <Sliders className="w-3.5 h-3.5" />
                Simulate Pricing Strategy
              </button>
            </div>

            {/* Metric Summary Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
              <div className="p-3 bg-white border border-slate-200 rounded-lg">
                <span className="text-[10px] uppercase font-bold text-slate-400">Total Revenue</span>
                <div className="text-base font-bold text-slate-900 mt-0.5">
                  ${productDetail.metrics.total_revenue.toLocaleString()}
                </div>
              </div>
              <div className="p-3 bg-white border border-slate-200 rounded-lg">
                <span className="text-[10px] uppercase font-bold text-slate-400">Gross Margin</span>
                <div className="text-base font-bold text-emerald-600 mt-0.5">
                  {productDetail.metrics.gross_margin != null ? `${(productDetail.metrics.gross_margin * 100).toFixed(1)}%` : 'Missing Cost'}
                </div>
              </div>
              <div className="p-3 bg-white border border-slate-200 rounded-lg">
                <span className="text-[10px] uppercase font-bold text-slate-400">Realized ASP</span>
                <div className="text-base font-bold text-slate-900 mt-0.5">
                  ${productDetail.metrics.asp.toFixed(2)}
                </div>
              </div>
              <div className="p-3 bg-white border border-slate-200 rounded-lg">
                <span className="text-[10px] uppercase font-bold text-slate-400">Units Fulfilled</span>
                <div className="text-base font-bold text-slate-900 mt-0.5">
                  {productDetail.metrics.total_units_sold.toLocaleString()}
                </div>
              </div>
            </div>

            {/* Elasticity Diagnostic */}
            <div className="p-4 rounded-lg border border-slate-200 bg-slate-50/50">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                  Price Elasticity Econometric Status
                </h4>
                <Badge
                  label={productDetail.elasticity.status}
                  variant={productDetail.elasticity.status}
                />
              </div>

              {productDetail.elasticity.status === 'ESTIMATED' ? (
                <div className="text-xs space-y-1.5">
                  <div className="flex items-center gap-4">
                    <span>
                      Point Elasticity (β):{' '}
                      <strong className="text-brand-700 font-mono text-sm">
                        {productDetail.elasticity.elasticity}
                      </strong>
                    </span>
                    <span>
                      R²:{' '}
                      <strong className="font-mono">{productDetail.elasticity.r_squared}</strong>
                    </span>
                    <span>
                      p-value:{' '}
                      <strong className="font-mono">{formatPValue(productDetail.elasticity.p_value, productDetail.elasticity.p_value_display)}</strong>
                    </span>
                  </div>
                  <p className="text-slate-500 text-[11px]">
                    Interpretation: {productDetail.elasticity.interpretation} demand.
                  </p>
                </div>
              ) : (
                <p className="text-xs text-amber-800 bg-amber-50 p-2 rounded border border-amber-200">
                  {productDetail.elasticity.warning_message}
                </p>
              )}
            </div>

            {/* Recent Transaction Lines */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                Recent Sales Transactions
              </h4>
              <div className="overflow-x-auto border border-slate-200 rounded-lg max-h-56">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold sticky top-0">
                    <tr>
                      <th className="py-2 px-3">Date</th>
                      <th className="py-2 px-3">Txn Code</th>
                      <th className="py-2 px-2 text-right">Qty</th>
                      <th className="py-2 px-2 text-right">Price</th>
                      <th className="py-2 px-2 text-right">Disc %</th>
                      <th className="py-2 px-3 text-right">Revenue</th>
                      <th className="py-2 px-3 text-right">Profit</th>
                      <th className="py-2 px-3">Channel</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-mono">
                    {productDetail.recent_transactions.map((t) => (
                      <tr key={t.id} className="hover:bg-slate-50">
                        <td className="py-1.5 px-3 text-slate-600">{t.sale_date}</td>
                        <td className="py-1.5 px-3 text-slate-500">{t.transaction_code}</td>
                        <td className="py-1.5 px-2 text-right text-slate-700">{t.quantity}</td>
                        <td className="py-1.5 px-2 text-right text-slate-700">${t.actual_selling_price.toFixed(2)}</td>
                        <td className="py-1.5 px-2 text-right text-slate-500">{t.discount_pct}%</td>
                        <td className="py-1.5 px-3 text-right text-slate-900 font-semibold">${t.revenue.toFixed(2)}</td>
                        <td className="py-1.5 px-3 text-right text-emerald-600">${(t.gross_profit ?? 0).toFixed(2)}</td>
                        <td className="py-1.5 px-3 font-sans text-slate-600 text-[11px]">{t.channel}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        ) : null}
      </Modal>
    </div>
  );
}
