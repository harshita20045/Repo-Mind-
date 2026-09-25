import React from 'react';
import { useOutletContext } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { analyticsApi, orgApi } from '../lib/api';
import { Button } from '../components/ui/Button';
import Modal from '../components/ui/Modal';
import { MetricCard, SectionCard } from '../components/ui/Card';
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
  info:     { color: 'bg-info',         label: 'Info' },
};

function SeverityBar({ severity, count, max }) {
  const config = SEV_CONFIG[severity] || { color: 'bg-text-muted', label: severity };
  const pct = max > 0 ? Math.max(4, Math.round((count / max) * 100)) : 0;
  return (
    <div className="flex items-center gap-4 group text-[13px]">
      <div className="w-16 font-medium text-text-secondary capitalize">{config.label}</div>
      <div className="flex-1 h-1.5 bg-surfaceHighlight rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${config.color} transition-all duration-700`}
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={count}
          aria-valuemin={0}
          aria-valuemax={max}
        />
      </div>
      <div className="w-8 text-right font-medium text-text-primary tabular-nums">{count}</div>
    </div>
  );
}

// ─── Category item ─────────────────────────────────────────────────────────────
function CategoryRow({ category, count, max }) {
  const pct = max > 0 ? Math.max(4, Math.round((count / max) * 100)) : 0;
  return (
    <div className="flex items-center gap-4 text-[13px]">
      <div className="w-32 font-medium text-text-secondary capitalize truncate" title={category}>
        {category}
      </div>
      <div className="flex-1 h-1.5 bg-surfaceHighlight rounded-full overflow-hidden">
        <div
          className="h-full rounded-full bg-accent transition-all duration-700"
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={count}
          aria-valuemin={0}
          aria-valuemax={max}
        />
      </div>
      <div className="w-8 text-right font-medium text-text-primary tabular-nums">{count}</div>
    </div>
  );
}

// ─── Lifecycle card ────────────────────────────────────────────────────────────
function LifecycleCard({ label, value, description, color }) {
  const colors = {
    primary: 'border-primary/20 bg-primary/5',
    warning: 'border-warning/20 bg-warning/5',
    success: 'border-success/20 bg-success/5',
  };
  return (
    <div className={`flex-1 p-4 rounded-lg border ${colors[color] || colors.primary}`}>
      <div className="text-[12px] font-medium text-text-secondary mb-1.5">{label}</div>
      <div className="text-2xl font-semibold tabular-nums text-text-primary tracking-tight leading-none mb-1.5">{value ?? 0}</div>
      <p className="text-[12px] text-text-muted leading-tight">{description}</p>
    </div>
  );
}

// ─── Dashboard Page ────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const { memberships } = useOutletContext();
  const orgId = memberships?.[0]?.organization_id;
  const [isCreateModalOpen, setIsCreateModalOpen] = React.useState(false);
  const [newOrgName, setNewOrgName] = React.useState('');

  const { mutate: createOrg, isPending: isCreatingOrg } = useMutation({
    mutationFn: (name) => orgApi.createOrganization(name),
    onSuccess: () => {
      setIsCreateModalOpen(false);
      setNewOrgName('');
      alert('Organization created successfully. Please refresh.');
    },
    onError: (err) => alert(err.message),
  });

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
    <div className="space-y-6 animate-slide-up max-w-[1200px]">
      {/* Page header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-[20px] font-semibold text-text-primary tracking-tight">Engineering Intelligence</h1>
          <p className="text-[13px] text-text-muted mt-1">
            Repository-aware insights across your connected engineering systems.
          </p>
        </div>
        <Button variant="primary" size="sm" onClick={() => setIsCreateModalOpen(true)}>
          Create Organization
        </Button>
      </div>

      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Create Organization"
        size="sm"
      >
        <div className="space-y-4">
          <input
            type="text"
            placeholder="Organization Name"
            value={newOrgName}
            onChange={e => setNewOrgName(e.target.value)}
            className="w-full bg-surfaceHighlight border border-border text-text-primary text-sm rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary placeholder-text-muted transition-all"
          />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="ghost" size="sm" onClick={() => setIsCreateModalOpen(false)} disabled={isCreatingOrg}>Cancel</Button>
            <Button variant="primary" size="sm" loading={isCreatingOrg} onClick={() => createOrg(newOrgName)}>Create</Button>
          </div>
        </div>
      </Modal>

      {/* Metric cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Active Repositories"
          value={analytics?.total_repositories || 0}
          icon={IconPRs}
          color="muted"
          subtitle="Connected to RepoMind"
        />
        <MetricCard
          title="PRs Reviewed"
          value={analytics?.total_reviews ?? 0}
          icon={IconPRs}
          color="primary"
          subtitle="Analyzed in last 30 days"
        />
        <MetricCard
          title="Average Risk Score"
          value={`${avgRisk}`}
          icon={IconRisk}
          color={riskColor}
          subtitle="0-100 scale across PRs"
        />
        <MetricCard
          title="Critical Findings"
          value={severityData.critical ?? 0}
          icon={IconCritical}
          color="danger"
          subtitle="Require immediate attention"
        />
      </div>

      {/* Findings breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <SectionCard title="Findings by Severity" subtitle="Distribution of identified issues across severity levels">
          {severityKeys.every(k => !severityData[k]) ? (
            <EmptyState
              title="No findings"
              description="No findings detected in the last 30 days."
              icon="success"
              variant="success"
              className="py-8"
            />
          ) : (
            <div className="space-y-4">
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
        </SectionCard>

        <SectionCard title="Findings by Category" subtitle="Top categories from AI review findings">
          {categoryEntries.length === 0 ? (
            <EmptyState
              title="No categorized findings"
              description="Category breakdown will appear after PRs are reviewed."
              icon="analytics"
              className="py-8"
            />
          ) : (
            <div className="space-y-4">
              {categoryEntries.map(([cat, count]) => (
                <CategoryRow key={cat} category={cat} count={count} max={maxCategory} />
              ))}
            </div>
          )}
        </SectionCard>
      </div>

      {/* Resolution lifecycle */}
      <SectionCard title="Resolution Lifecycle" subtitle="Finding lifecycle states across all reviewed PRs this period">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
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
      </SectionCard>
    </div>
  );
}
