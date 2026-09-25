import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../lib/api';
import { MetricCard } from '../components/ui/Card';
import { DashboardSkeleton } from '../components/ui/LoadingSkeleton';
import EmptyState from '../components/ui/EmptyState';

// Reusable bar chart row
function BarRow({ label, value, max, color = 'bg-primary', textColor = '' }) {
  const pct = max > 0 ? Math.max(4, Math.round((value / max) * 100)) : 0;
  return (
    <div className="flex items-center gap-3">
      <div className="w-28 text-xs font-medium text-text-muted capitalize truncate" title={label}>{label}</div>
      <div className="flex-1 h-2 bg-white/5 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${color} transition-all duration-700`}
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={max}
        />
      </div>
      <div className={`w-10 text-right text-xs font-bold tabular-nums ${textColor || 'text-text-primary'}`}>{value}</div>
    </div>
  );
}

const SEV_COLORS = {
  critical: 'bg-danger',
  high:     'bg-orange-500',
  medium:   'bg-warning',
  low:      'bg-success',
  info:     'bg-text-muted',
};

const SEV_TEXT = {
  critical: 'text-danger',
  high:     'text-orange-400',
  medium:   'text-warning',
  low:      'text-success',
  info:     'text-text-muted',
};

// Icons
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
const IconFindings = (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
  </svg>
);
const IconResolved = (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const PERIODS = [
  { label: '7 days', value: 7 },
  { label: '30 days', value: 30 },
  { label: '90 days', value: 90 },
];

export default function AnalyticsPage() {
  const { memberships } = useOutletContext();
  const orgId = memberships?.[0]?.organization_id;
  const [period, setPeriod] = useState(30);

  const { data: analytics, isLoading, error } = useQuery({
    queryKey: ['orgAnalytics', orgId, period],
    queryFn: () => analyticsApi.getOrgAnalytics(orgId, period),
    enabled: !!orgId,
  });

  if (isLoading) return <DashboardSkeleton />;

  if (error) {
    return (
      <EmptyState
        icon="analytics"
        title="Failed to load analytics"
        description={error.message || 'An unexpected error occurred. Please try again.'}
        className="min-h-[400px]"
      />
    );
  }

  if (!analytics) {
    return (
      <EmptyState
        icon="analytics"
        title="No data available"
        description="Analytics data will appear here once your team starts completing PR reviews."
        className="min-h-[400px]"
      />
    );
  }

  const sev = analytics.findings_by_severity || {};
  const cat = analytics.findings_by_category || {};
  const life = analytics.findings_by_lifecycle || {};

  const maxSev = Math.max(...Object.values(sev).filter(Number.isFinite), 1);
  const catEntries = Object.entries(cat).sort((a, b) => b[1] - a[1]).slice(0, 8);
  const maxCat = Math.max(...catEntries.map(([, v]) => v), 1);

  const totalFindings = Object.values(sev).reduce((a, b) => a + b, 0);
  const avgRisk = analytics.average_risk_score ?? 0;
  const riskColor = avgRisk > 70 ? 'danger' : avgRisk > 40 ? 'warning' : 'success';

  return (
    <div className="space-y-6 animate-slide-up">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">Engineering Intelligence</h1>
          <p className="text-sm text-text-muted mt-1">Organization-level analysis across all reviewed pull requests.</p>
        </div>

        {/* Period selector */}
        <div className="flex gap-1 bg-surface border border-border rounded-lg shadow-sm p-1 flex-shrink-0">
          {PERIODS.map(p => (
            <button
              key={p.value}
              onClick={() => setPeriod(p.value)}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all duration-150 ${
                period === p.value
                  ? 'bg-primary/15 text-primary'
                  : 'text-text-muted hover:text-text-secondary'
              }`}
              aria-pressed={period === p.value}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="PRs Reviewed"
          value={analytics.total_reviews ?? 0}
          icon={IconPRs}
          color="primary"
          subtitle={`Last ${period} days`}
        />
        <MetricCard
          title="Avg Risk Score"
          value={avgRisk}
          icon={IconRisk}
          color={riskColor}
          subtitle="0 = low · 100 = critical"
        />
        <MetricCard
          title="Total Findings"
          value={totalFindings}
          icon={IconFindings}
          color="accent"
          subtitle="Across all reviewed PRs"
        />
        <MetricCard
          title="Resolved Issues"
          value={life.resolved ?? 0}
          icon={IconResolved}
          color="success"
          subtitle="Fixed findings this period"
        />
      </div>

      {/* Breakdown charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Severity */}
        <div className="bg-surface border border-border rounded-lg shadow-sm p-5">
          <div className="mb-4">
            <h2 className="text-sm font-semibold text-text-primary">Severity Distribution</h2>
            <p className="text-xs text-text-muted mt-0.5">Number of findings per severity level</p>
          </div>
          {Object.values(sev).every(v => !v) ? (
            <EmptyState title="No findings" icon="success" variant="success" className="py-10" />
          ) : (
            <div className="space-y-3.5">
              {['critical', 'high', 'medium', 'low', 'info'].map(s => (
                <BarRow
                  key={s}
                  label={s}
                  value={sev[s] || 0}
                  max={maxSev}
                  color={SEV_COLORS[s] || 'bg-text-muted'}
                  textColor={SEV_TEXT[s] || 'text-text-primary'}
                />
              ))}
            </div>
          )}
        </div>

        {/* Category */}
        <div className="bg-surface border border-border rounded-lg shadow-sm p-5">
          <div className="mb-4">
            <h2 className="text-sm font-semibold text-text-primary">Category Breakdown</h2>
            <p className="text-xs text-text-muted mt-0.5">Top categories from AI analysis</p>
          </div>
          {catEntries.length === 0 ? (
            <EmptyState title="No categorized findings" icon="analytics" className="py-10" />
          ) : (
            <div className="space-y-3.5">
              {catEntries.map(([cat, count]) => (
                <BarRow
                  key={cat}
                  label={cat}
                  value={count}
                  max={maxCat}
                  color="bg-accent"
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Lifecycle */}
      <div className="bg-surface border border-border rounded-lg shadow-sm p-5">
        <div className="mb-5">
          <h2 className="text-sm font-semibold text-text-primary">Issue Lifecycle</h2>
          <p className="text-xs text-text-muted mt-0.5">Tracking how issues progress from detection to resolution</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            { key: 'new',        label: 'New Issues',        desc: 'Freshly detected in this period', border: 'border-primary/20', text: 'text-primary', bg: 'bg-primary/5' },
            { key: 'persistent', label: 'Persistent Issues', desc: 'Unresolved across multiple reviews', border: 'border-warning/20', text: 'text-warning', bg: 'bg-warning/5' },
            { key: 'resolved',   label: 'Resolved Issues',   desc: 'Addressed and fixed this period', border: 'border-success/20', text: 'text-success', bg: 'bg-success/5' },
          ].map(({ key, label, desc, border, text, bg }) => (
            <div key={key} className={`${bg} border ${border} rounded-lg p-4 text-center`}>
              <div className={`text-4xl font-bold tabular-nums leading-none ${text} mb-2`}>
                {life[key] ?? 0}
              </div>
              <div className={`text-sm font-semibold ${text} mb-1`}>{label}</div>
              <p className="text-xs text-text-muted leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
