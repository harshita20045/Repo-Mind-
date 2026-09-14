import React from 'react';
import FindingCard from './FindingCard';

export default function FindingList({ findings }) {
  if (!findings || findings.length === 0) {
    return (
      <div className="text-center py-12 bg-slate-900/50 rounded-xl border border-emerald-500/20">
        <div className="w-12 h-12 bg-emerald-500/20 text-emerald-400 rounded-full flex items-center justify-center mx-auto mb-3">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-white mb-1">No issues found</h3>
        <p className="text-slate-400 text-sm">This pull request looks great! No findings were reported.</p>
      </div>
    );
  }

  // Sort by severity: Critical > High > Medium > Low
  const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
  const sortedFindings = [...findings].sort((a, b) => {
    const sA = severityOrder[a.severity.toLowerCase()] ?? 4;
    const sB = severityOrder[b.severity.toLowerCase()] ?? 4;
    return sA - sB;
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-lg font-medium text-white">
          Findings <span className="ml-2 text-xs font-semibold px-2 py-0.5 bg-slate-800 rounded-full text-slate-300">{findings.length}</span>
        </h3>
      </div>
      <div>
        {sortedFindings.map((finding) => (
          <FindingCard key={finding.id} finding={finding} />
        ))}
      </div>
    </div>
  );
}
