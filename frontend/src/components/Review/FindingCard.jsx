import React, { useState } from 'react';
import { SeverityBadge } from '../ui/Badge';

function LifecycleBadge({ status }) {
  const styles = {
    new: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    persistent: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
    resolved: 'text-text-muted bg-white/5 border-white/10 line-through',
    reopened: 'text-rose-400 bg-rose-500/10 border-rose-500/20 animate-pulse',
  };
  const normalized = status?.toLowerCase() || 'new';
  const style = styles[normalized] || styles.new;
  const label = normalized.charAt(0).toUpperCase() + normalized.slice(1);

  return (
    <span className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider ${style}`}>
      {label}
    </span>
  );
}

function EvidenceStatus({ status }) {
  const styles = {
    supported: 'text-success',
    unverified: 'text-warning',
    contradicted: 'text-danger',
  };
  const icons = {
    supported: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />,
    unverified: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />,
    contradicted: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />,
  };
  const normalized = status?.toLowerCase() || 'unverified';
  const style = styles[normalized] || styles.unverified;
  const icon = icons[normalized] || icons.unverified;
  const label = normalized.charAt(0).toUpperCase() + normalized.slice(1);

  return (
    <div className={`flex items-center gap-1.5 text-[12px] font-medium ${style}`}>
      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        {icon}
      </svg>
      {label}
    </div>
  );
}

export default function FindingCard({ finding }) {
  const [expanded, setExpanded] = useState(true);

  const sev = finding.severity?.toLowerCase() || 'info';
  const leftColors = {
    critical: 'bg-danger',
    high: 'bg-orange-500',
    medium: 'bg-warning',
    low: 'bg-success',
    info: 'bg-info',
  };
  const leftColor = leftColors[sev] || 'bg-border';

  // 8 Multi-Stage categories + legacy fallback
  const categoryColors = {
    syntax: 'text-cyan-400 bg-cyan-500/10 border-cyan-400/20',
    security: 'text-danger bg-danger/10 border-danger/20',
    quality: 'text-primary bg-primary/10 border-primary/20',
    conventions: 'text-emerald-400 bg-emerald-500/10 border-emerald-400/20',
    architecture: 'text-indigo-400 bg-indigo-500/10 border-indigo-400/20',
    api_contract: 'text-amber-400 bg-amber-500/10 border-amber-400/20',
    dependencies: 'text-rose-400 bg-rose-500/10 border-rose-400/20',
    testing: 'text-purple-400 bg-purple-500/10 border-purple-400/20',
    // Legacy mappings
    standards_violation: 'text-emerald-400 bg-emerald-500/10 border-emerald-400/20',
    style: 'text-primary bg-primary/10 border-primary/20',
    performance: 'text-accent bg-accent/10 border-accent/20',
    bug: 'text-warning bg-warning/10 border-warning/20',
  };
  const catColor = categoryColors[finding.type?.toLowerCase()] || 'text-text-muted bg-surfaceHighlight border-white/5';

  return (
    <div className="relative flex flex-col bg-surface border border-border rounded-lg shadow-sm mb-4 transition-colors">
      <div className={`absolute left-0 top-0 bottom-0 w-1 rounded-l-lg ${leftColor}`} aria-hidden="true" />

      <div className="pl-5 p-4 flex flex-col gap-3">
        {/* Header row */}
        <div className="flex items-start justify-between gap-4">
          <button
            onClick={() => setExpanded(v => !v)}
            className="flex-1 text-left flex items-start gap-3 group"
            aria-expanded={expanded}
          >
            <div className={`mt-0.5 transition-transform ${expanded ? 'rotate-90' : ''}`}>
              <svg className="w-4 h-4 text-text-muted group-hover:text-text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </div>
            <div>
              <h4 className="text-[14px] font-medium text-text-primary group-hover:text-primary transition-colors leading-snug">
                {finding.title}
              </h4>
              {(finding.file || finding.line) && (
                <div className="font-mono text-[11px] text-text-muted mt-1.5 flex items-center gap-1.5">
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                  <span>{finding.file}</span>
                  {finding.line && <span className="px-1 bg-surfaceHighlight border border-border rounded">L{finding.line}</span>}
                </div>
              )}
            </div>
          </button>
          <div className="flex items-center gap-2 flex-shrink-0 flex-wrap justify-end">
            {finding.lifecycle_status && (
              <LifecycleBadge status={finding.lifecycle_status} />
            )}
            {finding.type && (
              <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${catColor}`}>
                {finding.type.replace('_', ' ')}
              </span>
            )}
            <SeverityBadge severity={sev} />
          </div>
        </div>

        {/* Details Panel */}
        {expanded && (
          <div className="mt-2 pl-7 space-y-4 animate-fade-in pr-2">

            {/* The Problem */}
            <div className="space-y-1.5">
              <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider">Problem detected</span>
              <p className="text-[13px] text-text-secondary leading-relaxed bg-surfaceHighlight/50 border border-border/50 rounded-md p-3">
                {finding.explanation}
              </p>
            </div>

            {/* Recommendation */}
            {finding.recommendation && (
              <div className="space-y-1.5">
                <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider">Suggested Action</span>
                <p className="text-[13px] text-text-primary leading-relaxed bg-primary/5 border border-primary/20 rounded-md p-3">
                  {finding.recommendation}
                </p>
              </div>
            )}

            {/* Evidence & Rules - Grounding */}
            <div className="flex flex-col gap-3 pt-3 border-t border-border">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider">Analysis Grounding</span>
                {finding.evidence_status && (
                  <EvidenceStatus status={finding.evidence_status} />
                )}
              </div>

              {finding.rule_source ? (
                <div className="flex items-start gap-3 bg-surface border border-border rounded-md p-3">
                  <div className="mt-0.5 flex-shrink-0">
                    <svg className="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                    </svg>
                  </div>
                  <div className="w-full">
                    <div className="text-[12px] font-medium text-text-primary mb-1">Code Evidence & Grounded Rule</div>
                    <pre className="text-[12px] text-text-secondary font-mono bg-surfaceHighlight p-2 rounded border border-border whitespace-pre-wrap overflow-x-auto">
                      {finding.rule_source}
                    </pre>
                  </div>
                </div>
              ) : (
                <div className="text-[12px] text-text-muted italic">
                  No specific repository rules found to cite. General best practices applied.
                </div>
              )}
            </div> 
          </div>
        )}
      </div>
    </div>
  );
}

