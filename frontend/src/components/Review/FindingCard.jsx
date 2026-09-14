import React from 'react';

export default function FindingCard({ finding }) {
  const getSeverityStyle = (severity) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'bg-red-500/10 border-red-500/20 text-red-400';
      case 'high':
        return 'bg-orange-500/10 border-orange-500/20 text-orange-400';
      case 'medium':
        return 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400';
      case 'low':
        return 'bg-blue-500/10 border-blue-500/20 text-blue-400';
      default:
        return 'bg-slate-500/10 border-slate-500/20 text-slate-400';
    }
  };

  const getCategoryColor = (category) => {
    switch (category.toLowerCase()) {
      case 'security': return 'text-red-400';
      case 'bug': return 'text-orange-400';
      case 'performance': return 'text-purple-400';
      case 'style': return 'text-blue-400';
      case 'architecture': return 'text-indigo-400';
      default: return 'text-slate-400';
    }
  };

  const severityStyle = getSeverityStyle(finding.severity);
  const categoryColor = getCategoryColor(finding.type);

  return (
    <div className={`p-4 rounded-xl border bg-slate-900/50 ${severityStyle} flex flex-col gap-3 mb-4`}>
      <div className="flex justify-between items-start gap-4">
        <h4 className="font-bold text-white text-base leading-tight">
          {finding.title}
        </h4>
        <div className="flex items-center gap-2 shrink-0">
          <span className={`px-2 py-0.5 text-xs font-semibold rounded uppercase tracking-wider ${severityStyle}`}>
            {finding.severity}
          </span>
          <span className={`text-xs font-medium uppercase tracking-wider ${categoryColor}`}>
            {finding.type}
          </span>
        </div>
      </div>

      {(finding.file || finding.line) && (
        <div className="text-xs font-mono text-slate-300 bg-slate-950 p-2 rounded-md border border-slate-800 self-start">
          {finding.file || 'Unknown file'} {finding.line ? `:${finding.line}` : ''}
        </div>
      )}

      <div className="space-y-2 text-sm text-slate-300">
        <div>
          <span className="font-semibold text-slate-200">Problem:</span> {finding.explanation}
        </div>
        {finding.recommendation && (
          <div>
            <span className="font-semibold text-slate-200">Recommendation:</span> {finding.recommendation}
          </div>
        )}
      </div>

      {(finding.rule_source || finding.confidence) && (
        <div className="pt-2 mt-2 border-t border-slate-800/50 flex items-center gap-4 text-xs text-slate-400">
          {finding.rule_source && (
            <div><span className="font-medium text-slate-500">Source:</span> {finding.rule_source}</div>
          )}
          {finding.confidence !== undefined && (
            <div><span className="font-medium text-slate-500">Confidence:</span> {Math.round(finding.confidence * 100)}%</div>
          )}
        </div>
      )}
    </div>
  );
}
