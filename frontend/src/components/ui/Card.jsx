import React from 'react';

// ─── Base Card ────────────────────────────────────────────────────────────────
export function Card({ children, className = '', hover = false, padding = true, ...props }) {
  return (
    <div
      className={`
        bg-surface border border-border rounded-lg shadow-sm
        ${hover ? 'hover:bg-surfaceHighlight hover:border-white/10 hover:shadow-card-hover cursor-pointer transition-all duration-200' : ''}
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
    primary:  { icon: 'text-primary', bg: 'bg-primary/10', border: 'border-primary/20' },
    success:  { icon: 'text-success', bg: 'bg-success/10', border: 'border-success/20' },
    warning:  { icon: 'text-warning', bg: 'bg-warning/10', border: 'border-warning/20' },
    danger:   { icon: 'text-danger',  bg: 'bg-danger/10',  border: 'border-danger/20'  },
    accent:   { icon: 'text-accent',  bg: 'bg-accent/10',  border: 'border-accent/20'  },
    info:     { icon: 'text-info',    bg: 'bg-info/10',    border: 'border-info/20'    },
    muted:    { icon: 'text-text-muted', bg: 'bg-surfaceHighlight', border: 'border-border' },
  };
  const c = colorMap[color] || colorMap.primary;

  return (
    <div className={`bg-surface border border-border rounded-lg p-5 flex flex-col justify-between h-full hover:border-white/10 transition-all duration-150 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-[13px] font-medium text-text-secondary">{title}</h3>
        {icon && (
          <div className={`w-8 h-8 rounded-md ${c.bg} border ${c.border} flex items-center justify-center ${c.icon}`}>
            {icon}
          </div>
        )}
      </div>
      <div>
        <div className="text-2xl font-semibold text-text-primary tabular-nums tracking-tight">
          {value ?? '—'}
        </div>
        {subtitle && (
          <p className="text-[13px] text-text-muted mt-1">{subtitle}</p>
        )}
        {trend !== undefined && (
          <div className={`text-[12px] font-medium mt-1 ${trend >= 0 ? 'text-success' : 'text-danger'}`}>
            {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}% vs prev
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Section Card (with header) ───────────────────────────────────────────────
export function SectionCard({ title, subtitle, action, children, className = '', noPadding = false }) {
  return (
    <div className={`bg-surface border border-border rounded-lg ${className}`}>
      {(title || action) && (
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-border">
          <div>
            <h3 className="text-sm font-medium text-text-primary">{title}</h3>
            {subtitle && <p className="text-[13px] text-text-muted mt-0.5">{subtitle}</p>}
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
