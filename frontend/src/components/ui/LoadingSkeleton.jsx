import React from 'react';

// Single skeleton block
export function Skeleton({ className = '', rounded = 'md' }) {
  const r = { sm: 'rounded', md: 'rounded-lg', lg: 'rounded-xl', full: 'rounded-full' };
  return (
    <div className={`skeleton ${r[rounded] || r.md} ${className}`} aria-hidden="true" />
  );
}

// Metric card skeleton
export function MetricCardSkeleton() {
  return (
    <div className="bg-surface border border-white/[0.07] rounded-xl p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <Skeleton className="h-3 w-28" />
        <Skeleton className="h-8 w-8" rounded="lg" />
      </div>
      <Skeleton className="h-9 w-20" />
      <Skeleton className="h-2.5 w-32" />
    </div>
  );
}

// Table row skeleton
export function TableRowSkeleton({ cols = 4 }) {
  return (
    <tr className="border-b border-white/[0.06]" aria-hidden="true">
      {Array.from({ length: cols }).map((_, i) => (
        <td key={i} className="px-4 py-3.5">
          <Skeleton className={`h-4 ${i === 0 ? 'w-48' : i === cols - 1 ? 'w-16' : 'w-24'}`} />
        </td>
      ))}
    </tr>
  );
}

// Card list skeleton
export function CardListSkeleton({ count = 3 }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="bg-surface border border-white/[0.07] rounded-xl p-5" aria-hidden="true">
          <div className="flex items-start gap-3">
            <Skeleton className="h-8 w-8 flex-shrink-0" rounded="full" />
            <div className="flex-1 space-y-2.5">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-3 w-1/2" />
              <Skeleton className="h-3 w-1/3" />
            </div>
            <Skeleton className="h-5 w-16" rounded="full" />
          </div>
        </div>
      ))}
    </div>
  );
}

// Sidebar item skeleton
export function SidebarSkeleton() {
  return (
    <div className="space-y-1 px-3" aria-hidden="true">
      {[60, 80, 50, 70, 55].map((w, i) => (
        <div key={i} className="flex items-center gap-3 px-3 py-2.5">
          <Skeleton className="h-4 w-4 flex-shrink-0" rounded="sm" />
          <Skeleton className={`h-3.5`} style={{ width: `${w}%` }} />
        </div>
      ))}
    </div>
  );
}

// Dashboard skeleton
export function DashboardSkeleton() {
  return (
    <div className="space-y-6" aria-label="Loading dashboard" aria-busy="true">
      <div className="space-y-1">
        <Skeleton className="h-8 w-56" />
        <Skeleton className="h-4 w-80" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {[0,1,2,3].map(i => <MetricCardSkeleton key={i} />)}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {[0,1].map(i => (
          <div key={i} className="bg-surface border border-white/[0.07] rounded-xl p-5 space-y-4">
            <Skeleton className="h-5 w-40" />
            {[0,1,2,3].map(j => (
              <div key={j} className="flex items-center gap-4">
                <Skeleton className="h-3.5 w-20" />
                <div className="flex-1">
                  <Skeleton className={`h-2.5 rounded-full`} style={{ width: `${60 + j * 10}%` }} />
                </div>
                <Skeleton className="h-3.5 w-8" />
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

// Loading spinner
export function Spinner({ size = 'md', className = '' }) {
  const sizes = { sm: 'w-4 h-4', md: 'w-6 h-6', lg: 'w-8 h-8', xl: 'w-10 h-10' };
  return (
    <svg
      className={`animate-spin text-primary ${sizes[size] || sizes.md} ${className}`}
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <circle className="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
      <path className="opacity-80" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
    </svg>
  );
}

// Full-page loading state
export function PageLoader({ message = 'Loading...' }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] gap-4" role="status" aria-label={message}>
      <Spinner size="lg" />
      <p className="text-sm text-text-muted animate-pulse">{message}</p>
    </div>
  );
}
