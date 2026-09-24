import React from 'react';
import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { githubApi, orgApi } from '../lib/api';
import { StatusBadge } from '../components/ui/Badge';
import EmptyState from '../components/ui/EmptyState';
import { TableRowSkeleton } from '../components/ui/LoadingSkeleton';

// ─── PR state icon ─────────────────────────────────────────────────────────────
function PrStateIcon({ state }) {
  if (state === 'open') {
    return (
      <div className="w-6 h-6 rounded-full bg-success/10 border border-success/25 flex items-center justify-center flex-shrink-0" aria-label="Open PR">
        <svg className="w-3.5 h-3.5 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <circle cx="6" cy="6" r="3" /><circle cx="6" cy="18" r="3" />
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 9v6M15.5 6H18a2 2 0 012 2v7a2 2 0 01-2 2h-2.5" />
          <circle cx="18" cy="6" r="3" />
        </svg>
      </div>
    );
  }
  if (state === 'merged') {
    return (
      <div className="w-6 h-6 rounded-full bg-accent/10 border border-accent/25 flex items-center justify-center flex-shrink-0" aria-label="Merged PR">
        <svg className="w-3.5 h-3.5 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" />
        </svg>
      </div>
    );
  }
  return (
    <div className="w-6 h-6 rounded-full bg-white/5 border border-white/10 flex items-center justify-center flex-shrink-0" aria-label="Closed PR">
      <svg className="w-3.5 h-3.5 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function PullRequestsPage() {
  const { rid } = useParams();

  const { data: repo, isLoading: loadingRepo } = useQuery({
    queryKey: ['repository', rid],
    queryFn: () => orgApi.getRepository(rid),
    enabled: !!rid,
  });

  const { data: prs = [], isLoading: loadingPRs, error, refetch } = useQuery({
    queryKey: ['pullRequests', rid],
    queryFn: () => githubApi.getPullRequests(rid),
    enabled: !!rid,
  });

  const isLoading = loadingRepo || loadingPRs;

  return (
    <div className="space-y-5 animate-slide-up">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary tracking-tight">Pull Requests</h1>
        <p className="text-sm text-text-muted mt-1">
          {repo ? (
            <>Tracking AI review status for <span className="font-mono text-text-secondary text-xs font-semibold">{repo.github_owner}/{repo.github_name}</span></>
          ) : (
            'Track the AI review status of active pull requests.'
          )}
        </p>
      </div>

      {/* PR table */}
      <div className="glass-card rounded-xl overflow-hidden">
        {isLoading ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/[0.06] bg-white/[0.02]">
                  {['#', 'Title', 'Author', 'SHA', 'Status', ''].map(h => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[0,1,2,3].map(i => <TableRowSkeleton key={i} cols={6} />)}
              </tbody>
            </table>
          </div>
        ) : error ? (
          <EmptyState
            icon="pr"
            title="Failed to load pull requests"
            description={error.message || 'Could not fetch pull requests from the server.'}
            action={
              <button
                onClick={() => refetch()}
                className="text-sm font-medium text-primary hover:text-primary-hover transition-colors"
              >
                Try again
              </button>
            }
            className="py-16"
          />
        ) : prs.length === 0 ? (
          <EmptyState
            icon="pr"
            title="No pull requests found"
            description="Pull requests will appear here once they are synced from GitHub. Make sure the repository is indexed and webhooks are configured."
            className="py-16"
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full" role="table" aria-label="Pull requests">
              <thead>
                <tr className="border-b border-white/[0.06] bg-white/[0.02]">
                  <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider w-16">#</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">Title</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider hidden md:table-cell">Author</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider hidden lg:table-cell">Commit</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">Status</th>
                  <th className="w-8" />
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {prs.map(pr => (
                  <tr
                    key={pr.id}
                    className="hover:bg-white/[0.025] transition-colors group cursor-pointer"
                    onClick={() => {}}
                  >
                    <td className="px-4 py-3.5">
                      <span className="text-xs font-mono text-text-muted font-semibold">
                        #{pr.github_number}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 max-w-[340px]">
                      <div className="flex items-center gap-3">
                        <PrStateIcon state={pr.state} />
                        <Link
                          to={`/repositories/${rid}/pull-requests/${pr.id}`}
                          className="text-sm font-medium text-text-primary group-hover:text-primary transition-colors truncate"
                          onClick={e => e.stopPropagation()}
                        >
                          {pr.title}
                        </Link>
                      </div>
                    </td>
                    <td className="px-4 py-3.5 hidden md:table-cell">
                      <div className="flex items-center gap-2">
                        <div className="w-5 h-5 rounded-full bg-gradient-to-br from-accent/30 to-primary/30 border border-white/10 flex items-center justify-center text-2xs font-bold text-white flex-shrink-0">
                          {pr.author?.charAt(0).toUpperCase() || 'U'}
                        </div>
                        <span className="text-sm text-text-muted truncate max-w-[120px]">{pr.author || '—'}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3.5 hidden lg:table-cell">
                      {pr.head_sha ? (
                        <span className="font-mono text-xs text-text-muted bg-white/5 border border-white/[0.07] px-2 py-0.5 rounded">
                          {pr.head_sha.substring(0, 7)}
                        </span>
                      ) : (
                        <span className="text-text-muted text-xs">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3.5">
                      <StatusBadge
                        status={pr.state}
                        label={pr.state ? pr.state.charAt(0).toUpperCase() + pr.state.slice(1) : '—'}
                      />
                    </td>
                    <td className="px-4 py-3.5">
                      <Link
                        to={`/repositories/${rid}/pull-requests/${pr.id}`}
                        className="text-text-muted group-hover:text-primary transition-colors"
                        aria-label={`Open PR: ${pr.title}`}
                        onClick={e => e.stopPropagation()}
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                        </svg>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
