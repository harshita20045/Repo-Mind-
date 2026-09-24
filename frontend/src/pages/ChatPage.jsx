import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { orgApi } from '../lib/api';
import ChatAssistant from '../components/Review/ChatAssistant';
import EmptyState from '../components/ui/EmptyState';
import { PageLoader } from '../components/ui/LoadingSkeleton';

export default function ChatPage({ user, memberships }) {
  const orgId = memberships?.[0]?.organization_id;
  const [selectedRepoId, setSelectedRepoId] = useState('');

  // 1. Fetch all projects
  const { data: projects = [], isLoading: loadingProjects } = useQuery({
    queryKey: ['projects', orgId],
    queryFn: () => orgApi.getProjects(orgId),
    enabled: !!orgId,
  });

  // 2. Fetch all repositories across projects
  const { data: repositories = [], isLoading: loadingRepos } = useQuery({
    queryKey: ['orgRepositories', orgId, projects.map(p => p.id)],
    queryFn: async () => {
      if (projects.length === 0) return [];
      const results = await Promise.all(projects.map(p => orgApi.getRepositories(p.id)));
      return results.flat();
    },
    enabled: projects.length > 0,
  });

  const isLoading = loadingProjects || loadingRepos;
  const selectedRepo = repositories.find(r => String(r.id) === String(selectedRepoId));

  if (!orgId) {
    return (
      <EmptyState
        icon="chat"
        title="Organization required"
        description="You must belong to an organization to use the Developer Assistant."
        className="min-h-[400px]"
      />
    );
  }

  return (
    <div className="flex flex-col gap-5 animate-slide-up h-full">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary tracking-tight">Developer Assistant</h1>
        <p className="text-sm text-text-muted mt-1">
          Ask questions about a specific repository using its indexed code and documentation.
        </p>
      </div>

      {/* Main chat panel */}
      <div className="flex flex-col glass-card rounded-xl overflow-hidden" style={{ minHeight: '640px' }}>

        {/* Repository selector bar */}
        <div className="px-5 py-3.5 border-b border-white/[0.07] bg-surfaceHighlight/20 flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center text-primary flex-shrink-0">
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
            </div>
            <span className="text-sm font-semibold text-text-secondary">Repository</span>
          </div>

          <div className="flex-1 min-w-0">
            <select
              value={selectedRepoId}
              onChange={e => setSelectedRepoId(e.target.value)}
              disabled={isLoading || repositories.length === 0}
              aria-label="Select repository"
              className="bg-surface border border-white/[0.09] text-text-primary text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary/40 disabled:opacity-50 transition-all max-w-xs w-full"
            >
              <option value="" disabled>
                {isLoading
                  ? 'Loading repositories…'
                  : repositories.length === 0
                    ? 'No indexed repositories'
                    : 'Select a repository'}
              </option>
              {repositories.map(repo => (
                <option key={repo.id} value={repo.id}>
                  {repo.github_owner}/{repo.github_name}
                </option>
              ))}
            </select>
          </div>

          {selectedRepo && (
            <div className="flex items-center gap-2 flex-shrink-0">
              <span className="text-xs font-mono text-text-muted bg-white/5 border border-white/[0.07] px-2 py-0.5 rounded">
                {selectedRepo.default_branch}
              </span>
              <span className={`text-xs font-semibold px-2 py-0.5 rounded border ${
                selectedRepo.index_status === 'indexed'
                  ? 'text-success bg-success/10 border-success/20'
                  : 'text-warning bg-warning/10 border-warning/20'
              }`}>
                {selectedRepo.index_status}
              </span>
            </div>
          )}
        </div>

        {/* Chat area */}
        <div className="flex-1 p-5">
          {isLoading ? (
            <PageLoader message="Loading repositories…" />
          ) : selectedRepoId ? (
            <ChatAssistant
              key={`repo-chat-${selectedRepoId}`}
              organizationId={orgId}
              repositoryId={parseInt(selectedRepoId)}
              contextType="repository"
              contextId={parseInt(selectedRepoId)}
            />
          ) : (
            <div className="flex flex-col items-center justify-center h-full gap-4 py-16 text-center">
              <div className="w-16 h-16 rounded-2xl bg-surfaceHighlight/60 border border-white/[0.08] flex items-center justify-center text-text-muted">
                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-semibold text-text-primary">Select a repository to begin</p>
                <p className="text-xs text-text-muted mt-1.5 max-w-xs leading-relaxed">
                  Choose an indexed repository from the dropdown above to chat with its code and documentation.
                </p>
              </div>
              {repositories.length === 0 && !isLoading && (
                <div className="mt-2 text-xs text-text-muted bg-surfaceHighlight/40 border border-white/[0.07] rounded-lg px-4 py-3 max-w-sm">
                  No indexed repositories found. Connect and index repositories first.
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
