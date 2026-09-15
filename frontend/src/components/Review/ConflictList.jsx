import React from 'react';

export default function ConflictList({ conflicts = [] }) {
  if (!conflicts || conflicts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-400 space-y-4">
        <div className="w-16 h-16 rounded-full bg-success/10 flex items-center justify-center text-success mb-2">
          <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <p className="font-medium text-gray-300">No Semantic Conflicts Detected</p>
        <p className="text-sm text-center max-w-md">The conflict engine did not find any API contract breakages, overlapping architectural changes, or logic conflicts.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">Semantic Conflicts</h2>
        <p className="text-gray-400 text-sm">
          These conflicts represent logic clashes, API breakages, or overlapping work that Git cannot detect mechanically.
        </p>
      </div>

      <div className="space-y-4">
        {conflicts.map((conflict, i) => (
          <div key={i} className="bg-surfaceHighlight/20 border border-white/5 rounded-xl p-5 hover:bg-surfaceHighlight/30 transition-colors group relative overflow-hidden">
            
            {/* Warning strip */}
            <div className={`absolute left-0 top-0 bottom-0 w-1 ${
              conflict.severity === 'critical' ? 'bg-danger' : 
              conflict.severity === 'high' ? 'bg-warning' : 'bg-primary'
            }`}></div>

            <div className="flex justify-between items-start mb-3 pl-3">
              <div className="flex items-center gap-3">
                <span className={`px-2.5 py-1 rounded-full text-xs font-bold capitalize border ${
                  conflict.severity === 'critical' ? 'text-danger bg-danger/10 border-danger/20' : 
                  conflict.severity === 'high' ? 'text-warning bg-warning/10 border-warning/20' : 
                  'text-primary bg-primary/10 border-primary/20'
                }`}>
                  {conflict.severity || 'Medium'} Severity
                </span>
                <span className="px-2.5 py-1 rounded-full text-xs font-medium text-gray-300 bg-white/5 border border-white/10 uppercase tracking-wider">
                  {conflict.conflict_type?.replace('_', ' ')}
                </span>
              </div>
            </div>

            <div className="pl-3">
              <p className="text-gray-200 text-sm leading-relaxed mb-4">
                {conflict.description}
              </p>

              {/* Related Files/PRs */}
              <div className="flex flex-wrap gap-4 mt-4 pt-4 border-t border-white/5">
                {conflict.related_files && conflict.related_files.length > 0 && (
                  <div className="flex-1 min-w-[200px]">
                    <h4 className="text-xs font-bold text-gray-500 uppercase mb-2">Conflicting Files</h4>
                    <div className="flex flex-wrap gap-2">
                      {conflict.related_files.map((file, idx) => (
                        <div key={idx} className="flex items-center gap-1.5 px-2 py-1 bg-surface rounded text-xs text-gray-300 font-mono border border-white/5">
                          <svg className="w-3.5 h-3.5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                          </svg>
                          {file}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
