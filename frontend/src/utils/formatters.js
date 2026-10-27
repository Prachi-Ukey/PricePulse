/**
 * Financial, Econometric & Statistical Formatting Utilities
 */

/**
 * Formats a p-value into a statistically appropriate string.
 * Never displays a computed p-value as exactly 0 when it is below floating-point precision.
 * @param {number|null|undefined} pVal - Raw numeric p-value
 * @param {string|null|undefined} pValDisplay - Backend provided display string (e.g. "< 0.0001")
 * @returns {string} Formatted p-value (e.g., "< 0.0001", "0.0024", "0.1450")
 */
export function formatPValue(pVal, pValDisplay) {
  if (pValDisplay && typeof pValDisplay === 'string') {
    return pValDisplay;
  }
  if (pVal === null || pVal === undefined || isNaN(Number(pVal))) {
    return '—';
  }
  const num = Number(pVal);
  if (num < 0.0001) {
    return '< 0.0001';
  }
  return num.toFixed(4);
}

/**
 * Returns human-readable model-fit label and tone for an R² value
 * with cautious wording that does not treat R² alone as a validity test.
 * @param {number|null|undefined} rSquared
 * @returns {{ rating: string, label: string, colorClass: string, badgeVariant: string, description: string }}
 */
export function getModelFitInfo(rSquared) {
  if (rSquared === null || rSquared === undefined || isNaN(Number(rSquared))) {
    return {
      rating: 'N/A',
      label: 'Undetermined',
      colorClass: 'text-slate-500',
      badgeVariant: 'default',
      description: 'Model fit could not be determined due to insufficient or static data.'
    };
  }

  const r2 = Number(rSquared);
  if (r2 >= 0.65) {
    return {
      rating: 'STRONG',
      label: 'Strong In-Sample Fit',
      colorClass: 'text-emerald-700 bg-emerald-50 border-emerald-200',
      badgeVariant: 'success',
      description: `Historical price variation accounts for ${(r2 * 100).toFixed(1)}% of log-demand variation. Cautious note: High R² reflects in-sample empirical correlation and does not prove absence of confounders.`
    };
  }
  if (r2 >= 0.35) {
    return {
      rating: 'MODERATE',
      label: 'Moderate In-Sample Fit',
      colorClass: 'text-indigo-700 bg-indigo-50 border-indigo-200',
      badgeVariant: 'info',
      description: `Price variation accounts for ${(r2 * 100).toFixed(1)}% of demand fluctuations. Substantial residual variation suggests non-price factors (seasonality, stock, promotions) actively drive purchases.`
    };
  }
  return {
    rating: 'WEAK',
    label: 'Low Explanatory Power',
    colorClass: 'text-amber-800 bg-amber-50 border-amber-200',
    badgeVariant: 'warning',
    description: `Price changes explain only ${(r2 * 100).toFixed(1)}% of demand variance. Volume is largely driven by unmodeled factors or noisy observations. Interpret elasticity with heightened caution.`
  };
}

/**
 * Formats currency values consistently.
 * @param {number} val 
 * @returns {string} e.g. "$1,250.50"
 */
export function formatCurrency(val) {
  if (val === null || val === undefined || isNaN(Number(val))) return '$0.00';
  return `$${Number(val).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/**
 * Calculates actual selling price from list price and discount %.
 */
export function calcActualPrice(unitPrice, discountPct) {
  const p = Math.max(0, Number(unitPrice || 0));
  const d = Math.max(0, Math.min(100, Number(discountPct || 0)));
  return Number((p * (1 - d / 100)).toFixed(2));
}

/**
 * Calculates gross margin percentage safely.
 */
export function calcGrossMargin(grossProfit, revenue) {
  if (!revenue || Number(revenue) <= 0) return 0;
  return Number((Number(grossProfit) / Number(revenue)).toFixed(4));
}
