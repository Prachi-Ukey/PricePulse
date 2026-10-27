import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export default function MetricCard({
  title,
  value,
  subvalue,
  changePct,
  changeLabel = 'vs prior period',
  icon: Icon,
  variant = 'default', // 'default', 'brand', 'emerald', 'amber', 'rose'
}) {
  const iconBgClasses = {
    default: 'bg-slate-100 text-slate-700',
    brand: 'bg-brand-50 text-brand-600',
    emerald: 'bg-emerald-50 text-emerald-600',
    amber: 'bg-amber-50 text-amber-600',
    rose: 'bg-rose-50 text-rose-600',
  };

  const isPositive = typeof changePct === 'number' && changePct > 0;
  const isNegative = typeof changePct === 'number' && changePct < 0;
  const isNeutral = typeof changePct === 'number' && changePct === 0;

  return (
    <div className="card-enterprise p-5 bg-white">
      <div className="flex items-start justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          {title}
        </span>
        {Icon && (
          <div className={`p-2 rounded-lg ${iconBgClasses[variant] || iconBgClasses.default}`}>
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div className="mt-2.5">
        <div className="text-2xl font-bold text-slate-900 tracking-tight font-sans">
          {value}
        </div>
        {subvalue && (
          <div className="text-xs text-slate-500 mt-0.5">{subvalue}</div>
        )}
      </div>

      {typeof changePct === 'number' && (
        <div className="mt-3 pt-3 border-t border-slate-100 flex items-center gap-1.5 text-xs">
          {isPositive && (
            <span className="inline-flex items-center text-emerald-600 font-semibold gap-0.5">
              <TrendingUp className="w-3.5 h-3.5" />
              +{changePct.toFixed(1)}%
            </span>
          )}
          {isNegative && (
            <span className="inline-flex items-center text-rose-600 font-semibold gap-0.5">
              <TrendingDown className="w-3.5 h-3.5" />
              {changePct.toFixed(1)}%
            </span>
          )}
          {isNeutral && (
            <span className="inline-flex items-center text-slate-500 font-medium gap-0.5">
              <Minus className="w-3.5 h-3.5" />
              0.0%
            </span>
          )}
          <span className="text-slate-400 font-normal">{changeLabel}</span>
        </div>
      )}
    </div>
  );
}
