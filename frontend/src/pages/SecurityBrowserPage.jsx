import React from 'react';

export default function SecurityBrowserPage() {
  const findings = []; // Backend does not currently provide a global findings endpoint

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Security & Findings Browser</h1>
          <p className="text-gray-400 text-sm">Global view of all vulnerabilities and code quality issues across the organization.</p>
        </div>
      </div>

      <div className="bg-surface/50 backdrop-blur-md border border-white/5 rounded-2xl overflow-hidden min-h-[400px]">
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

        <div className="flex flex-col items-center justify-center h-64 text-gray-400">
          <svg className="w-12 h-12 mb-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          <p>Global findings API is not yet implemented.</p>
        </div>
      </div>
    </div>
  );
}
