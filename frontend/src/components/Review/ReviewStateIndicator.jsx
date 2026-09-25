import React from 'react';

export default function ReviewStateIndicator({ status, isPending, error, onTrigger }) {

  // Error state
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-6 text-center animate-fade-in">
        <div className="w-14 h-14 rounded-2xl bg-danger/10 border border-danger/20 flex items-center justify-center text-danger mb-5">
          <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h3 className="text-base font-semibold text-text-primary mb-1.5">Review Error</h3>
        <p className="text-sm text-text-muted max-w-sm mb-6 leading-relaxed">
          {error.message || 'An error occurred while generating the review.'}
        </p>
        <button
          onClick={onTrigger}
          className="px-5 py-2 bg-surfaceHighlight hover:bg-surface text-text-primary text-[13px] font-medium rounded-lg border border-border shadow-sm transition-all"
        >
          Try Again
        </button>
      </div>
    );
  }

  // Running / pending
  if (isPending || status === 'pending' || status === 'running') {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-6 text-center animate-fade-in">
        <div className="relative mb-6">
          {/* Outer pulse ring */}
          <div className="absolute inset-0 rounded-full bg-primary/10 animate-ping" style={{ animationDuration: '1.8s' }} />
          {/* Spinner */}
          <div className="relative w-14 h-14 rounded-full border-2 border-primary/20 flex items-center justify-center">
            <svg className="w-8 h-8 animate-spin text-primary" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
              <path className="opacity-80" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
          </div>
        </div>
        <h3 className="text-base font-semibold text-text-primary mb-2">
          {status === 'running' ? 'Analysis in Progress' : 'Review Queued'}
        </h3>
        <p className="text-sm text-text-muted max-w-xs leading-relaxed">
          {status === 'running'
            ? 'The AI intelligence engine is analyzing code changes for risk, semantic conflicts, and security issues.'
            : 'Waiting for a background worker to pick up the review job.'}
        </p>
        <div className="flex items-center gap-1.5 mt-6">
          {[0, 150, 300].map(delay => (
            <div
              key={delay}
              className="w-1.5 h-1.5 rounded-full bg-primary/60 animate-bounce"
              style={{ animationDelay: `${delay}ms` }}
            />
          ))}
        </div>
      </div>
    );
  }

  // Failed
  if (status === 'failed') {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-6 text-center animate-fade-in">
        <div className="w-14 h-14 rounded-2xl bg-danger/10 border border-danger/20 flex items-center justify-center text-danger mb-5">
          <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
        <h3 className="text-base font-semibold text-text-primary mb-1.5">Review Failed</h3>
        <p className="text-sm text-text-muted max-w-sm mb-6 leading-relaxed">
          The background worker encountered an error while generating the intelligence report.
        </p>
        <button
          onClick={onTrigger}
          className="px-5 py-2 bg-danger hover:bg-danger/90 text-white text-sm font-medium rounded-lg shadow-sm shadow-danger/20 border border-danger/20 transition-all"
        >
          Retry Review
        </button>
      </div>
    );
  }

  // Cancelled
  if (status === 'cancelled') {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-6 text-center animate-fade-in">
        <div className="w-14 h-14 rounded-2xl bg-warning/10 border border-warning/20 flex items-center justify-center text-warning mb-5">
          <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h3 className="text-base font-semibold text-text-primary mb-1.5">Review Cancelled</h3>
        <p className="text-sm text-text-muted max-w-sm mb-6 leading-relaxed">
          The automated review run was cancelled before completion.
        </p>
        <button
          onClick={onTrigger}
          className="px-5 py-2 bg-surfaceHighlight hover:bg-surface text-text-primary text-[13px] font-medium rounded-lg border border-border shadow-sm transition-all"
        >
          Restart Review
        </button>
      </div>
    );
  }

  // No active review — show trigger prompt
  return (
    <div className="flex flex-col items-center justify-center py-16 px-6 text-center animate-fade-in">
      <div className="w-16 h-16 rounded-2xl bg-surfaceHighlight border border-border flex items-center justify-center text-text-muted mb-6 shadow-sm">
        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
      </div>
      <h3 className="text-lg font-bold text-text-primary mb-2 tracking-tight">No Active Review</h3>
      <p className="text-sm text-text-muted max-w-sm mb-8 leading-relaxed">
        Start an AI-powered review to analyze this pull request for semantic conflicts, security vulnerabilities, and architectural risks.
      </p>
      <button
        onClick={onTrigger}
        disabled={isPending}
        className="inline-flex items-center gap-2.5 px-6 py-2.5 bg-primary hover:bg-primary-hover text-white text-sm font-semibold rounded-xl transition-all shadow-lg shadow-primary/20 border border-primary/20 disabled:opacity-50"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
          <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        Generate Intelligence Report
      </button>
    </div>
  );
}
