import React, { useState } from 'react';
import FindingCard from './FindingCard';
import EmptyState from '../ui/EmptyState';

// Severity order for sorting
const SEV_ORDER = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };

const STAGES = [
  { id: 'all', label: 'All Stages' },
  { id: 'security', label: 'Security' },
  { id: 'architecture', label: 'Architecture' },
  { id: 'quality', label: 'Quality' },
  { id: 'conventions', label: 'Conventions' },
  { id: 'api_contract', label: 'API Contract' },
  { id: 'dependencies', label: 'Dependencies' },
  { id: 'testing', label: 'Testing' },
  { id: 'syntax', label: 'Syntax' },
];

export default function FindingList({ findings }) {
  const [selectedStage, setSelectedStage] = useState('all');
  const [selectedLifecycle, setSelectedLifecycle] = useState('all');

  if (!findings || findings.length === 0) {
    return (
      <EmptyState
        icon="success"
        variant="success"
        title="No issues found"
        description="This pull request looks great! The evidence-backed review found no significant issues."
        className="py-16"
      />
    );
  }

  // Filter findings based on selected stage and lifecycle
  const filtered = findings.filter(f => {
    if (selectedStage !== 'all') {
      const cat = f.type?.toLowerCase();
      // Match direct or normalized category
      if (selectedStage === 'quality' && ['quality', 'style', 'performance', 'general', 'bug'].includes(cat)) {
        // match
      } else if (selectedStage === 'conventions' && ['conventions', 'standards_violation'].includes(cat)) {
        // match
      } else if (cat !== selectedStage) {
        return false;
      }
    }
    if (selectedLifecycle !== 'all') {
      const lc = f.lifecycle_status?.toLowerCase() || 'new';
      if (lc !== selectedLifecycle) return false;
    }
    return true;
  });

  const sorted = [...filtered].sort((a, b) => {
    const aO = SEV_ORDER[a.severity?.toLowerCase()] ?? 5;
    const bO = SEV_ORDER[b.severity?.toLowerCase()] ?? 5;
    return aO - bO;
  });

  // Count by severity across all findings
  const counts = findings.reduce((acc, f) => {
    const s = f.severity?.toLowerCase() || 'info';
    acc[s] = (acc[s] || 0) + 1;
    return acc;
  }, {});

  const SEV_COLORS = {
    critical: 'text-danger bg-danger/10 border-danger/20',
    high: 'text-orange-400 bg-orange-500/10 border-orange-400/20',
    medium: 'text-warning bg-warning/10 border-warning/20',
    low: 'text-success bg-success/10 border-success/20',
    info: 'text-text-muted bg-white/5 border-white/10',
  };

  return (
    <div className="space-y-4">
      {/* Header + severity summary */}
      <div className="flex items-center justify-between flex-wrap gap-3 mb-2">
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

      {/* 8-Stage Category Filters */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-2 border-b border-border/60">
        {STAGES.map(stage => {
          const isSelected = selectedStage === stage.id;
          return (
            <button
              key={stage.id}
              onClick={() => setSelectedStage(stage.id)}
              className={`text-xs px-2.5 py-1 rounded-md font-medium whitespace-nowrap transition-colors border ${
                isSelected
                  ? 'bg-primary/10 text-primary border-primary/30'
                  : 'bg-surfaceHighlight text-text-muted border-border hover:text-text-primary'
              }`}
            >
              {stage.label}
            </button>
          );
        })}
      </div>

      {/* Findings List or Filter Empty State */}
      {sorted.length === 0 ? (
        <div className="py-8 text-center text-xs text-text-muted">
          No findings match the selected stage filter ({selectedStage}).
          <button
            onClick={() => { setSelectedStage('all'); setSelectedLifecycle('all'); }}
            className="ml-2 text-primary underline"
          >
            Reset Filters
          </button>
        </div>
      ) : (
        <div>
          {sorted.map(finding => (
            <FindingCard key={finding.id} finding={finding} />
          ))}
        </div>
      )}
    </div>
  );
}
