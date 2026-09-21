import React from 'react';
import { useOutletContext } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../lib/api';
import { MetricCard } from '../components/ui/Card';
import { DashboardSkeleton } from '../components/ui/LoadingSkeleton';
import EmptyState from '../components/ui/EmptyState';

// ─── Inline icons ──────────────────────────────────────────────────────────────
const IconPRs = (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <circle cx="6" cy="6" r="3" /><circle cx="6" cy="18" r="3" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M6 9v6M13 6h3a2 2 0 012 2v7a2 2 0 01-2 2h-3" />
    <circle cx="18" cy="6" r="3" />
  </svg>
);
const IconRisk = (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
  </svg>
);
const IconCritical = (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);
const IconSecurity = (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
  </svg>
);

// ─── Severity bar ──────────────────────────────────────────────────────────────
const SEV_CONFIG = {
  critical: { color: 'bg-danger',       label: 'Critical' },
  high:     { color: 'bg-orange-500',   label: 'High' },
  medium:   { color: 'bg-warning',      label: 'Medium' },
  low:      { color: 'bg-success',      label: 'Low' },
  info:     { color: 'bg-text-muted',   label: 'Info' },
};

function SeverityBar({ severity, count, max }) {
  const config = SEV_CONFIG[severity] || { color: 'bg-text-muted', label: severity };
  const pct = max > 0 ? Math.max(4, Math.round((count / max) * 100)) : 0;
  return (
    <div className="flex items-center gap-3 group">
      <div className="w-16 text-xs font-medium text-text-muted capitalize">{config.label}</div>
      <div className="flex-1 h-2 bg-white/5 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${config.color} transition-all duration-700`}
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={count}
          aria-valuemin={0}
          aria-valuemax={max}
          aria-label={`${config.label}: ${count}`}
        />
      </div>
      <div className="w-8 text-right text-xs font-bold text-text-primary tabular-nums">{count}</div>
    </div>
  );
}

// ─── Category item ─────────────────────────────────────────────────────────────
function CategoryRow({ category, count, max }) {
  const pct = max > 0 ? Math.max(4, Math.round((count / max) * 100)) : 0;
  return (
    <div className="flex items-center gap-3">
      <div className="w-28 text-xs font-medium text-text-muted capitalize truncate" title={category}>
        {category}
      </div>
      <div className="flex-1 h-2 bg-white/5 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full bg-accent transition-all duration-700"
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={count}
          aria-valuemin={0}
          aria-valuemax={max}
        />
      </div>
      <div className="w-8 text-right text-xs font-bold text-text-primary tabular-nums">{count}</div>
    </div>
  );
}

// ─── Lifecycle card ────────────────────────────────────────────────────────────
function LifecycleCard({ label, value, description, color }) {
  const colors = {
    primary: 'text-primary border-primary/15 bg-primary/5',
    warning: 'text-warning border-warning/15 bg-warning/5',
    success: 'text-success border-success/15 bg-success/5',
  };
  return (
    <div className={`flex-1 p-4 rounded-xl border text-center ${colors[color] || colors.primary}`}>
      <div className="text-xs font-semibold uppercase tracking-wider mb-2 opacity-80">{label}</div>
      <div className="text-3xl font-bold tabular-nums leading-none mb-2">{value ?? 0}</div>
      <p className="text-xs opacity-70 leading-snug">{description}</p>
    </div>
  );
}

