import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useOutletContext } from 'react-router-dom';
import { securityApi } from '../lib/api';
import { StatusBadge, RiskBadge } from '../components/ui/Badge';

export default function SecurityBrowserPage() {
  const { memberships } = useOutletContext();
  const orgId = memberships?.[0]?.organization_id;
  const queryClient = useQueryClient();

  const [severityFilter, setSeverityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const { data: findings, isLoading } = useQuery({
    queryKey: ['securityFindings', orgId, severityFilter, statusFilter],
    queryFn: () => securityApi.getFindings(orgId, severityFilter, statusFilter),
    enabled: !!orgId,
  });

  const { mutate: updateStatus } = useMutation({
    mutationFn: ({ findingId, status }) => securityApi.updateFindingStatus(findingId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['securityFindings'] });
    },
  });

  return (
    <div className="space-y-5 animate-slide-up">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary tracking-tight">Security Browser</h1>
        <p className="text-sm text-text-muted mt-1">
          Organization-wide view of vulnerabilities and code quality issues.
        </p>
      </div>

      {/* Filters bar */}
      <div className="bg-surface border border-white/[0.07] rounded-xl p-4 grid grid-cols-1 md:grid-cols-4 gap-3">
        {/* Search */}
        <div className="md:col-span-2 relative">
          <svg className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            placeholder="Search by rule, file, or repository…"
            disabled
            className="w-full bg-surfaceHighlight/20 border border-white/[0.07] text-text-muted text-sm rounded-lg pl-9 pr-4 py-2 cursor-not-allowed opacity-60 focus:outline-none"
          />
        </div>
        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="bg-surfaceHighlight border border-white/[0.07] text-text-primary text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-primary/50"
        >
          <option value="">All Severities</option>
          <option value="CRITICAL">Critical</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-surfaceHighlight border border-white/[0.07] text-text-primary text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-primary/50"
        >
          <option value="">All States</option>
          <option value="NEW">New</option>
          <option value="PERSISTENT">Persistent</option>
          <option value="RESOLVED">Resolved</option>
          <option value="accept">Accepted</option>
          <option value="reject">Rejected</option>
          <option value="ignore">Ignored</option>
        </select>
      </div>

      {/* List */}
      <div className="bg-surface border border-white/[0.07] rounded-xl overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-text-muted text-sm">Loading findings...</div>
        ) : !findings || findings.length === 0 ? (
          <div className="p-8 text-center text-text-muted text-sm">No findings match the current filters.</div>
        ) : (
          <div className="divide-y divide-white/[0.07]">
            {findings.map((f) => (
              <div key={f.id} className="p-4 hover:bg-surfaceHighlight/20 transition-colors flex flex-col md:flex-row md:items-start gap-4 justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <RiskBadge level={f.severity.toLowerCase()} />
                    <span className="text-sm font-semibold text-text-primary">{f.title}</span>
                  </div>
                  <div className="text-xs text-text-muted font-mono mt-2">
                    {f.repository_name} #{f.pull_request_number} &middot; {f.file}{f.line ? `:${f.line}` : ''}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={f.status} />
                  <select
                    value={f.status}
                    onChange={(e) => updateStatus({ findingId: f.id, status: e.target.value })}
                    className="bg-surfaceHighlight border border-white/[0.07] text-text-primary text-xs rounded px-2 py-1 focus:outline-none"
                  >
                    <option value="" disabled>Set Status</option>
                    <option value="accept">Accept</option>
                    <option value="reject">Reject</option>
                    <option value="ignore">Ignore</option>
                  </select>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
