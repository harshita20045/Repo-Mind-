import React from 'react';
import { SeverityBadge } from '../ui/Badge';

export default function BreakingChangesList({ breakingChanges = [] }) {
  if (breakingChanges.length === 0) {
    return (
      <div className="bg-surface border border-border rounded-lg p-5 flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-success/10 border border-success/20 flex items-center justify-center text-success flex-shrink-0">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <div>
          <h3 className="text-sm font-semibold text-text-primary">
            No Breaking Changes Detected
          </h3>
          <p className="text-[12px] text-text-secondary mt-0.5">
            Public function signatures, exported symbols, database models, and API route contracts are backward-compatible.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
          <span>Breaking Changes</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-danger/10 text-danger font-mono font-bold">
            {breakingChanges.length}
          </span>
        </h3>
        <span className="text-[11px] text-danger font-medium">
          Requires immediate review or backward-compatibility layer
        </span>
      </div>

      <div className="space-y-3">
        {breakingChanges.map((change, idx) => (
          <div
            key={idx}
            className="bg-surface border border-danger/30 rounded-lg p-4 transition-colors hover:border-danger/50"
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
              <div className="flex items-center gap-2 flex-wrap">
                <SeverityBadge severity={change.severity || 'critical'} />
                <span className="font-mono text-xs font-semibold text-text-primary bg-surfaceHighlight px-2 py-0.5 rounded border border-border">
                  {change.component_name}
                </span>
                <span className="text-[11px] font-mono text-text-muted">
                  {change.file_path}{change.line_number ? `:${change.line_number}` : ''}
                </span>
              </div>
              <span className="text-[10px] uppercase tracking-wider font-bold text-text-muted bg-white/5 px-2 py-0.5 rounded border border-white/5">
                {change.change_type?.replace(/_/g, ' ') || 'mutation'}
              </span>
            </div>

            <p className="text-[13px] text-text-secondary leading-relaxed mb-3">
              {change.description}
            </p>

            {change.evidence && (
              <div className="bg-surfaceHighlight/50 border border-border rounded p-2.5 mb-3">
                <div className="text-[11px] font-semibold text-text-muted mb-1 uppercase tracking-wider">
                  Supporting Evidence
                </div>
                <pre className="font-mono text-[12px] text-rose-300 whitespace-pre-wrap break-all">
                  {change.evidence}
                </pre>
              </div>
            )}

            {change.suggested_fix && (
              <div className="flex items-start gap-2 text-[12px] text-text-primary bg-primary/5 border border-primary/20 rounded p-2.5">
                <span className="text-primary font-semibold flex-shrink-0">Suggested Fix:</span>
                <span className="text-text-secondary">{change.suggested_fix}</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
