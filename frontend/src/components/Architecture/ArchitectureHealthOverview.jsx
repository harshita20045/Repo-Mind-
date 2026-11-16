import React from 'react';
import { RiskBadge } from '../ui/Badge';
import { Button } from '../ui/Button';

export default function ArchitectureHealthOverview({
  analysis,
  isLoading = false,
  onTriggerAudit,
  isAuditing = false,
}) {
  if (!analysis) return null;

  const {
    health_score = 100,
    inferred_pattern = 'layered_mvc',
    pattern_confidence = 1.0,
    total_violations = 0,
    critical_violations = 0,
    circular_dependency_count = 0,
    layer_summary = {},
  } = analysis;

  const totalModules = Object.values(layer_summary).reduce(
    (acc, cur) => acc + (cur.file_count || 0),
    0
  );

  // Health gauge styling
  const isGood = health_score >= 80;
  const isFair = health_score >= 50 && health_score < 80;
  const scoreColor = isGood ? 'text-success' : isFair ? 'text-warning' : 'text-danger';
  const strokeColor = isGood ? 'stroke-success' : isFair ? 'stroke-warning' : 'stroke-danger';

  const r = 36;
  const circ = 2 * Math.PI * r;
  const offset = circ - (circ * health_score) / 100;

  return (
    <div className="space-y-4">
      {/* Top Banner with Health Score and Inferred Pattern */}
      <div className="bg-surface border border-border rounded-lg p-5 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-center gap-5">
          {/* Circular Score Gauge */}
          <div className="relative w-20 h-20 flex-shrink-0">
            <svg className="w-20 h-20 -rotate-90" viewBox="0 0 80 80">
              <circle
                cx="40"
                cy="40"
                r={r}
                fill="none"
                stroke="currentColor"
                strokeWidth="7"
                className="text-surfaceHighlight"
              />
              <circle
                cx="40"
                cy="40"
                r={r}
                fill="none"
                strokeWidth="7"
                strokeDasharray={circ}
                strokeDashoffset={offset}
                strokeLinecap="round"
                className={`${strokeColor} transition-all duration-1000`}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className={`text-xl font-bold font-mono ${scoreColor}`}>
                {health_score}
              </span>
              <span className="text-[9px] uppercase font-semibold text-text-muted">Health</span>
            </div>
          </div>

          <div>
            <div className="flex items-center gap-2.5 mb-1 flex-wrap">
              <h2 className="text-base font-semibold text-text-primary">
                Architecture Health & Pattern Compliance
              </h2>
              <span className="px-2 py-0.5 rounded text-[11px] font-bold font-mono uppercase bg-primary/10 text-primary border border-primary/20">
                {inferred_pattern.replace(/_/g, ' ')}
              </span>
              <span className="text-[11px] text-text-muted font-mono">
                {Math.round(pattern_confidence * 100)}% Confidence
              </span>
            </div>
            <p className="text-[13px] text-text-secondary leading-relaxed max-w-2xl">
              Architecture health measures structural stability, cyclic coupling, and adherence to layer boundaries without enforcing dogmatic assumptions.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 self-start md:self-auto flex-shrink-0">
          <Button
            variant="secondary"
            onClick={onTriggerAudit}
            disabled={isAuditing}
            className="text-xs"
          >
            {isAuditing ? 'Auditing Architecture...' : 'Run Architecture Audit'}
          </Button>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-surface border border-border rounded-lg p-4 flex flex-col justify-between">
          <div className="text-[11px] font-medium text-text-muted uppercase tracking-wider mb-2">
            Total Violations
          </div>
          <div className="flex items-baseline gap-2">
            <span className={`text-2xl font-bold font-mono ${total_violations > 0 ? 'text-amber-400' : 'text-success'}`}>
              {total_violations}
            </span>
            <span className="text-[11px] text-text-muted">rule findings</span>
          </div>
          <div className="text-[11px] text-text-secondary mt-2">
            {total_violations === 0 ? 'Compliant with all active rules' : 'Design boundary issues identified'}
          </div>
        </div>

        <div className="bg-surface border border-border rounded-lg p-4 flex flex-col justify-between">
          <div className="text-[11px] font-medium text-text-muted uppercase tracking-wider mb-2">
            Critical Violations
          </div>
          <div className="flex items-baseline gap-2">
            <span className={`text-2xl font-bold font-mono ${critical_violations > 0 ? 'text-danger' : 'text-success'}`}>
              {critical_violations}
            </span>
            <span className="text-[11px] text-text-muted">critical</span>
          </div>
          <div className="text-[11px] text-text-secondary mt-2">
            {critical_violations > 0 ? 'Leaky controller or forbidden bypass' : 'No critical layer leaks'}
          </div>
        </div>

        <div className="bg-surface border border-border rounded-lg p-4 flex flex-col justify-between">
          <div className="text-[11px] font-medium text-text-muted uppercase tracking-wider mb-2">
            Circular Dependencies
          </div>
          <div className="flex items-baseline gap-2">
            <span className={`text-2xl font-bold font-mono ${circular_dependency_count > 0 ? 'text-danger' : 'text-success'}`}>
              {circular_dependency_count}
            </span>
            <span className="text-[11px] text-text-muted">cycles</span>
          </div>
          <div className="text-[11px] text-text-secondary mt-2">
            {circular_dependency_count === 0 ? 'Acyclic dependency graph' : 'Cyclic loops require decoupling'}
          </div>
        </div>

        <div className="bg-surface border border-border rounded-lg p-4 flex flex-col justify-between">
          <div className="text-[11px] font-medium text-text-muted uppercase tracking-wider mb-2">
            Cataloged Modules
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-primary">
              {totalModules || '—'}
            </span>
            <span className="text-[11px] text-text-muted">files in layers</span>
          </div>
          <div className="text-[11px] text-text-secondary mt-2">
            Mapped across {Object.keys(layer_summary).length} architectural tiers
          </div>
        </div>
      </div>
    </div>
  );
}
