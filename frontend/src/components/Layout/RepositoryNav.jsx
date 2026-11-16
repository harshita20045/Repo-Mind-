import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { StatusBadge } from '../ui/Badge';
import { Button } from '../ui/Button';

export default function RepositoryNav({
  repository,
  repositoryId,
  onTriggerIndex,
  isIndexing = false,
  canIndex = true,
}) {
  const location = useLocation();
  const pathname = location.pathname;

  const repoName = repository
    ? `${repository.github_owner}/${repository.github_name}`
    : `Repository #${repositoryId}`;

  const tabs = [
    {
      to: `/repositories/${repositoryId}/topology`,
      label: 'Topology & Knowledge Graph',
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
          <circle cx="6" cy="6" r="3" />
          <circle cx="18" cy="6" r="3" />
          <circle cx="12" cy="18" r="3" />
          <path d="M8.5 7.5L15.5 7.5M7.5 8.5L10.5 15.5M16.5 8.5L13.5 15.5" strokeLinecap="round" />
        </svg>
      ),
      active: pathname.includes('/topology'),
    },
    {
      to: `/repositories/${repositoryId}/guide`,
      label: 'Codebase Guide & Onboarding',
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
      ),
      active: pathname.includes('/guide'),
    },
    {
      to: `/repositories/${repositoryId}/pull-requests`,
      label: 'Pull Requests & Reviews',
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
          <circle cx="6" cy="6" r="3" />
          <circle cx="6" cy="18" r="3" />
          <path d="M6 9v6M13 6h3a2 2 0 012 2v7a2 2 0 01-2 2h-3" strokeLinecap="round" strokeLinejoin="round" />
          <circle cx="18" cy="6" r="3" />
        </svg>
      ),
      active: pathname.includes('/pull-requests'),
    },
    {
      to: `/repositories/${repositoryId}/history`,
      label: 'History & ADRs',
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      active: pathname.includes('/history'),
    },
  ];

  return (
    <div className="rounded-xl border border-white/[0.08] bg-surface/60 backdrop-blur-md shadow-sm overflow-hidden mb-6">
      {/* Top Banner */}
      <div className="p-4 sm:p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/[0.06]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 border border-primary/30 flex items-center justify-center text-primary flex-shrink-0 shadow-glow-primary">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
            </svg>
          </div>
          <div>
            <div className="flex items-center gap-2.5 flex-wrap">
              <h2 className="text-lg font-bold text-text-primary tracking-tight">{repoName}</h2>
              {repository?.default_branch && (
                <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded bg-surfaceHighlight border border-white/10 text-text-secondary">
                  {repository.default_branch}
                </span>
              )}
              <StatusBadge
                status={repository?.index_status || 'indexed'}
                label={repository?.index_status || 'Indexed'}
              />
            </div>
            <p className="text-xs text-text-muted mt-0.5">
              Engineering intelligence perspectives, code knowledge graph, and architecture metrics.
            </p>
          </div>
        </div>

        {/* Right action button */}
        {onTriggerIndex && canIndex && (
          <div className="flex items-center gap-2 flex-shrink-0">
            <Button
              variant="outline"
              size="xs"
              onClick={onTriggerIndex}
              loading={isIndexing}
              disabled={isIndexing}
              leftIcon={
                <svg className="w-3.5 h-3.5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              }
            >
              {isIndexing ? 'Indexing…' : 'Re-Index Knowledge Graph'}
            </Button>
          </div>
        )}
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="flex items-center gap-1 px-3 py-1.5 bg-surfaceHighlight/20 overflow-x-auto text-xs">
        {tabs.map((tab) => (
          <Link
            key={tab.to}
            to={tab.to}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-lg font-medium transition-all whitespace-nowrap ${
              tab.active
                ? 'bg-primary/15 text-primary font-semibold border border-primary/25 shadow-sm'
                : 'text-text-muted hover:text-text-primary hover:bg-white/[0.04]'
            }`}
          >
            <span className={tab.active ? 'text-primary' : 'text-text-muted'}>{tab.icon}</span>
            <span>{tab.label}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}

