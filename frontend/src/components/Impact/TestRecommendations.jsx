import React, { useState } from 'react';

const PRIORITY_CONFIG = {
  P0: {
    label: 'P0 - Critical Path',
    badge: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
  },
  P1: {
    label: 'P1 - Direct Dependent',
    badge: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  },
  P2: {
    label: 'P2 - Transitive Blast Radius',
    badge: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  },
};

export default function TestRecommendations({ testRecommendations = [] }) {
  const [copiedIdx, setCopiedIdx] = useState(null);

  const handleCopy = (command, idx) => {
    navigator.clipboard.writeText(command);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  if (testRecommendations.length === 0) {
    return (
      <div className="bg-surface border border-border rounded-lg p-5 text-center text-text-muted text-[13px]">
        No specific test recommendations generated for this change set.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
          <span>Recommended Tests</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary font-mono font-bold">
            {testRecommendations.length}
          </span>
        </h3>
        <span className="text-[11px] text-text-muted">
          Prioritized by component criticality and dependency proximity
        </span>
      </div>

      <div className="space-y-3">
        {testRecommendations.map((rec, idx) => {
          const priority = PRIORITY_CONFIG[rec.priority] || PRIORITY_CONFIG.P2;
          const isCopied = copiedIdx === idx;

          return (
            <div
              key={idx}
              className="bg-surface border border-border rounded-lg p-4 transition-colors hover:border-white/20"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider border ${priority.badge}`}>
                    {priority.label}
                  </span>
                  <span className="text-[11px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-surfaceHighlight border border-border text-text-secondary">
                    {rec.test_type}
                  </span>
                  <span className="font-mono text-xs font-semibold text-text-primary">
                    {rec.target_component}
                  </span>
                </div>
                <span className="font-mono text-[11px] text-text-muted">
                  Target: {rec.target_file}
                </span>
              </div>

              <p className="text-[12px] text-text-secondary leading-relaxed mb-3">
                {rec.reason}
              </p>

              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 bg-surfaceHighlight/50 border border-border rounded p-2.5">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider flex-shrink-0">
                    Run:
                  </span>
                  <code className="font-mono text-[12px] text-primary truncate" title={rec.command}>
                    {rec.command}
                  </code>
                </div>
                <button
                  type="button"
                  onClick={() => handleCopy(rec.command, idx)}
                  className="flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-medium rounded bg-surfaceHighlight hover:bg-white/10 text-text-primary border border-border transition-colors flex-shrink-0 self-end sm:self-auto"
                >
                  {isCopied ? (
                    <>
                      <svg className="w-3.5 h-3.5 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-success">Copied!</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-3.5 h-3.5 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                      <span>Copy Command</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
