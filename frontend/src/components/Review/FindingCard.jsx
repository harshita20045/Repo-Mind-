import React from 'react';

export default function FindingCard({ finding }) {
  const getSeverityStyle = (severity) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'bg-danger/10 border-danger/20 text-danger shadow-danger/5';
      case 'high':
        return 'bg-orange-500/10 border-orange-500/20 text-orange-400 shadow-orange-500/5';
      case 'medium':
        return 'bg-warning/10 border-warning/20 text-warning shadow-warning/5';
      case 'low':
        return 'bg-primary/10 border-primary/20 text-primary shadow-primary/5';
      default:
        return 'bg-surfaceHighlight/30 border-white/10 text-gray-300';
    }
  };

  const getCategoryColor = (category) => {
    switch (category.toLowerCase()) {
      case 'security': return 'text-danger';
      case 'bug': return 'text-warning';
      case 'performance': return 'text-accent';
      case 'style': return 'text-primary';
      case 'architecture': return 'text-indigo-400';
      default: return 'text-gray-400';
    }
  };

  const severityStyle = getSeverityStyle(finding.severity);
  const categoryColor = getCategoryColor(finding.type);

  return (
    <div className={`p-5 rounded-2xl border backdrop-blur-sm shadow-lg transition-all hover:-translate-y-1 ${severityStyle} flex flex-col gap-3 mb-4`}>
      <div className="flex justify-between items-start gap-4">
        <h4 className="font-bold text-white text-lg leading-tight tracking-tight">
          {finding.title}
        </h4>
        <div className="flex items-center gap-2 shrink-0">
          <span className={`px-2.5 py-1 text-[10px] font-bold rounded-md uppercase tracking-wider border ${severityStyle}`}>
            {finding.severity}
          </span>
          <span className={`text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-md bg-surface border border-white/5 ${categoryColor}`}>
            {finding.type}
          </span>
        </div>
      </div>

      {(finding.file || finding.line) && (
        <div className="text-xs font-mono text-gray-300 bg-surfaceHighlight/50 px-3 py-1.5 rounded-lg border border-white/5 self-start shadow-inner">
          {finding.file || 'Unknown file'} {finding.line ? <span className="text-gray-500">:{finding.line}</span> : ''}
        </div>
      )}

      <div className="space-y-3 text-sm text-gray-300 bg-surface/30 p-4 rounded-xl border border-white/5">
        <div>
          <span className="font-semibold text-white block mb-1">Problem</span> 
          <p className="leading-relaxed text-gray-400">{finding.explanation}</p>
        </div>
        {finding.recommendation && (
          <div className="pt-3 border-t border-white/5">
            <span className="font-semibold text-white block mb-1">Recommendation</span> 
            <p className="leading-relaxed text-gray-400">{finding.recommendation}</p>
          </div>
        )}
      </div>

      <div className="pt-2 mt-2 border-t border-white/10 flex items-center justify-between text-xs">
        <div className="flex items-center gap-4 text-gray-500 font-medium">
          {finding.rule_source && (
            <div className="flex items-center gap-1.5">
              <svg className="w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              {finding.rule_source}
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          {finding.evidence_status === 'supported' && (
            <span className="inline-flex items-center gap-1 text-success bg-success/10 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border border-success/20">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
              Grounded
            </span>
          )}
          <button className="px-3 py-1.5 hover:bg-white/5 rounded-lg text-gray-400 hover:text-white transition-colors border border-transparent hover:border-white/10">
            Dismiss
          </button>
        </div>
      </div>
    </div>
  );
}
