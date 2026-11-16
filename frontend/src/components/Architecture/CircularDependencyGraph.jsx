import React from 'react';
import { SeverityBadge } from '../ui/Badge';

export default function CircularDependencyGraph({ circularDependencies = [] }) {
  if (circularDependencies.length === 0) {
    return (
      <div className="bg-surface border border-border rounded-lg p-8 text-center space-y-3">
        <div className="w-10 h-10 rounded-full bg-success/10 border border-success/20 flex items-center justify-center text-success mx-auto">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h3 className="text-sm font-semibold text-text-primary">
          Acyclic Dependency Graph
        </h3>
        <p className="text-[12px] text-text-secondary max-w-md mx-auto">
          Zero circular dependency cycles detected across modules. Module import order is clean and deterministic.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
          <span>Circular Dependency Cycles</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-danger/10 text-danger font-mono font-bold">
            {circularDependencies.length}
          </span>
        </h3>
        <span className="text-[11px] text-danger font-medium">
          Tight coupling hazard: Refactor cycles before adding more features
        </span>
      </div>

      <div className="space-y-4">
        {circularDependencies.map((cycle, idx) => (
          <div
            key={idx}
            className="bg-surface border border-border rounded-lg p-5 transition-colors hover:border-danger/40"
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
              <div className="flex items-center gap-2 flex-wrap">
                <SeverityBadge severity={cycle.severity || 'high'} />
                <span className="text-xs font-semibold text-text-primary">
                  {cycle.title}
                </span>
                <span className="text-[10px] uppercase font-bold font-mono px-2 py-0.5 rounded bg-surfaceHighlight text-text-muted border border-border">
                  {cycle.length} File Loop
                </span>
              </div>
            </div>

            <p className="text-[12px] text-text-secondary leading-relaxed mb-3">
              {cycle.explanation}
            </p>

            {/* Cycle Chain Visualizer */}
            <div className="bg-surfaceHighlight/50 border border-border rounded-lg p-3 mb-3">
              <span className="text-[10px] font-semibold text-text-muted uppercase tracking-wider block mb-2">
                Dependency Chain Loop
              </span>
              <div className="flex items-center gap-2 flex-wrap text-xs font-mono">
                {cycle.cycle_path.map((node, nIdx) => (
                  <React.Fragment key={nIdx}>
                    <span
                      className={`px-2 py-1 rounded border ${
                        nIdx === 0 || nIdx === cycle.cycle_path.length - 1
                          ? 'bg-rose-500/10 text-rose-300 border-rose-500/30 font-bold'
                          : 'bg-surface text-text-primary border-border'
                      }`}
                    >
                      {node}
                    </span>
                    {nIdx < cycle.cycle_path.length - 1 && (
                      <span className="text-text-muted text-[11px]">→</span>
                    )}
                  </React.Fragment>
                ))}
              </div>
            </div>

            {/* Decoupling Recommendation */}
            {cycle.decoupling_recommendation && (
              <div className="flex items-start gap-2 bg-primary/5 border border-primary/20 rounded p-2.5 text-[12px]">
                <span className="text-primary font-semibold flex-shrink-0 text-[11px] uppercase tracking-wider">
                  Decoupling Advice:
                </span>
                <span className="text-text-secondary">{cycle.decoupling_recommendation}</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
