import React from 'react';

const BADGE_STYLES = {
  // Elasticity
  ELASTIC: 'bg-indigo-50 text-indigo-700 border-indigo-200',
  INELASTIC: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  UNITARY: 'bg-sky-50 text-sky-700 border-sky-200',
  ANOMALOUS_POSITIVE: 'bg-amber-50 text-amber-700 border-amber-200',
  ESTIMATED: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  INSUFFICIENT_DATA: 'bg-amber-50 text-amber-800 border-amber-200',
  NO_PRICE_VARIATION: 'bg-slate-100 text-slate-700 border-slate-200',

  // Pricing Health
  OPTIMAL: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  NEGATIVE_MARGIN: 'bg-rose-100 text-rose-800 border-rose-300 font-bold',
  LOW_MARGIN: 'bg-rose-50 text-rose-700 border-rose-200',
  HEAVILY_DISCOUNTED: 'bg-amber-50 text-amber-700 border-amber-200',
  REVIEW_REQUIRED: 'bg-purple-50 text-purple-700 border-purple-200',
  ANOMALOUS: 'bg-purple-50 text-purple-700 border-purple-200',
  NOT_ENOUGH_DATA: 'bg-slate-100 text-slate-600 border-slate-200',
  UNDERPRICED: 'bg-violet-50 text-violet-700 border-violet-200',

  // Severity
  high: 'bg-rose-50 text-rose-700 border-rose-200',
  medium: 'bg-amber-50 text-amber-800 border-amber-200',
  low: 'bg-sky-50 text-sky-700 border-sky-200',
  info: 'bg-slate-100 text-slate-700 border-slate-200',

  // General Status
  SUCCESS: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  FAILED: 'bg-rose-50 text-rose-700 border-rose-200',
  ROLLED_BACK: 'bg-amber-50 text-amber-800 border-amber-200',
  default: 'bg-slate-100 text-slate-700 border-slate-200',
};

export default function Badge({ label, variant, size = 'sm' }) {
  const key = variant || label;
  const style = BADGE_STYLES[key] || BADGE_STYLES.default;
  const sizeClasses = size === 'xs' ? 'px-1.5 py-0.5 text-[10px]' : 'px-2 py-0.5 text-xs';

  return (
    <span
      className={`inline-flex items-center font-medium rounded-md border tracking-tight ${style} ${sizeClasses}`}
    >
      {label}
    </span>
  );
}
