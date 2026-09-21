import React from 'react';
import { RiskBadge } from '../ui/Badge';
import EmptyState from '../ui/EmptyState';

// ─── Risk vector card ──────────────────────────────────────────────────────────
function RiskVector({ label, level, description }) {
  const styles = {
    critical: { badge: 'bg-danger/10 text-danger border-danger/25', bar: 'bg-danger', width: '100%' },
    high:     { badge: 'bg-orange-500/10 text-orange-400 border-orange-400/25', bar: 'bg-orange-500', width: '75%' },
    medium:   { badge: 'bg-warning/10 text-warning border-warning/25', bar: 'bg-warning', width: '50%' },
    low:      { badge: 'bg-success/10 text-success border-success/25', bar: 'bg-success', width: '25%' },
    unknown:  { badge: 'bg-white/5 text-text-muted border-white/10', bar: 'bg-text-muted', width: '0%' },
  };
  const normalized = level?.toLowerCase() || 'unknown';
  const style = styles[normalized] || styles.unknown;

  return (
    <div className="bg-surfaceHighlight/30 border border-white/[0.07] rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-semibold text-text-secondary">{label}</span>
        <span className={`text-xs font-bold px-2 py-0.5 rounded border uppercase tracking-wide ${style.badge}`}>
          {level || 'Unknown'}
        </span>
      </div>
      <div className="h-1.5 bg-white/5 rounded-full overflow-hidden mb-2">
        <div
          className={`h-full rounded-full ${style.bar} transition-all duration-1000`}
          style={{ width: style.width }}
          role="presentation"
        />
      </div>
      <p className="text-xs text-text-muted leading-relaxed">{description}</p>
    </div>
  );
}

// ─── Risk Assessment ───────────────────────────────────────────────────────────
export default function RiskAssessment({ riskData }) {
  if (!riskData) {
    return (
      <EmptyState
        icon="analytics"
        title="No risk assessment data"
        description="Risk assessment data will appear here after the review run completes."
        className="py-12"
      />
    );
  }

  const {
    risk_score,
    security_risk_level,
    architecture_risk_level,
    test_gap_level,
    blast_radius_modules,
    explanation,
  } = riskData;

  const isHigh = risk_score > 70;
  const isMed = risk_score > 40;
  const riskLevel = isHigh ? 'high' : isMed ? 'medium' : risk_score > 0 ? 'low' : null;
  const scoreColor = isHigh ? 'text-danger' : isMed ? 'text-warning' : risk_score > 0 ? 'text-success' : 'text-text-muted';
  const trackColor = isHigh ? 'text-danger' : isMed ? 'text-warning' : risk_score > 0 ? 'text-success' : 'text-text-muted';

  // SVG ring
  const r = 52;
  const circ = 2 * Math.PI * r;
  const filled = circ - (circ * (risk_score || 0)) / 100;

  return (
    <div className="space-y-6 animate-fade-in">

      {/* Overall risk header */}
      <div className="flex flex-col md:flex-row gap-6 items-center bg-surfaceHighlight/20 border border-white/[0.06] rounded-xl p-6">
        {/* Ring gauge */}
        <div className="relative flex-shrink-0">
          <svg className="w-32 h-32 -rotate-90" viewBox="0 0 120 120" aria-hidden="true">
            <circle cx="60" cy="60" r={r} fill="none" stroke="currentColor" strokeWidth="10" className="text-white/5" />
            <circle
              cx="60" cy="60" r={r}
              fill="none" stroke="currentColor" strokeWidth="10"
              strokeDasharray={circ}
              strokeDashoffset={filled}
              strokeLinecap="round"
              className={`${trackColor} transition-all duration-1200`}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`text-4xl font-bold tabular-nums ${scoreColor}`}>{risk_score ?? '—'}</span>
            <span className="text-xs text-text-muted uppercase tracking-wider">/ 100</span>
          </div>
        </div>

        {/* Summary text */}
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-3">
            <h2 className="text-lg font-bold text-text-primary">Overall Risk Assessment</h2>
            {riskLevel && <RiskBadge level={riskLevel} />}
          </div>
          <p className="text-sm text-text-secondary leading-relaxed">
            {explanation || 'The risk engine analyzed structural changes, security implications, and test coverage gaps to produce this aggregate risk score.'}
          </p>
        </div>
      </div>

      {/* Risk vectors */}
      <div>
        <h3 className="text-sm font-semibold text-text-secondary mb-3 uppercase tracking-wider">Risk Vectors</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <RiskVector
            label="Security"
            level={security_risk_level}
            description="Derived from secrets exposure, authentication changes, and injection vulnerabilities."
          />
          <RiskVector
            label="Architecture"
            level={architecture_risk_level}
            description="Assessed from core structural modifications or changes to deep dependencies."
          />
          <RiskVector
            label="Test Coverage"
            level={test_gap_level}
            description="Measures the absence of tests accompanying new critical logic changes."
          />
        </div>
      </div>

      {/* Blast radius */}
      <div>
        <h3 className="text-sm font-semibold text-text-secondary mb-3 uppercase tracking-wider">Blast Radius</h3>
        <div className="bg-surfaceHighlight/20 border border-white/[0.06] rounded-xl p-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center text-accent flex-shrink-0">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <circle cx="12" cy="12" r="10" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-semibold text-text-primary">Impacted Modules</p>
              <p className="text-xs text-text-muted">Files and services potentially affected by this PR's changes</p>
            </div>
          </div>
          {blast_radius_modules && blast_radius_modules.length > 0 ? (
            <div className="flex flex-wrap gap-2 mt-1">
              {blast_radius_modules.map((mod, i) => (
                <span
                  key={i}
                  className="font-mono text-xs text-text-secondary bg-white/5 border border-white/[0.08] px-2.5 py-1 rounded-md"
                >
                  {mod}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-xs text-text-muted italic">No significant multi-module blast radius detected.</p>
          )}
        </div>
      </div>
    </div>
  );
}
