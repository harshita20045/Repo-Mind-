import React from 'react';
import { Link } from 'react-router-dom';

export default function SecurityBrowserPage() {
  const findings = [
    { id: 'F-892', repo: 'backend-api', rule: 'hardcoded-secret', file: 'auth.py:42', severity: 'critical', state: 'new', time: '10 mins ago', pr: 104 },
    { id: 'F-891', repo: 'backend-api', rule: 'sql-injection', file: 'users.py:112', severity: 'high', state: 'persistent', time: '2 hours ago', pr: 104 },
    { id: 'F-880', repo: 'frontend-web', rule: 'xss-vulnerability', file: 'DangerouslySet.jsx:12', severity: 'medium', state: 'resolved', time: '1 day ago', pr: 98 },
  ];

  const getSeverityColor = (sev) => {
    switch (sev) {
      case 'critical': return 'text-danger bg-danger/10 border-danger/20';
      case 'high': return 'text-warning bg-warning/10 border-warning/20';
      case 'medium': return 'text-primary bg-primary/10 border-primary/20';
      default: return 'text-gray-400 bg-white/5 border-white/10';
    }
  };

  const getStateColor = (state) => {
    switch (state) {
      case 'new': return 'text-danger';
      case 'persistent': return 'text-warning';
      case 'resolved': return 'text-success';
      default: return 'text-gray-400';
    }
  };

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Security & Findings Browser</h1>
          <p className="text-gray-400 text-sm">Global view of all vulnerabilities and code quality issues across the organization.</p>
        </div>
        <button className="px-4 py-2 bg-surfaceHighlight/50 hover:bg-surfaceHighlight text-white rounded-lg font-medium transition-colors border border-white/10 flex items-center gap-2">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Export CSV
        </button>
      </div>

      <div className="bg-surface/50 backdrop-blur-md border border-white/5 rounded-2xl overflow-hidden">
        <div className="p-4 border-b border-white/5 grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="md:col-span-2 relative">
            <svg className="w-4 h-4 absolute left-3 top-3 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input 
              type="text" 
              placeholder="Search by rule, file, or repository..." 
              className="w-full bg-surfaceHighlight/30 border border-white/5 text-gray-200 text-sm rounded-lg pl-10 pr-4 py-2 focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all"
            />
          </div>
          <select className="bg-surfaceHighlight/30 border border-white/5 text-gray-200 text-sm rounded-lg px-4 py-2 focus:outline-none focus:ring-1 focus:ring-primary/50 appearance-none">
            <option>All Severities</option>
            <option>Critical</option>
            <option>High</option>
            <option>Medium</option>
            <option>Low</option>
          </select>
          <select className="bg-surfaceHighlight/30 border border-white/5 text-gray-200 text-sm rounded-lg px-4 py-2 focus:outline-none focus:ring-1 focus:ring-primary/50 appearance-none">
            <option>All States</option>
            <option>New</option>
            <option>Persistent</option>
            <option>Resolved</option>
          </select>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surfaceHighlight/20 border-b border-white/5 text-xs uppercase tracking-wider text-gray-500 font-semibold">
                <th className="px-6 py-4">ID</th>
                <th className="px-6 py-4">Finding / Rule</th>
                <th className="px-6 py-4">Repository</th>
                <th className="px-6 py-4">Severity</th>
                <th className="px-6 py-4">State</th>
                <th className="px-6 py-4 text-right">Introduced In</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {findings.map((finding) => (
                <tr key={finding.id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-500">
                    {finding.id}
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-200 mb-0.5">{finding.rule}</div>
                    <div className="text-xs font-mono text-gray-500 flex items-center gap-1">
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                      </svg>
                      {finding.file}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                    {finding.repo}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-bold border capitalize ${getSeverityColor(finding.severity)}`}>
                      {finding.severity}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`flex items-center gap-1.5 text-sm font-medium capitalize ${getStateColor(finding.state)}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${
                        finding.state === 'new' ? 'bg-danger' : 
                        finding.state === 'persistent' ? 'bg-warning' : 'bg-success'
                      }`}></span>
                      {finding.state}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <Link to={`/repositories/1/pull-requests/${finding.pr}`} className="text-sm text-primary hover:text-primary-hover font-medium hover:underline flex justify-end items-center gap-1">
                      PR #{finding.pr}
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </Link>
                    <div className="text-xs text-gray-500 mt-1">{finding.time}</div>
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
