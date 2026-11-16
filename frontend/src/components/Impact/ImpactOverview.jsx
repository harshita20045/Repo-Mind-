import React from 'react';
import { RiskBadge } from '../ui/Badge';

export default function ImpactOverview({ impactData }) {
  if (!impactData) return null;

  const {
    risk_level = 'low',
    directly_affected_count = 0,
    indirectly_affected_count = 0,
    breaking_changes_count = 0,
    test_recommendations = [],
    summary,
  } = impactData;

  const totalAffected = directly_affected_count + indirectly_affected_count;

  return (
    <div className="space-y-4">
      {/* Top Banner */}
      <div className="bg-surface border border-border rounded-lg p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5 mb-1.5">
            <h2 className="text-base font-semibold text-text-primary">
              Change Impact & Blast Radius Analysis
            </h2>
            <RiskBadge level={risk_level} />
          </div>
          <p className="text-[13px] text-text-secondary leading-relaxed max-w-3xl">
            {summary || 'Blast radius analysis measures code surface area exposed to modified symbols and calls, grounded in repository knowledge graph dependencies.'}
          </p>
        </div>
        <div className="flex items-center gap-2 text-[12px] text-text-muted self-start md:self-auto">
          <span className="inline-block w-2 h-2 rounded-full bg-primary animate-pulse" />
          <span>Knowledge Graph Grounded</span>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-surface border border-border rounded-lg p-4 flex flex-col justify-between">
          <div className="text-[11px] font-medium text-text-muted uppercase tracking-wider mb-2">
            Directly Affected
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-rose-400">
              {directly_affected_count}
            </span>
            <span className="text-[11px] text-text-muted">components</span>
          </div>
          <div className="text-[11px] text-text-secondary mt-2">
            Immediate callers & direct imports (Hop 1)
          </div>
        </div>

        <div className="bg-surface border border-border rounded-lg p-4 flex flex-col justify-between">
          <div className="text-[11px] font-medium text-text-muted uppercase tracking-wider mb-2">
            Indirectly Affected
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-amber-400">
              {indirectly_affected_count}
            </span>
            <span className="text-[11px] text-text-muted">components</span>
          </div>
          <div className="text-[11px] text-text-secondary mt-2">
            Transitive callers & downstream modules (Hop 2-3)
          </div>
        </div>

        <div className="bg-surface border border-border rounded-lg p-4 flex flex-col justify-between">
          <div className="text-[11px] font-medium text-text-muted uppercase tracking-wider mb-2">
            Breaking Changes
          </div>
          <div className="flex items-baseline gap-2">
            <span className={`text-2xl font-bold font-mono ${breaking_changes_count > 0 ? 'text-danger' : 'text-success'}`}>
              {breaking_changes_count}
            </span>
            <span className="text-[11px] text-text-muted">detected</span>
          </div>
          <div className="text-[11px] text-text-secondary mt-2">
            {breaking_changes_count > 0 ? 'Signature mutations or schema changes' : 'No breaking mutations found'}
          </div>
        </div>

        <div className="bg-surface border border-border rounded-lg p-4 flex flex-col justify-between">
          <div className="text-[11px] font-medium text-text-muted uppercase tracking-wider mb-2">
            Recommended Tests
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-primary">
              {test_recommendations.length}
            </span>
            <span className="text-[11px] text-text-muted">test targets</span>
          </div>
          <div className="text-[11px] text-text-secondary mt-2">
            Prioritized unit, integration & regression tests
          </div>
        </div>
      </div>
    </div>
  );
}
