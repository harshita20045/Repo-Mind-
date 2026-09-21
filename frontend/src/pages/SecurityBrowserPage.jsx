import React from 'react';

export default function SecurityBrowserPage() {
  return (
    <div className="space-y-5 animate-slide-up">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary tracking-tight">Security Browser</h1>
        <p className="text-sm text-text-muted mt-1">
          Organization-wide view of vulnerabilities and code quality issues.
        </p>
      </div>

      {/* Filters bar — static context only */}
      <div className="bg-surface border border-white/[0.07] rounded-xl p-4 grid grid-cols-1 md:grid-cols-4 gap-3">
        {/* Search */}
        <div className="md:col-span-2 relative">
          <svg className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            placeholder="Search by rule, file, or repository…"
            disabled
            aria-label="Search (not yet available)"
            className="w-full bg-surfaceHighlight/20 border border-white/[0.07] text-text-muted text-sm rounded-lg pl-9 pr-4 py-2 cursor-not-allowed opacity-60 focus:outline-none"
          />
        </div>
        <select
          disabled
          aria-label="Filter by severity (not yet available)"
          className="bg-surfaceHighlight/20 border border-white/[0.07] text-text-muted text-sm rounded-lg px-3 py-2 cursor-not-allowed opacity-60 focus:outline-none appearance-none"
        >
          <option>All Severities</option>
        </select>
        <select
          disabled
          aria-label="Filter by state (not yet available)"
          className="bg-surfaceHighlight/20 border border-white/[0.07] text-text-muted text-sm rounded-lg px-3 py-2 cursor-not-allowed opacity-60 focus:outline-none appearance-none"
        >
          <option>All States</option>
        </select>
      </div>

      {/* Empty state */}
      <div className="bg-surface border border-white/[0.07] rounded-xl overflow-hidden">
        <div className="flex flex-col items-center justify-center py-20 px-6 text-center">
          <div className="w-16 h-16 rounded-2xl bg-surfaceHighlight/60 border border-white/[0.08] flex items-center justify-center text-text-muted mb-5">
            <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
          </div>
          <h3 className="text-sm font-semibold text-text-primary mb-2">Global Security Findings API Not Yet Available</h3>
          <p className="text-sm text-text-muted max-w-md leading-relaxed mb-2">
            This view will aggregate security and code quality findings across all repositories.
            The global findings API endpoint is planned for a future release.
          </p>
          <p className="text-xs text-text-muted">
            Per-PR security findings are available on the{' '}
            <span className="text-primary font-medium">Pull Request Review</span> page.
          </p>
        </div>
      </div>
    </div>
  );
}
