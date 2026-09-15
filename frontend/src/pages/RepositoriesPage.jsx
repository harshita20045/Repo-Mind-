import React from 'react';
import { Link } from 'react-router-dom';

export default function RepositoriesPage() {
  const repositories = [
    { id: 1, name: 'backend-api', language: 'Python', visibility: 'Private', lastScan: '2 hours ago', risk: 'Low', prs: 3 },
    { id: 2, name: 'frontend-web', language: 'JavaScript', visibility: 'Private', lastScan: '5 hours ago', risk: 'Medium', prs: 5 },
    { id: 3, name: 'auth-service', language: 'Go', visibility: 'Internal', lastScan: '1 day ago', risk: 'High', prs: 1 },
    { id: 4, name: 'infrastructure-cdk', language: 'TypeScript', visibility: 'Private', lastScan: '3 days ago', risk: 'Low', prs: 0 },
  ];

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

      <div className="bg-surface/50 backdrop-blur-md border border-white/5 rounded-2xl overflow-hidden">
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
          <button className="px-4 py-2 bg-surfaceHighlight/50 border border-white/5 rounded-lg text-sm text-gray-300 hover:text-white transition-colors">
            Filter
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surfaceHighlight/20 border-b border-white/5 text-xs uppercase tracking-wider text-gray-500 font-semibold">
                <th className="px-6 py-4">Repository Name</th>
                <th className="px-6 py-4">Language</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Risk Profile</th>
                <th className="px-6 py-4 text-right">Active PRs</th>
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
                        <Link to={`/repositories/${repo.id}`} className="font-medium text-gray-200 hover:text-white transition-colors">
                          {repo.name}
                        </Link>
                        <div className="text-xs text-gray-500 mt-0.5 text-mono">{repo.visibility}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm text-gray-400">{repo.language}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-400 flex items-center gap-1.5">
                      <div className="w-1.5 h-1.5 rounded-full bg-success"></div>
                      Scanned {repo.lastScan}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-bold border ${
                      repo.risk === 'High' ? 'text-danger bg-danger/10 border-danger/20' :
                      repo.risk === 'Medium' ? 'text-warning bg-warning/10 border-warning/20' :
                      'text-success bg-success/10 border-success/20'
                    }`}>
                      {repo.risk}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-surfaceHighlight text-xs font-medium text-gray-300">
                      {repo.prs}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
