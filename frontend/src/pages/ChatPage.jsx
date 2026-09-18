import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { orgApi } from '../lib/api';
import ChatAssistant from '../components/Review/ChatAssistant';

export default function ChatPage({ user, memberships }) {
  const orgId = memberships?.[0]?.organization_id;
  const [selectedRepoId, setSelectedRepoId] = useState('');

  // 1. Fetch all projects in the org
  const { data: projects = [], isLoading: loadingProjects } = useQuery({
    queryKey: ['projects', orgId],
    queryFn: () => orgApi.getProjects(orgId),
    enabled: !!orgId,
  });

  // 2. For all projects, fetch their repositories
  // (In a very large org, a backend endpoint for all org repos would be better,
  // but we reuse the existing orgApi.getRepositories per project for now)
  const { data: repositories = [], isLoading: loadingRepos } = useQuery({
    queryKey: ['orgRepositories', orgId, projects.map(p => p.id)],
    queryFn: async () => {
      if (projects.length === 0) return [];
      const repoPromises = projects.map(p => orgApi.getRepositories(p.id));
      const results = await Promise.all(repoPromises);
      return results.flat();
    },
    enabled: projects.length > 0,
  });

  const isLoading = loadingProjects || loadingRepos;

  if (!orgId) {
    return (
      <div className="flex flex-col items-center justify-center h-[600px] text-gray-400">
        <p>You must belong to an organization to use the Chatbot.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-slide-up h-full flex flex-col">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">RepoMind AI</h1>
          <p className="text-gray-400 text-sm">Ask questions about the selected repository using its indexed code and documentation.</p>
        </div>
      </div>

      <div className="flex flex-col flex-1 bg-surface/50 backdrop-blur-md border border-white/5 rounded-2xl p-6 min-h-[600px] gap-6">
        
        {/* Repository Selector */}
        <div className="w-full max-w-md">
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Target Repository
          </label>
          <select
            value={selectedRepoId}
            onChange={(e) => setSelectedRepoId(e.target.value)}
            disabled={isLoading || repositories.length === 0}
            className="w-full bg-surface border border-white/10 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary/50"
          >
            <option value="" disabled>
              {isLoading ? 'Loading repositories...' : repositories.length === 0 ? 'No repositories available' : 'Select a repository'}
            </option>
            {repositories.map(repo => (
              <option key={repo.id} value={repo.id}>
                {repo.github_owner}/{repo.github_name}
              </option>
            ))}
          </select>
        </div>

        {/* Chat Assistant */}
        <div className="flex-1">
          {selectedRepoId ? (
            <ChatAssistant 
              key={`repo-chat-${selectedRepoId}`}
              organizationId={orgId}
              repositoryId={parseInt(selectedRepoId)}
              contextType="repository"
              contextId={parseInt(selectedRepoId)}
            />
          ) : (
            <div className="flex items-center justify-center h-full border-2 border-dashed border-white/10 rounded-xl text-gray-500">
              Please select a repository to start chatting.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
