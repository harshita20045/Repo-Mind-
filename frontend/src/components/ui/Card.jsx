import React from 'react';

// ─── Base Card ────────────────────────────────────────────────────────────────
export function Card({ children, className = '', hover = false, padding = true, ...props }) {
  return (
    <div
      className={`
        bg-surface border border-white/[0.07] rounded-xl shadow-card
        ${hover ? 'hover:bg-surfaceHighlight/50 hover:border-white/10 hover:shadow-card-hover cursor-pointer transition-all duration-200' : ''}
        ${padding ? 'p-5' : ''}
        ${className}
      `}
      {...props}
    >
      {children}
    </div>
  );
}

// ─── Metric Card ──────────────────────────────────────────────────────────────
export function MetricCard({ title, value, icon, color = 'primary', subtitle, trend, className = '' }) {
  const colorMap = {
    primary:  { icon: 'text-primary', bg: 'bg-primary/10', border: 'border-primary/15' },
    success:  { icon: 'text-success', bg: 'bg-success/10', border: 'border-success/15' },
    warning:  { icon: 'text-warning', bg: 'bg-warning/10', border: 'border-warning/15' },
    danger:   { icon: 'text-danger',  bg: 'bg-danger/10',  border: 'border-danger/15'  },
    accent:   { icon: 'text-accent',  bg: 'bg-accent/10',  border: 'border-accent/15'  },
    info:     { icon: 'text-info',    bg: 'bg-info/10',    border: 'border-info/15'    },
    muted:    { icon: 'text-text-secondary', bg: 'bg-white/5', border: 'border-white/10' },
  };
  const c = colorMap[color] || colorMap.primary;

  return (
    <div className={`bg-surface border border-white/[0.07] rounded-xl p-5 flex flex-col gap-4 shadow-card hover:border-white/10 transition-all duration-200 ${className}`}>
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">{title}</p>
        {icon && (
          <div className={`w-8 h-8 rounded-lg ${c.bg} border ${c.border} flex items-center justify-center ${c.icon}`}>
            {icon}
          </div>
        )}
      </div>
      <div>
        <div className="text-3xl font-bold text-text-primary tracking-tight leading-none">
          {value ?? '—'}
        </div>
        {subtitle && (
          <p className="text-xs text-text-muted mt-1.5">{subtitle}</p>
        )}
      </div>
      {trend !== undefined && (
        <div className={`text-xs font-medium ${trend >= 0 ? 'text-success' : 'text-danger'}`}>
          {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}% vs prev. period
        </div>
      )}
    </div>
  );
}

// ─── Section Card (with header) ───────────────────────────────────────────────
export function SectionCard({ title, subtitle, action, children, className = '', noPadding = false }) {
  return (
    <div className={`bg-surface border border-white/[0.07] rounded-xl shadow-card ${className}`}>
      {(title || action) && (
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.07]">
          <div>
            <h3 className="text-sm font-semibold text-text-primary">{title}</h3>
            {subtitle && <p className="text-xs text-text-muted mt-0.5">{subtitle}</p>}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      <div className={noPadding ? '' : 'p-5'}>
        {children}
      </div>
    </div>
  );
}
