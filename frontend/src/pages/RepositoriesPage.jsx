import React from 'react';
import { Link, useOutletContext } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { orgApi } from '../lib/api';

export default function RepositoriesPage() {
  const { memberships } = useOutletContext();
  const orgId = memberships?.[0]?.organization_id;

  const { data: projects, isLoading: loadingProjects, error: projectError } = useQuery({
    queryKey: ['projects', orgId],
    queryFn: () => orgApi.getProjects(orgId),
    enabled: !!orgId,
  });

  const projectId = projects?.[0]?.id;

  const { data: repositories = [], isLoading: loadingRepos, error: repoError } = useQuery({
    queryKey: ['repositories', projectId],
    queryFn: () => orgApi.getRepositories(projectId),
    enabled: !!projectId,
  });

  const isLoading = loadingProjects || loadingRepos;
  const error = projectError || repoError;

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Repositories</h1>
          <p className="text-gray-400 text-sm">Manage and monitor source code repositories onboarded to RepoMind.</p>
        </div>
        <button className="px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg font-medium transition-colors border border-white/10 shadow-lg shadow-primary/20 flex items-center gap-2">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Repository
        </button>
      </div>

      <div className="bg-surface/50 backdrop-blur-md border border-white/5 rounded-2xl overflow-hidden min-h-[400px]">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-400">
            <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mb-4"></div>
            Loading repositories...
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center h-64 text-danger">
            <svg className="w-12 h-12 mb-4 text-danger/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <p>Failed to load repositories.</p>
          </div>
        ) : repositories.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-400">
            <svg className="w-12 h-12 mb-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            <p>No repositories found for this project.</p>
          </div>
        ) : (
          <>
            <div className="p-4 border-b border-white/5 flex gap-4">
              <div className="relative flex-1">
                <svg className="w-4 h-4 absolute left-3 top-3 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input 
                  type="text" 
                  placeholder="Search repositories..." 
                  className="w-full bg-surfaceHighlight/30 border border-white/5 text-gray-200 text-sm rounded-lg pl-10 pr-4 py-2 focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all"
                />
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-surfaceHighlight/20 border-b border-white/5 text-xs uppercase tracking-wider text-gray-500 font-semibold">
                    <th className="px-6 py-4">Repository Name</th>
                    <th className="px-6 py-4">Owner</th>
                    <th className="px-6 py-4">Default Branch</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {repositories.map(repo => (
                    <tr key={repo.id} className="hover:bg-white/[0.02] transition-colors group">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-surfaceHighlight flex items-center justify-center text-gray-400 group-hover:text-primary transition-colors border border-white/5">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                            </svg>
                          </div>
                          <div>
                            <Link to={`/repositories/${repo.id}/pull-requests`} className="font-medium text-gray-200 hover:text-white transition-colors">
                              {repo.github_name}
                            </Link>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-sm text-gray-400">{repo.github_owner}</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-400 flex items-center gap-1.5 font-mono">
                          {repo.default_branch}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
