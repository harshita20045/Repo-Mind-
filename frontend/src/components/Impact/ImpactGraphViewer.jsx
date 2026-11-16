import React, { useState } from 'react';
import MermaidViewer from '../Onboarding/MermaidViewer';

export default function ImpactGraphViewer({ graphVisualization }) {
  const [activeView, setActiveView] = useState('diagram');
  const [copied, setCopied] = useState(false);

  const mermaidChart = graphVisualization?.mermaid || '';
  const nodes = graphVisualization?.nodes || [];
  const edges = graphVisualization?.edges || [];

  const handleCopyMermaid = () => {
    if (!mermaidChart) return;
    navigator.clipboard.writeText(mermaidChart);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!mermaidChart && nodes.length === 0) {
    return (
      <div className="bg-surface border border-border rounded-lg p-6 text-center text-text-muted text-[13px]">
        No dependency graph available for this change set.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-surface border border-border rounded-lg p-4">
        <div>
          <h3 className="text-sm font-semibold text-text-primary">
            Blast Radius Dependency Graph
          </h3>
          <p className="text-[12px] text-text-secondary mt-0.5">
            Interactive visualization of modified nodes and outbound blast radius along caller dependencies.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center rounded border border-border bg-surfaceHighlight p-0.5">
            <button
              onClick={() => setActiveView('diagram')}
              className={`px-2.5 py-1 text-xs font-medium rounded transition-colors ${
                activeView === 'diagram'
                  ? 'bg-primary text-white shadow-sm'
                  : 'text-text-muted hover:text-text-primary'
              }`}
            >
              Diagram
            </button>
            <button
              onClick={() => setActiveView('nodes')}
              className={`px-2.5 py-1 text-xs font-medium rounded transition-colors ${
                activeView === 'nodes'
                  ? 'bg-primary text-white shadow-sm'
                  : 'text-text-muted hover:text-text-primary'
              }`}
            >
              Nodes ({nodes.length})
            </button>
          </div>

          {mermaidChart && (
            <button
              onClick={handleCopyMermaid}
              className="px-2.5 py-1 text-xs font-medium rounded bg-surface border border-border text-text-secondary hover:text-text-primary transition-colors flex items-center gap-1.5"
            >
              {copied ? 'Copied' : 'Copy Mermaid'}
            </button>
          )}
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 flex-wrap text-[11px] px-2 text-text-secondary">
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded bg-red-500/80 border border-red-400 inline-block" />
          <span>Changed Origin</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded bg-amber-500/80 border border-amber-400 inline-block" />
          <span>Direct Dependent (Hop 1)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded bg-blue-500/80 border border-blue-400 inline-block" />
          <span>Indirect Dependent (Hop 2-3)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded bg-purple-500/80 border border-purple-400 inline-block" />
          <span>Breaking Mutation</span>
        </div>
      </div>

      {/* Content Area */}
      {activeView === 'diagram' ? (
        <div className="bg-surface border border-border rounded-lg p-5 overflow-x-auto min-h-[350px] flex items-center justify-center">
          {mermaidChart ? (
            <MermaidViewer chart={mermaidChart} />
          ) : (
            <div className="text-text-muted text-xs">No diagram syntax generated.</div>
          )}
        </div>
      ) : (
        <div className="bg-surface border border-border rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-surfaceHighlight/50 border-b border-border text-text-muted uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="p-3">Node Name</th>
                  <th className="p-3">Type</th>
                  <th className="p-3">Impact Tier</th>
                  <th className="p-3">File Path</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {nodes.map((node, idx) => (
                  <tr key={idx} className="hover:bg-white/[0.02] transition-colors">
                    <td className="p-3 font-mono font-semibold text-text-primary">
                      {node.name || node.id}
                    </td>
                    <td className="p-3">
                      <span className="font-mono text-[10px] uppercase px-1.5 py-0.5 rounded bg-surfaceHighlight text-text-muted border border-border">
                        {node.type || 'component'}
                      </span>
                    </td>
                    <td className="p-3">
                      <span className="font-medium capitalize text-text-secondary">
                        {node.impact_tier?.replace(/_/g, ' ') || 'Dependent'}
                      </span>
                    </td>
                    <td className="p-3 font-mono text-[11px] text-text-muted truncate max-w-xs">
                      {node.file_path || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
