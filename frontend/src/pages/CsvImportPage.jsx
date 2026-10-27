import React, { useState, useEffect } from 'react';
import {
  UploadCloud,
  FileText,
  CheckCircle,
  AlertTriangle,
  Download,
  RotateCcw,
  Check,
  X,
  History,
  ShieldCheck,
  AlertCircle
} from 'lucide-react';
import {
  previewCsvFile,
  importCsvFile,
  getSampleTemplateUrl,
  resetSyntheticData,
  getImportLogs
} from '../api/client';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Badge from '../components/common/Badge';
import Modal from '../components/common/Modal';

export default function CsvImportPage() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewResult, setPreviewResult] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [importLoading, setImportLoading] = useState(false);
  const [importStatus, setImportStatus] = useState(null); // { type: 'success'|'error', message: '' }
  const [importLogs, setImportLogs] = useState([]);
  const [isResetModalOpen, setIsResetModalOpen] = useState(false);
  const [resetLoading, setResetLoading] = useState(false);

  const [priceMode, setPriceMode] = useState('list_price');

  const fetchLogs = () => {
    getImportLogs()
      .then(setImportLogs)
      .catch((err) => console.error(err));
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const runPreview = async (file, mode) => {
    if (!file) return;
    setPreviewLoading(true);
    setPreviewResult(null);
    setImportStatus(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('price_mode', mode);

    try {
      const preview = await previewCsvFile(formData);
      setPreviewResult(preview);
    } catch (err) {
      setImportStatus({
        type: 'error',
        message: err?.response?.data?.detail || 'Failed to parse and validate CSV file.',
      });
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setSelectedFile(file);
    await runPreview(file, priceMode);
  };

  const handlePriceModeChange = async (newMode) => {
    setPriceMode(newMode);
    if (selectedFile) {
      await runPreview(selectedFile, newMode);
    }
  };

  const handleExecuteImport = async () => {
    if (!selectedFile) return;
    setImportLoading(true);
    setImportStatus(null);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('price_mode', priceMode);

    try {
      const res = await importCsvFile(formData);
      setImportStatus({
        type: 'success',
        message: res.message,
      });
      fetchLogs();
    } catch (err) {
      setImportStatus({
        type: 'error',
        message: err?.response?.data?.detail || 'Import failed. Database transaction was rolled back.',
      });
      fetchLogs();
    } finally {
      setImportLoading(false);
    }
  };

  const handleResetData = async () => {
    setResetLoading(true);
    try {
      await resetSyntheticData();
      setIsResetModalOpen(false);
      setImportStatus({
        type: 'success',
        message: 'Database reset to 100 deterministic synthetic products and exactly 4,948 sales transactions successfully.',
      });
      setSelectedFile(null);
      setPreviewResult(null);
      fetchLogs();
    } catch (err) {
      setImportStatus({
        type: 'error',
        message: 'Failed to reset synthetic seed data.',
      });
    } finally {
      setResetLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload Zone & Actions Bar */}
      <div className="card-enterprise p-6 bg-white">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <h2 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <UploadCloud className="w-5 h-5 text-brand-600" />
              CSV Sales Data Import & Pre-Validation Engine
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Strict column validation, duplicate detection, metadata conflict safeguards, and atomic transactional rollback.
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <a
              href={getSampleTemplateUrl()}
              download="pricepulse_sample_template.csv"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition-colors border border-slate-200"
            >
              <Download className="w-3.5 h-3.5" />
              Download Sample CSV Template
            </a>

            <button
              onClick={() => setIsResetModalOpen(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-800 text-xs font-semibold transition-colors border border-amber-200"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Reset Synthetic Seed Data
            </button>
          </div>
        </div>

        {/* Price Interpretation Mode Selector */}
        <div className="mt-5 p-4 rounded-xl bg-slate-50 border border-slate-200">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <span className="text-xs font-bold text-slate-900 block">
                CSV Unit Price Interpretation Mode
              </span>
              <span className="text-[11px] text-slate-500">
                Specify whether <code>unit_price</code> in your CSV is the pre-discount list price or realized net selling price.
              </span>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => handlePriceModeChange('list_price')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors border ${
                  priceMode === 'list_price'
                    ? 'bg-brand-600 text-white border-brand-600 shadow-xs'
                    : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-100'
                }`}
              >
                List Price (MSRP) [Default]
              </button>
              <button
                type="button"
                onClick={() => handlePriceModeChange('net_price')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors border ${
                  priceMode === 'net_price'
                    ? 'bg-brand-600 text-white border-brand-600 shadow-xs'
                    : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-100'
                }`}
              >
                Net Selling Price (ASP)
              </button>
            </div>
          </div>

          <div className="mt-2 text-[11px] text-slate-600 leading-relaxed border-t border-slate-200/60 pt-2">
            {priceMode === 'list_price' ? (
              <span>
                <strong>List Price Mode:</strong> CSV <code>unit_price</code> represents pre-discount catalog list price (MSRP). Realized revenue = <code>Quantity × [unit_price × (1 - discount_pct/100)]</code>.
              </span>
            ) : (
              <span>
                <strong>Net Selling Price Mode:</strong> CSV <code>unit_price</code> is already the net selling price (ASP). Realized revenue = <code>Quantity × unit_price</code> (preventing double-discounting). Pre-discount list price is reconstructed if discount percentage is provided.
              </span>
            )}
          </div>
        </div>

        {/* Drag & Drop File Zone */}
        <div className="mt-5">
          <label className="border-2 border-dashed border-slate-300 hover:border-brand-500 rounded-xl p-8 flex flex-col items-center justify-center cursor-pointer bg-slate-50/50 hover:bg-slate-50 transition-colors">
            <UploadCloud className="w-10 h-10 text-slate-400 mb-2" />
            <span className="text-xs font-bold text-slate-800">
              Click to choose CSV or drag and drop sales file
            </span>
            <span className="text-[11px] text-slate-400 mt-1">
              Required: sku, name, category, sale_date, quantity, unit_price | Optional: discount_pct, cogs_per_unit, channel
            </span>
            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="hidden"
            />
          </label>
        </div>

        {/* Feedback Alert */}
        {importStatus && (
          <div
            className={`mt-4 p-4 rounded-lg text-xs flex items-start gap-2.5 ${
              importStatus.type === 'success'
                ? 'bg-emerald-50 text-emerald-900 border border-emerald-200'
                : 'bg-rose-50 text-rose-900 border border-rose-200'
            }`}
          >
            {importStatus.type === 'success' ? (
              <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
            )}
            <div>
              <strong className="font-semibold">
                {importStatus.type === 'success' ? 'Import Successful:' : 'Import Blocked / Rolled Back:'}
              </strong>{' '}
              {importStatus.message}
            </div>
          </div>
        )}
      </div>

      {/* Pre-Import Validation & Preview Section */}
      {previewLoading ? (
        <LoadingSpinner message="Checking columns, checking format syntax, and verifying dates..." />
      ) : previewResult ? (
        <div className="card-enterprise p-5 bg-white space-y-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-slate-900 tracking-tight">
                  File Validation Preview: {previewResult.filename}
                </h3>
                <span className="inline-block px-2 py-0.5 rounded text-[10px] font-semibold bg-brand-50 text-brand-700 border border-brand-200">
                  {previewResult.price_mode === 'net_price' ? 'Net Selling Price (ASP) Mode' : 'List Price (MSRP) Mode'}
                </span>
                {previewResult.metadata_conflict_count > 0 && (
                  <span className="inline-block px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                    {previewResult.metadata_conflict_count} Metadata Conflicts
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Total rows detected: {previewResult.total_rows} • Valid lines:{' '}
                <span className="font-semibold text-emerald-600">{previewResult.valid_rows_count}</span> •
                Errors:{' '}
                <span className="font-semibold text-rose-600">{previewResult.invalid_rows_count}</span>
              </p>
            </div>

            {/* Commit Import Button */}
            <button
              onClick={handleExecuteImport}
              disabled={importLoading || !previewResult.is_ready_for_import}
              className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold shadow-xs transition-colors ${
                previewResult.is_ready_for_import
                  ? 'bg-brand-600 hover:bg-brand-700 text-white'
                  : 'bg-slate-200 text-slate-400 cursor-not-allowed'
              }`}
            >
              {importLoading ? (
                <>
                  <LoadingSpinner size="sm" /> Committing Transaction...
                </>
              ) : (
                <>
                  <Check className="w-4 h-4" />
                  {previewResult.is_ready_for_import
                    ? `Safe Import ${previewResult.valid_rows_count} Rows`
                    : 'Fix Errors to Import'}
                </>
              )}
            </button>
          </div>

          {/* Error Summary Box if invalid */}
          {previewResult.error_summary?.length > 0 && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-900 space-y-1">
              <strong className="font-bold flex items-center gap-1.5">
                <AlertCircle className="w-4 h-4 text-rose-600" />
                Validation Issues Detected:
              </strong>
              <ul className="list-disc pl-5 space-y-0.5">
                {previewResult.error_summary.map((err, idx) => (
                  <li key={idx}>{err}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Preview Table */}
          <div className="overflow-x-auto border border-slate-200 rounded-lg">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase">
                <tr>
                  <th className="py-2.5 px-3">Row #</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">SKU</th>
                  <th className="py-2.5 px-3">Product Name</th>
                  <th className="py-2.5 px-3">Category</th>
                  <th className="py-2.5 px-3">Date</th>
                  <th className="py-2.5 px-3 text-right">Quantity</th>
                  <th className="py-2.5 px-3 text-right">Unit Price</th>
                  <th className="py-2.5 px-3 text-right">Discount</th>
                  <th className="py-2.5 px-3 text-right">Realized ASP</th>
                  <th className="py-2.5 px-3 text-right">Revenue</th>
                  <th className="py-2.5 px-3">Validation Message</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono">
                {previewResult.preview_rows.map((row) => (
                  <tr
                    key={row.row_number}
                    className={row.is_valid ? 'hover:bg-slate-50' : 'bg-rose-50/50'}
                  >
                    <td className="py-2 px-3 text-slate-400 font-sans font-medium">{row.row_number}</td>
                    <td className="py-2 px-3 font-sans">
                      {row.is_valid ? (
                        <span className="inline-flex items-center text-emerald-600 gap-1 text-[11px] font-semibold">
                          <Check className="w-3.5 h-3.5" /> Valid
                        </span>
                      ) : (
                        <span className="inline-flex items-center text-rose-600 gap-1 text-[11px] font-semibold">
                          <X className="w-3.5 h-3.5" /> Error
                        </span>
                      )}
                    </td>
                    <td className="py-2 px-3 font-semibold text-slate-800">{row.data?.sku || '—'}</td>
                    <td className="py-2 px-3 font-sans text-slate-800">{row.data?.name || '—'}</td>
                    <td className="py-2 px-3 font-sans text-slate-600">{row.data?.category || '—'}</td>
                    <td className="py-2 px-3 text-slate-600">{row.data?.sale_date || '—'}</td>
                    <td className="py-2 px-3 text-right text-slate-800">{row.data?.quantity || '—'}</td>
                    <td className="py-2 px-3 text-right text-slate-800">${row.data?.unit_price || '—'}</td>
                    <td className="py-2 px-3 text-right text-slate-600">{row.data?.discount_pct || 0}%</td>
                    <td className="py-2 px-3 text-right text-slate-800 font-semibold">
                      {row.data?.actual_selling_price ? `$${Number(row.data.actual_selling_price).toFixed(2)}` : '—'}
                    </td>
                    <td className="py-2 px-3 text-right text-emerald-700 font-semibold">
                      {row.data?.calculated_revenue ? `$${Number(row.data.calculated_revenue).toFixed(2)}` : '—'}
                    </td>
                    <td className="py-2 px-3 font-sans text-[11px] text-rose-700 font-medium">
                      {row.errors.join('; ')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}

      {/* Historical Import Log */}
      <div className="card-enterprise p-5 bg-white">
        <div className="pb-3 mb-4 border-b border-slate-100 flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <History className="w-4 h-4 text-brand-600" />
            Audit Log of Import Operations
          </h3>
          <span className="text-xs text-slate-400">Database Transaction History</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-400 font-semibold uppercase">
              <tr>
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">Filename</th>
                <th className="py-2.5 px-3 text-center">Status</th>
                <th className="py-2.5 px-3 text-right">Rows</th>
                <th className="py-2.5 px-3 text-right">Valid</th>
                <th className="py-2.5 px-3">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {importLogs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-50">
                  <td className="py-2 px-3 text-slate-500 font-mono text-[11px]">{log.created_at}</td>
                  <td className="py-2 px-3 font-mono text-slate-900 font-semibold">{log.filename}</td>
                  <td className="py-2 px-3 text-center">
                    <Badge label={log.status} variant={log.status} size="xs" />
                  </td>
                  <td className="py-2 px-3 text-right font-mono text-slate-700">{log.row_count}</td>
                  <td className="py-2 px-3 text-right font-mono text-emerald-600 font-semibold">
                    {log.valid_count}
                  </td>
                  <td className="py-2 px-3 text-slate-600 text-[11px] max-w-xs truncate">{log.details}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Reset Confirmation Modal */}
      <Modal
        isOpen={isResetModalOpen}
        onClose={() => setIsResetModalOpen(false)}
        title="Confirm Synthetic Database Reset"
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-600 leading-relaxed">
            This operation will clear all existing products, sales transactions, and import logs, and rebuild
            the deterministic synthetic catalog:
          </p>
          <ul className="text-xs list-disc pl-5 text-slate-700 space-y-1">
            <li>100 products across 6 retail categories</li>
            <li>4,948 sales transaction records (sales lines) across 14 months</li>
            <li>Elastic, inelastic, static-price, and seasonal segments for analytical benchmarking</li>
          </ul>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <button
              onClick={() => setIsResetModalOpen(false)}
              className="px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              onClick={handleResetData}
              disabled={resetLoading}
              className="px-4 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold"
            >
              {resetLoading ? 'Resetting Database...' : 'Confirm Reset to Synthetic Data'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
