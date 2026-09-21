import React from 'react';
import FindingCard from './FindingCard';
import EmptyState from '../ui/EmptyState';

// Severity order for sorting
const SEV_ORDER = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };

export default function FindingList({ findings }) {
  if (!findings || findings.length === 0) {
    return (
      <EmptyState
        icon="success"
        variant="success"
        title="No issues found"
        description="This pull request looks great! The AI review found no significant issues."
        className="py-16"
      />
    );
  }

  const sorted = [...findings].sort((a, b) => {
    const aO = SEV_ORDER[a.severity?.toLowerCase()] ?? 5;
    const bO = SEV_ORDER[b.severity?.toLowerCase()] ?? 5;
    return aO - bO;
  });

  // Count by severity
  const counts = findings.reduce((acc, f) => {
    const s = f.severity?.toLowerCase() || 'info';
    acc[s] = (acc[s] || 0) + 1;
    return acc;
  }, {});

  const SEV_COLORS = {
    critical: 'text-danger bg-danger/10 border-danger/20',
    high:     'text-orange-400 bg-orange-500/10 border-orange-400/20',
    medium:   'text-warning bg-warning/10 border-warning/20',
    low:      'text-success bg-success/10 border-success/20',
    info:     'text-text-muted bg-white/5 border-white/10',
  };

  return (
    <div className="space-y-4">
      {/* Header + severity summary */}
      <div className="flex items-center justify-between flex-wrap gap-3 mb-4">
        <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
          Findings
          <span className="text-xs font-bold px-2 py-0.5 bg-white/5 border border-white/10 rounded text-text-muted">
            {findings.length}
          </span>
        </h3>
        {/* Severity pill summary */}
        <div className="flex items-center gap-1.5 flex-wrap">
          {Object.entries(SEV_ORDER)
            .filter(([sev]) => counts[sev])
            .map(([sev]) => (
              <span
                key={sev}
                className={`text-2xs font-bold px-2 py-0.5 rounded border capitalize ${SEV_COLORS[sev] || SEV_COLORS.info}`}
              >
                {counts[sev]} {sev}
              </span>
            ))
          }
        </div>
      </div>

      {/* Findings */}
      <div>
        {sorted.map(finding => (
          <FindingCard key={finding.id} finding={finding} />
        ))}
      </div>
    </div>
  );
}
