import React, { useState } from 'react';
import { SeverityBadge } from '../ui/Badge';

// ─── Evidence status ───────────────────────────────────────────────────────────
function EvidenceStatus({ status }) {
  const styles = {
    supported:    'bg-success/10 text-success border-success/20',
    unverified:   'bg-warning/10 text-warning border-warning/20',
    contradicted: 'bg-danger/10 text-danger border-danger/20',
  };
  const icons = {
    supported:    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />,
    unverified:   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />,
    contradicted: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />,
  };
  const normalized = status?.toLowerCase() || 'unverified';
  const style = styles[normalized] || styles.unverified;
  const icon = icons[normalized] || icons.unverified;
  const label = normalized.charAt(0).toUpperCase() + normalized.slice(1);

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs font-bold rounded border uppercase tracking-wider ${style}`}>
      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
        {icon}
      </svg>
      {label}
    </span>
  );
}

// ─── Finding Card ──────────────────────────────────────────────────────────────
export default function FindingCard({ finding }) {
  const [expanded, setExpanded] = useState(true);

  const sev = finding.severity?.toLowerCase() || 'info';
  const leftColors = {
    critical: 'bg-danger',
    high:     'bg-orange-500',
    medium:   'bg-warning',
    low:      'bg-success',
    info:     'bg-info',
  };
  const leftColor = leftColors[sev] || 'bg-text-muted';

  const categoryColors = {
    security:     'text-danger',
    bug:          'text-warning',
    performance:  'text-accent',
    style:        'text-primary',
    architecture: 'text-info',
  };
  const catColor = categoryColors[finding.type?.toLowerCase()] || 'text-text-muted';

  return (
    <div className="relative flex overflow-hidden bg-surface border border-white/[0.07] rounded-xl shadow-card mb-3 hover:border-white/10 transition-colors">
      {/* Left severity strip */}
      <div className={`w-1 flex-shrink-0 ${leftColor}`} aria-hidden="true" />

      <div className="flex-1 p-4 min-w-0">
        {/* Header row */}
        <div className="flex items-start justify-between gap-3 mb-1">
          <button
            onClick={() => setExpanded(v => !v)}
            className="flex-1 text-left group"
            aria-expanded={expanded}
          >
            <h4 className="text-sm font-semibold text-text-primary group-hover:text-primary transition-colors leading-snug">
              {finding.title}
            </h4>
          </button>
          <div className="flex items-center gap-1.5 flex-shrink-0">
            <SeverityBadge severity={sev} />
            {finding.type && (
              <span className={`text-2xs font-bold uppercase tracking-wider px-2 py-0.5 rounded border border-white/[0.08] bg-white/5 ${catColor}`}>
                {finding.type}
              </span>
            )}
          </div>
        </div>

        {/* File + line */}
        {(finding.file || finding.line) && (
          <div className="font-mono text-xs text-text-muted bg-surfaceHighlight/50 border border-white/[0.07] px-2.5 py-1 rounded inline-block mb-3">
            {finding.file || 'Unknown file'}
            {finding.line && <span className="text-text-muted/60">:{finding.line}</span>}
          </div>
        )}

        {/* Collapsible body */}
        {expanded && (
          <div className="space-y-3 animate-fade-in">
            {/* Problem */}
            <div className="bg-surfaceHighlight/20 border border-white/[0.05] rounded-lg p-3 text-xs">
              <span className="block font-semibold text-text-secondary mb-1.5 uppercase tracking-wider text-2xs">Problem</span>
              <p className="text-text-secondary leading-relaxed">{finding.explanation}</p>
            </div>

            {/* Recommendation */}
            {finding.recommendation && (
              <div className="bg-primary/5 border border-primary/15 rounded-lg p-3 text-xs">
                <span className="block font-semibold text-primary mb-1.5 uppercase tracking-wider text-2xs">Recommendation</span>
                <p className="text-text-secondary leading-relaxed">{finding.recommendation}</p>
              </div>
            )}

            {/* Footer */}
            <div className="flex items-center justify-between pt-1">
              <div className="flex items-center gap-3">
                {finding.rule_source && (
                  <span className="text-xs text-text-muted flex items-center gap-1">
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {finding.rule_source}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                {finding.evidence_status && (
                  <EvidenceStatus status={finding.evidence_status} />
                )}
                {finding.is_grounded && (
                  <span className="inline-flex items-center gap-1 text-success bg-success/10 border border-success/20 px-2 py-0.5 rounded text-2xs font-bold uppercase tracking-wider">
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5} aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Grounded
                  </span>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
