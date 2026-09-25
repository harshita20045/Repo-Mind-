import React from 'react';
import { SeverityBadge } from '../ui/Badge';
import EmptyState from '../ui/EmptyState';

// ─── Conflict card ─────────────────────────────────────────────────────────────
function ConflictCard({ conflict }) {
  const sev = conflict.severity?.toLowerCase() || 'medium';
  const leftColors = {
    critical: 'bg-danger',
    high:     'bg-orange-500',
    medium:   'bg-warning',
    low:      'bg-success',
  };
  const leftColor = leftColors[sev] || 'bg-text-muted';

  const typeLabel = conflict.conflict_type?.replace(/_/g, ' ') || 'Unknown';

  return (
    <div className="relative flex overflow-hidden bg-surface border border-border rounded-lg shadow-sm hover:bg-surfaceHighlight transition-colors">
      {/* Left severity strip */}
      <div className={`w-1 flex-shrink-0 ${leftColor}`} aria-hidden="true" />

      <div className="flex-1 p-5 min-w-0">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-center gap-2 flex-wrap">
            <SeverityBadge severity={sev} />
            <span className="inline-flex items-center px-2 py-0.5 text-xs font-semibold text-text-muted bg-surfaceHighlight border border-border rounded uppercase tracking-wider">
              {typeLabel}
            </span>
          </div>
        </div>

        {/* Description */}
        <p className="text-sm text-text-secondary leading-relaxed mb-4">
          {conflict.description}
        </p>

        {/* Related files */}
        {conflict.related_files && conflict.related_files.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">Conflicting Files</p>
            <div className="flex flex-wrap gap-1.5">
              {conflict.related_files.map((file, i) => (
                <div
                  key={i}
                  className="flex items-center gap-1.5 font-mono text-[11px] text-text-secondary bg-surfaceHighlight border border-border px-2 py-1 rounded"
                >
                  <svg className="w-3 h-3 text-text-muted flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                  {file}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Related PRs */}
        {conflict.related_pr_numbers && conflict.related_pr_numbers.length > 0 && (
          <div className="mt-3">
            <p className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">Related PRs</p>
            <div className="flex gap-1.5">
              {conflict.related_pr_numbers.map((num, i) => (
                <span key={i} className="font-mono text-xs text-accent bg-accent/10 border border-accent/20 px-2 py-0.5 rounded">
                  #{num}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Confidence */}
        {conflict.confidence_score != null && (
          <div className="mt-3 pt-3 border-t border-white/[0.05] flex items-center gap-2">
            <span className="text-xs text-text-muted">Confidence</span>
            <div className="flex-1 max-w-[80px] h-1 bg-white/5 rounded-full overflow-hidden">
              <div
                className="h-full bg-primary rounded-full"
                style={{ width: `${(conflict.confidence_score * 100).toFixed(0)}%` }}
              />
            </div>
            <span className="text-xs text-text-secondary font-semibold">
              {(conflict.confidence_score * 100).toFixed(0)}%
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Conflict List ─────────────────────────────────────────────────────────────
export default function ConflictList({ conflicts = [] }) {
  if (!conflicts || conflicts.length === 0) {
    return (
      <EmptyState
        icon="success"
        variant="success"
        title="No Semantic Conflicts Detected"
        description="The conflict engine found no API contract breakages, overlapping architectural changes, or logic conflicts in this PR."
        className="py-16"
      />
    );
  }

  // Sort: critical > high > medium > low
  const order = { critical: 0, high: 1, medium: 2, low: 3 };
  const sorted = [...conflicts].sort((a, b) => {
    const aO = order[a.severity?.toLowerCase()] ?? 4;
    const bO = order[b.severity?.toLowerCase()] ?? 4;
    return aO - bO;
  });

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
          Semantic Conflicts
          <span className="text-xs font-bold px-2 py-0.5 bg-white/5 border border-white/10 rounded text-text-muted">
            {conflicts.length}
          </span>
        </h3>
      </div>
      <p className="text-xs text-text-muted leading-relaxed mb-4">
        These conflicts represent logic clashes, API breakages, or overlapping work that Git cannot detect mechanically.
      </p>
      <div className="space-y-3">
        {sorted.map((conflict, i) => (
          <ConflictCard key={i} conflict={conflict} />
        ))}
      </div>
    </div>
  );
}
