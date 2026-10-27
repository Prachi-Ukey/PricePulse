import React from 'react';
import { Loader2 } from 'lucide-react';

export default function LoadingSpinner({ message = 'Loading analytics data...', size = 'md' }) {
  const spinnerSizes = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  return (
    <div className="flex flex-col items-center justify-center p-12 text-slate-500">
      <Loader2 className={`${spinnerSizes[size] || spinnerSizes.md} animate-spin text-brand-600 mb-3`} />
      <span className="text-sm font-medium text-slate-600">{message}</span>
    </div>
  );
}
