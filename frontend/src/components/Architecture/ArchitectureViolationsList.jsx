import React, { useState, useMemo } from 'react';
import { SeverityBadge } from '../ui/Badge';

export default function ArchitectureViolationsList({ violations = [] }) {
  const [filterSeverity, setFilterSeverity] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  const counts = useMemo(() => {
    return {
      all: violations.length,
      critical: violations.filter(v => v.severity === 'critical').length,
      high: violations.filter(v => v.severity === 'high').length,
      medium: violations.filter(v => v.severity === 'medium').length,
      low: violations.filter(v => v.severity === 'low').length,
    };
  }, [violations]);

  const filteredViolations = useMemo(() => {
    return violations.filter(v => {
      if (filterSeverity !== 'all' && v.severity !== filterSeverity) {
        return false;
      }
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const matchesCode = v.rule_code?.toLowerCase().includes(query);
        const matchesTitle = v.title?.toLowerCase().includes(query);
        const matchesSource = v.source_file?.toLowerCase().includes(query);
        const matchesTarget = v.target_file?.toLowerCase().includes(query);
        return matchesCode || matchesTitle || matchesSource || matchesTarget;
      }
      return true;
    });
  }, [violations, filterSeverity, searchQuery]);

  if (violations.length === 0) {
    return (
      <div className="bg-surface border border-border rounded-lg p-8 text-center space-y-3">
        <div className="w-10 h-10 rounded-full bg-success/10 border border-success/20 flex items-center justify-center text-success mx-auto">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h3 className="text-sm font-semibold text-text-primary">
          Zero Architecture Rule Violations
        </h3>
        <p className="text-[12px] text-text-secondary max-w-md mx-auto">
          All modules respect their configured architectural boundaries, layer separation rules, and import policies.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filtering and Search Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-surface border border-border rounded-lg p-3">
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
          <button
            onClick={() => setFilterSeverity('all')}
            className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
              filterSeverity === 'all'
                ? 'bg-primary/10 text-primary border border-primary/20'
                : 'text-text-muted hover:text-text-primary'
            }`}
          >
            All ({counts.all})
          </button>
          {counts.critical > 0 && (
            <button
              onClick={() => setFilterSeverity('critical')}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                filterSeverity === 'critical'
                  ? 'bg-danger/10 text-danger border border-danger/20'
                  : 'text-text-muted hover:text-text-primary'
              }`}
            >
              Critical ({counts.critical})
            </button>
          )}
          {counts.high > 0 && (
            <button
              onClick={() => setFilterSeverity('high')}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                filterSeverity === 'high'
                  ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                  : 'text-text-muted hover:text-text-primary'
              }`}
            >
              High ({counts.high})
            </button>
          )}
          {counts.medium > 0 && (
            <button
              onClick={() => setFilterSeverity('medium')}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                filterSeverity === 'medium'
                  ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20'
                  : 'text-text-muted hover:text-text-primary'
              }`}
            >
              Medium ({counts.medium})
            </button>
          )}
        </div>

        <div className="relative min-w-[220px]">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search rule or file..."
            className="w-full bg-surfaceHighlight border border-border rounded px-3 py-1.5 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary"
          />
        </div>
      </div>

      {/* Violations List */}
      {filteredViolations.length === 0 ? (
        <div className="bg-surface border border-border rounded-lg p-6 text-center text-text-muted text-[13px]">
          No violations match your filter criteria.
        </div>
      ) : (
        <div className="space-y-3">
          {filteredViolations.map((v, idx) => (
            <div
              key={idx}
              className="bg-surface border border-border rounded-lg p-4 transition-all hover:border-white/20"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-surfaceHighlight border border-border text-text-primary">
                    {v.rule_code}
                  </span>
                  <SeverityBadge severity={v.severity} />
                  <span className="text-[10px] uppercase font-bold font-mono px-1.5 py-0.5 rounded bg-white/5 text-text-muted">
                    {v.violation_type?.replace(/_/g, ' ')}
                  </span>
                  <span className="text-xs font-semibold text-text-primary">
                    {v.title}
                  </span>
                </div>
                <div className="font-mono text-[11px] text-text-muted">
                  {v.source_file}{v.source_line ? `:${v.source_line}` : ''}
                </div>
              </div>

              <p className="text-[12px] text-text-secondary leading-relaxed mb-3">
                {v.explanation}
              </p>

              {v.evidence && (
                <div className="bg-surfaceHighlight/50 border border-border rounded p-2.5 mb-2.5">
                  <span className="text-[10px] uppercase tracking-wider font-semibold text-text-muted block mb-1">
                    Offending Evidence
                  </span>
                  <code className="font-mono text-xs text-rose-300 whitespace-pre-wrap break-all">
                    {v.evidence}
                  </code>
                </div>
              )}

              {v.suggested_correction && (
                <div className="flex items-start gap-2 bg-primary/5 border border-primary/20 rounded p-2.5 text-[12px]">
                  <span className="text-primary font-semibold flex-shrink-0 text-[11px] uppercase tracking-wider">
                    Suggested Correction:
                  </span>
                  <span className="text-text-secondary">{v.suggested_correction}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
