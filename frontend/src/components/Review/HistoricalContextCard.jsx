import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { historyApi } from '../../lib/api';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import EmptyState from '../ui/EmptyState';
import { Skeleton } from '../ui/LoadingSkeleton';

export default function HistoricalContextCard({ repositoryId, pullRequestId }) {
  const repoId = parseInt(repositoryId);
  const prId = parseInt(pullRequestId);

  const { data: comparison, isLoading, error, refetch } = useQuery({
    queryKey: ['prHistoricalContext', repoId, prId],
    queryFn: () => historyApi.compareChanges(repoId, { pull_request_id: prId }),
    enabled: !!repoId && !!prId,
  });

  if (isLoading) {
    return (
      <div className="space-y-4 py-4 animate-fade-in">
        <div className="flex items-center justify-between">
          <Skeleton className="h-6 w-48 rounded" />
          <Skeleton className="h-6 w-24 rounded" />
        </div>
        <Skeleton className="h-28 w-full rounded-lg" />
        <Skeleton className="h-40 w-full rounded-lg" />
      </div>
    );
  }

  if (error) {
    return (
      <Card className="p-6 text-center border-danger/20 bg-danger/5">
        <p className="text-sm text-danger font-medium">Failed to retrieve historical context</p>
        <p className="text-xs text-text-muted mt-1">{error.message}</p>
        <Button variant="secondary" size="xs" onClick={() => refetch()} className="mt-3">
          Retry
        </Button>
      </Card>
    );
  }

  if (!comparison) {
    return (
      <EmptyState
        title="No historical data available"
        description="Unable to analyze historical changes for this pull request."
      />
    );
  }

  const {
    is_problematic_hotspot,
    hotspot_details,
    relevant_adrs = [],
    historical_commits = [],
    similar_resolved_bugs = [],
    change_evolution_summary,
  } = comparison;

  const hasAnyData =
    is_problematic_hotspot ||
    relevant_adrs.length > 0 ||
    historical_commits.length > 0 ||
    similar_resolved_bugs.length > 0;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Overview Banner */}
      <div className="bg-surface border border-border rounded-lg p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-3 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-text-primary tracking-tight">
                Historical Intelligence & Architecture Context
              </h3>
              <p className="text-xs text-text-muted mt-0.5">
                Grounded in indexed git history, resolved review findings, and Architecture Decision Records (ADRs).
              </p>
            </div>
          </div>
          {is_problematic_hotspot ? (
            <Badge variant="critical">Problematic Hotspot Detected</Badge>
          ) : (
            <Badge variant="success">Standard Churn Profile</Badge>
          )}
        </div>

        {/* Hotspot Warning Banner */}
        {is_problematic_hotspot && hotspot_details && (
          <div className="mt-4 p-4 rounded-lg bg-danger/10 border border-danger/25 text-danger flex items-start gap-3">
            <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div className="space-y-1 text-xs">
              <div className="font-semibold text-sm">Caution: Modified files have high historical churn or bug rates</div>
              <p className="leading-relaxed opacity-90">
                File <span className="font-mono font-semibold">{hotspot_details.file_path}</span> has undergone{' '}
                <span className="font-bold">{hotspot_details.bugfix_count} bug fixes</span> and{' '}
                <span className="font-bold">{hotspot_details.recurring_finding_count} previous review findings</span>{' '}
                (Hotspot score: {hotspot_details.hotspot_score}).
              </p>
              {hotspot_details.recommendation && (
                <p className="mt-1 font-medium text-text-primary">
                  Recommendation: {hotspot_details.recommendation}
                </p>
              )}
            </div>
          </div>
        )}

        {/* Evolution Summary */}
        {change_evolution_summary && (
          <div className="mt-4 p-3 bg-surfaceHighlight/50 border border-border rounded-md text-xs text-text-secondary leading-relaxed">
            <span className="font-semibold text-text-primary mr-1">Change Evolution:</span>
            {change_evolution_summary}
          </div>
        )}
      </div>

      {!hasAnyData && (
        <EmptyState
          title="No historical patterns detected"
          description="None of the modified files have previous bugfixes, recurring findings, or governing ADRs recorded."
        />
      )}

      {/* Governing Architecture Decision Records (ADRs) */}
      {relevant_adrs.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-semibold text-text-primary uppercase tracking-wider flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-primary" />
              Governing Architecture Decisions ({relevant_adrs.length})
            </h4>
            <span className="text-[11px] text-text-muted">Must conform to these architectural choices</span>
          </div>

          <div className="grid grid-cols-1 gap-3">
            {relevant_adrs.map(adr => (
              <Card key={adr.id} className="p-4 border-primary/20 hover:border-primary/40 transition-colors">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-primary">{adr.adr_number}</span>
                      <span className="text-xs font-semibold text-text-primary">{adr.title}</span>
                      <Badge variant="outline" size="sm">{adr.status}</Badge>
                    </div>
                    <p className="text-xs text-text-secondary mt-1.5 leading-relaxed font-mono bg-surfaceHighlight/50 p-2 rounded border border-border">
                      {adr.decision}
                    </p>
                  </div>
                </div>

                <div className="mt-3 pt-3 border-t border-border flex flex-wrap items-center justify-between gap-2 text-[11px] text-text-muted">
                  <div>
                    <span className="font-medium text-text-secondary">Rationale:</span> {adr.reason}
                  </div>
                  {adr.consequences && (
                    <div className="text-text-muted italic truncate max-w-md">
                      Consequences: {adr.consequences}
                    </div>
                  )}
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Historical Commits & Engineering Decisions */}
      {historical_commits.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-semibold text-text-primary uppercase tracking-wider flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-indigo-400" />
              Related Historical Changes & Original Decisions ({historical_commits.length})
            </h4>
            <span className="text-[11px] text-text-muted">Actual git commit evidence</span>
          </div>

          <div className="space-y-2">
            {historical_commits.map(commit => (
              <div
                key={commit.id}
                className="p-3 bg-surface border border-border rounded-lg text-xs hover:border-primary/40 transition-colors"
              >
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-semibold text-text-primary bg-surfaceHighlight px-1.5 py-0.5 rounded border border-border">
                      {commit.commit_sha.substring(0, 7)}
                    </span>
                    {commit.pull_request_number && (
                      <span className="text-primary font-medium">PR #{commit.pull_request_number}</span>
                    )}
                    {commit.is_bugfix && <Badge variant="warning" size="sm">Bugfix</Badge>}
                    <span className="text-text-secondary font-medium truncate max-w-md">
                      {commit.commit_message.split('\n')[0]}
                    </span>
                  </div>
                  <span className="text-[11px] text-text-muted flex-shrink-0">
                    {commit.committed_at ? new Date(commit.committed_at).toLocaleDateString() : 'Historical'}
                  </span>
                </div>

                {commit.original_decision && (
                  <div className="mt-2 text-[11px] text-text-secondary bg-surfaceHighlight/50 p-2 rounded border border-border">
                    <span className="font-semibold text-text-primary">Original Engineering Decision:</span>{' '}
                    {commit.original_decision}
                  </div>
                )}

                {commit.supporting_evidence && (
                  <div className="mt-1 text-[11px] text-text-muted flex items-center gap-1.5">
                    <svg className="w-3.5 h-3.5 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>Supporting Evidence: {commit.supporting_evidence}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Similar Resolved Bugs */}
      {similar_resolved_bugs.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-semibold text-text-primary uppercase tracking-wider flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-amber-400" />
              Previously Resolved Similar Bugs ({similar_resolved_bugs.length})
            </h4>
            <span className="text-[11px] text-text-muted">Prior fixes in these files</span>
          </div>

          <div className="space-y-2">
            {similar_resolved_bugs.map(bug => (
              <div
                key={bug.id}
                className="p-3 bg-surface border border-border rounded-lg text-xs"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="font-semibold text-text-primary">{bug.title}</div>
                  <Badge variant="outline" size="sm">{bug.category}</Badge>
                </div>
                <div className="text-text-secondary mt-1 leading-relaxed">{bug.resolution_notes}</div>
                <div className="mt-2 pt-2 border-t border-border flex items-center justify-between text-[11px] text-text-muted">
                  <span className="font-mono text-text-muted">{bug.file_path}</span>
                  {bug.commit_sha && (
                    <span className="font-mono bg-surfaceHighlight px-1.5 py-0.5 rounded">
                      Fix: {bug.commit_sha.substring(0, 7)}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
