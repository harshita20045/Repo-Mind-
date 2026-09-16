import React from 'react';
import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { githubApi, orgApi } from '../lib/api';

export default function PullRequestsPage() {
  const { rid } = useParams();

  const { data: repo, isLoading: loadingRepo } = useQuery({
    queryKey: ['repository', rid],
    queryFn: () => orgApi.getRepository(rid),
    enabled: !!rid,
  });

  const { data: prs = [], isLoading: loadingPRs, error } = useQuery({
    queryKey: ['pullRequests', rid],
    queryFn: () => githubApi.getPullRequests(rid),
    enabled: !!rid,
  });

  const isLoading = loadingRepo || loadingPRs;

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="flex justify-between items-center">
        <div>
          <div className="flex items-center gap-3 mb-1 text-sm">
            <Link to="/repositories" className="text-gray-400 hover:text-white transition-colors">
              Repositories
            </Link>
            <span className="text-gray-600">/</span>
            <span className="text-gray-300">{repo?.github_name || `Repo #${rid}`}</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Pull Requests</h1>
          <p className="text-gray-400 text-sm">Track the AI review status of active pull requests for this repository.</p>
        </div>
      </div>

      <div className="grid gap-4 min-h-[400px]">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-400 bg-surface/50 rounded-2xl">
            <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mb-4"></div>
            Loading pull requests...
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center h-64 text-danger bg-surface/50 rounded-2xl">
            <p>Failed to load pull requests. Please try again later.</p>
          </div>
        ) : prs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-400 bg-surface/50 rounded-2xl">
            <p>No pull requests found for this repository.</p>
          </div>
        ) : (
          prs.map(pr => (
            <Link 
              key={pr.id} 
              to={`/repositories/${rid}/pull-requests/${pr.id}`}
              className="block bg-surface/50 backdrop-blur-md border border-white/5 rounded-2xl p-5 hover:bg-surface/80 transition-colors group"
            >
              <div className="flex items-start justify-between">
                <div className="flex gap-4">
                  <div className={`mt-1 flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center border ${
                    pr.state === 'open' ? 'bg-success/10 text-success border-success/20' :
                    pr.state === 'closed' ? 'bg-danger/10 text-danger border-danger/20' :
                    'bg-warning/10 text-warning border-warning/20'
                  }`}>
                    {pr.state === 'open' && (
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                    {pr.state === 'closed' && (
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs text-gray-500 font-mono">{repo?.github_name || 'repo'}</span>
                      <span className="text-gray-600">/</span>
                      <span className="text-xs text-gray-400 font-medium">PR #{pr.github_number}</span>
                    </div>
                    <h3 className="text-lg font-semibold text-gray-200 group-hover:text-white transition-colors">{pr.title}</h3>
                    <div className="text-sm text-gray-500 mt-2">
                      by {pr.author} • {pr.head_sha ? pr.head_sha.substring(0, 7) : ''}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center gap-6 text-right">
                  <div className="text-gray-600 group-hover:text-primary transition-colors">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </div>
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
