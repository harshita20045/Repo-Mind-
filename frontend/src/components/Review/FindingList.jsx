import React from 'react';
import FindingCard from './FindingCard';

export default function FindingList({ findings }) {
  if (!findings || findings.length === 0) {
    return (
      <div className="text-center py-16 bg-surface/30 rounded-2xl border border-success/20 backdrop-blur-sm animate-fade-in shadow-inner">
        <div className="w-16 h-16 bg-gradient-to-br from-success/20 to-success/5 text-success rounded-full flex items-center justify-center mx-auto mb-4 border border-success/20 shadow-lg shadow-success/10">
          <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h3 className="text-xl font-bold text-white mb-2 tracking-tight">No issues found</h3>
        <p className="text-gray-400 text-sm max-w-sm mx-auto leading-relaxed">This pull request looks great! The automated risk assessment found no significant issues.</p>
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
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold tracking-tight text-white flex items-center gap-3">
          Findings 
          <span className="text-xs font-bold px-2.5 py-0.5 bg-surfaceHighlight border border-white/10 rounded-md text-gray-300">
            {findings.length}
          </span>
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
