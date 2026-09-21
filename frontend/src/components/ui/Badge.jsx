import React from 'react';

// ─── Risk Badge ──────────────────────────────────────────────────────────────
const RISK_STYLES = {
  low:      'bg-success/10 text-success border-success/20',
  medium:   'bg-warning/10 text-warning border-warning/20',
  high:     'bg-orange-500/10 text-orange-400 border-orange-500/20',
  critical: 'bg-danger/10 text-danger border-danger/20',
};

export function RiskBadge({ level, className = '' }) {
  const normalized = level?.toLowerCase() || 'unknown';
  const style = RISK_STYLES[normalized] || 'bg-white/5 text-text-secondary border-white/10';
  return (
    <span
      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wide border ${style} ${className}`}
      role="status"
      aria-label={`Risk level: ${normalized}`}
    >
      <span
        className="w-1.5 h-1.5 rounded-full bg-current opacity-80 flex-shrink-0"
        aria-hidden="true"
      />
      {normalized}
    </span>
  );
}

// ─── Severity Badge ───────────────────────────────────────────────────────────
const SEVERITY_STYLES = {
  critical: 'bg-danger/10 text-danger border-danger/25',
  high:     'bg-orange-500/10 text-orange-400 border-orange-400/25',
  medium:   'bg-warning/10 text-warning border-warning/25',
  low:      'bg-success/10 text-success border-success/25',
  info:     'bg-info/10 text-info border-info/25',
};

export function SeverityBadge({ severity, className = '' }) {
  const normalized = severity?.toLowerCase() || 'info';
  const style = SEVERITY_STYLES[normalized] || 'bg-white/5 text-text-secondary border-white/10';
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-2xs font-bold uppercase tracking-wider border ${style} ${className}`}
      role="status"
    >
      {normalized}
    </span>
  );
}

// ─── Status Badge ─────────────────────────────────────────────────────────────
const STATUS_STYLES = {
  // Repository indexing
  indexed:    'bg-success/10 text-success border-success/20',
  indexing:   'bg-info/10 text-info border-info/20',
  failed:     'bg-danger/10 text-danger border-danger/20',
  unindexed:  'bg-white/5 text-text-secondary border-white/10',
  connected:  'bg-primary/10 text-primary border-primary/20',
  // PR state
  open:       'bg-success/10 text-success border-success/20',
  closed:     'bg-white/5 text-text-secondary border-white/10',
  merged:     'bg-accent/10 text-accent border-accent/20',
  // Review state
  completed:  'bg-success/10 text-success border-success/20',
  running:    'bg-info/10 text-info border-info/20',
  pending:    'bg-warning/10 text-warning border-warning/20',
  cancelled:  'bg-white/5 text-text-secondary border-white/10',
  // Decision
  approved:   'bg-success/10 text-success border-success/20',
  rejected:   'bg-danger/10 text-danger border-danger/20',
  // Evidence
  supported:  'bg-success/10 text-success border-success/20',
  unverified: 'bg-warning/10 text-warning border-warning/20',
  contradicted: 'bg-danger/10 text-danger border-danger/20',
};

export function StatusBadge({ status, label, className = '' }) {
  const normalized = status?.toLowerCase() || '';
  const style = STATUS_STYLES[normalized] || 'bg-white/5 text-text-secondary border-white/10';
  const display = label || normalized || '—';
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${style} ${className}`}
    >
      {display}
    </span>
  );
}

// ─── Generic Badge ────────────────────────────────────────────────────────────
export function Badge({ children, variant = 'default', className = '' }) {
  const variants = {
    default:  'bg-white/5 text-text-secondary border-white/10',
    primary:  'bg-primary/10 text-primary border-primary/20',
    accent:   'bg-accent/10 text-accent border-accent/20',
    success:  'bg-success/10 text-success border-success/20',
    warning:  'bg-warning/10 text-warning border-warning/20',
    danger:   'bg-danger/10 text-danger border-danger/20',
    info:     'bg-info/10 text-info border-info/20',
  };
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold border ${variants[variant] || variants.default} ${className}`}
    >
      {children}
    </span>
  );
}
