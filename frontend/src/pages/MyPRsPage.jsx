import React from 'react';
import { Link } from 'react-router-dom';

export default function MyPRsPage() {
  const prs = [
    { id: 104, repo: 'backend-api', title: 'Implement Payment Gateway Integration', status: 'pending', risk: 85, conflicts: 1, lastUpdated: '10 mins ago' },
    { id: 98, repo: 'frontend-web', title: 'Fix dashboard rendering bug', status: 'approved', risk: 12, conflicts: 0, lastUpdated: '1 hour ago' },
    { id: 105, repo: 'backend-api', title: 'Add rate limiting to public endpoints', status: 'rejected', risk: 92, conflicts: 3, lastUpdated: '3 hours ago' },
  ];

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">My Pull Requests</h1>
          <p className="text-gray-400 text-sm">Track the AI review status of your active pull requests.</p>
        </div>
      </div>

      <div className="grid gap-4">
        {prs.map(pr => (
          <Link 
            key={pr.id} 
            to={`/repositories/1/pull-requests/${pr.id}`}
            className="block bg-surface/50 backdrop-blur-md border border-white/5 rounded-2xl p-5 hover:bg-surface/80 transition-colors group"
          >
            <div className="flex items-start justify-between">
              <div className="flex gap-4">
                <div className={`mt-1 flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center border ${
                  pr.status === 'approved' ? 'bg-success/10 text-success border-success/20' :
                  pr.status === 'rejected' ? 'bg-danger/10 text-danger border-danger/20' :
                  'bg-warning/10 text-warning border-warning/20'
                }`}>
                  {pr.status === 'approved' && (
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                  {pr.status === 'rejected' && (
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  )}
                  {pr.status === 'pending' && (
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                  )}
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs text-gray-500 font-mono">{pr.repo}</span>
                    <span className="text-gray-600">/</span>
                    <span className="text-xs text-gray-400 font-medium">PR #{pr.id}</span>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-200 group-hover:text-white transition-colors">{pr.title}</h3>
                  <div className="text-sm text-gray-500 mt-2">
                    Updated {pr.lastUpdated}
                  </div>
                </div>
              </div>
              
              <div className="flex items-center gap-6 text-right">
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">Risk</div>
                  <div className={`font-bold ${pr.risk > 70 ? 'text-danger' : pr.risk > 40 ? 'text-warning' : 'text-success'}`}>
                    {pr.risk}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">Conflicts</div>
                  <div className={`font-bold ${pr.conflicts > 0 ? 'text-warning' : 'text-gray-400'}`}>
                    {pr.conflicts}
                  </div>
                </div>
                <div className="text-gray-600 group-hover:text-primary transition-colors">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