// ─── Dashboard Page ────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const { memberships } = useOutletContext();
  const orgId = memberships?.[0]?.organization_id;

  const { data: analytics, isLoading, error } = useQuery({
    queryKey: ['orgAnalytics', orgId],
    queryFn: () => analyticsApi.getOrgAnalytics(orgId, 30),
    enabled: !!orgId,
  });

  if (isLoading) return <DashboardSkeleton />;

  if (error) {
    return (
      <EmptyState
        icon="analytics"
        title="Failed to load analytics"
        description={error.message || 'An unexpected error occurred loading dashboard data.'}
        className="min-h-[400px]"
      />
    );
  }

  if (!analytics && !isLoading) {
    return (
      <EmptyState
        icon="analytics"
        title="No analytics data"
        description="Analytics will appear here once your organization has completed PR reviews."
        className="min-h-[400px]"
      />
    );
  }

  const severityData = analytics?.findings_by_severity || {};
  const severityKeys = ['critical', 'high', 'medium', 'low', 'info'];
  const maxSeverity = Math.max(...severityKeys.map(k => severityData[k] || 0), 1);

  const categoryData = analytics?.findings_by_category || {};
  const categoryEntries = Object.entries(categoryData).sort((a, b) => b[1] - a[1]).slice(0, 6);
  const maxCategory = Math.max(...categoryEntries.map(([, v]) => v), 1);

  const avgRisk = analytics?.average_risk_score ?? 0;
  const riskColor = avgRisk > 70 ? 'danger' : avgRisk > 40 ? 'warning' : 'success';

  return (
    <div className="space-y-6 animate-slide-up">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary tracking-tight">Dashboard</h1>
        <p className="text-sm text-text-muted mt-1">
          Engineering intelligence overview · Last 30 days
        </p>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="PRs Reviewed"
          value={analytics?.total_reviews ?? 0}
          icon={IconPRs}
          color="primary"
          subtitle="Pull requests analyzed this period"
        />
        <MetricCard
          title="Average Risk Score"
          value={`${avgRisk}`}
          icon={IconRisk}
          color={riskColor}
          subtitle="0 = low risk · 100 = critical risk"
        />
        <MetricCard
          title="Critical Findings"
          value={severityData.critical ?? 0}
          icon={IconCritical}
          color="danger"
          subtitle="Require immediate attention"
        />
        <MetricCard
          title="Security Issues"
          value={analytics?.findings_by_category?.security ?? 0}
          icon={IconSecurity}
          color="accent"
          subtitle="Security-category findings"
        />
      </div>

      {/* Findings breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Severity distribution */}
        <div className="bg-surface border border-white/[0.07] rounded-xl p-5">
          <div className="mb-5">
            <h2 className="text-sm font-semibold text-text-primary">Findings by Severity</h2>
            <p className="text-xs text-text-muted mt-0.5">Distribution of identified issues across severity levels</p>
          </div>
          {severityKeys.every(k => !severityData[k]) ? (
            <EmptyState
              title="No findings"
              description="No findings detected in the last 30 days."
              icon="success"
              variant="success"
              className="py-8"
            />
          ) : (
            <div className="space-y-3.5">
              {severityKeys.map(sev => (
                <SeverityBar
                  key={sev}
                  severity={sev}
                  count={severityData[sev] || 0}
                  max={maxSeverity}
                />
              ))}
            </div>
          )}
        </div>

        {/* Category distribution */}
        <div className="bg-surface border border-white/[0.07] rounded-xl p-5">
          <div className="mb-5">
            <h2 className="text-sm font-semibold text-text-primary">Findings by Category</h2>
            <p className="text-xs text-text-muted mt-0.5">Top categories from AI review findings</p>
          </div>
          {categoryEntries.length === 0 ? (
            <EmptyState
              title="No categorized findings"
              description="Category breakdown will appear after PRs are reviewed."
              icon="analytics"
              className="py-8"
            />
          ) : (
            <div className="space-y-3.5">
              {categoryEntries.map(([cat, count]) => (
                <CategoryRow key={cat} category={cat} count={count} max={maxCategory} />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Resolution lifecycle */}
      <div className="bg-surface border border-white/[0.07] rounded-xl p-5">
        <div className="mb-5">
          <h2 className="text-sm font-semibold text-text-primary">Resolution Lifecycle</h2>
          <p className="text-xs text-text-muted mt-0.5">Finding lifecycle states across all reviewed PRs this period</p>
        </div>
        <div className="flex flex-col sm:flex-row gap-3">
          <LifecycleCard
            label="New"
            value={analytics?.findings_by_lifecycle?.new}
            description="Findings introduced in this period"
            color="primary"
          />
          <LifecycleCard
            label="Persistent"
            value={analytics?.findings_by_lifecycle?.persistent}
            description="Unresolved across multiple reviews"
            color="warning"
          />
          <LifecycleCard
            label="Resolved"
            value={analytics?.findings_by_lifecycle?.resolved}
            description="Issues fixed by the engineering team"
            color="success"
          />
        </div>
      </div>
    </div>
  );
}
