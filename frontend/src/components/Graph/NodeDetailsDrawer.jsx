import React, { useState } from 'react';
import { Link } from 'react-router-dom';

export default function NodeDetailsDrawer({
  node,
  allNodes = [],
  edges = [],
  repositoryId,
  onClose,
  onSelectNode,
}) {
  const [activeTab, setActiveTab] = useState('summary'); // summary, dependencies, dependents, related

  if (!node) return null;

  const outgoingConnections = edges
    .filter((e) => e.source === node.id)
    .map((e) => {
      const targetNode = allNodes.find((n) => n.id === e.target);
      return { edge: e, targetNode };
    })
    .filter((item) => item.targetNode);

  const incomingConnections = edges
    .filter((e) => e.target === node.id)
    .map((e) => {
      const sourceNode = allNodes.find((n) => n.id === e.source);
      return { edge: e, sourceNode };
    })
    .filter((item) => item.sourceNode);

  const metadata = node.metadata || {};
  const docstring = metadata.docstring || null;
  const signature = metadata.signature || null;
  const apiRoute = metadata.api_route || null;

  return (
    <div className="absolute top-0 right-0 w-96 h-full bg-surface/95 border-l border-white/10 backdrop-blur-xl shadow-2xl z-30 flex flex-col animate-slide-left overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-white/[0.08] flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span
              className="text-[10px] uppercase font-bold font-mono px-2 py-0.5 rounded border"
              style={{
                backgroundColor: `${node.style?.bg}30`,
                borderColor: `${node.style?.border}60`,
                color: node.style?.text || '#ffffff',
              }}
            >
              {node.node_type}
            </span>
            <span className="text-xs text-text-muted font-mono">ID: #{node.id}</span>
          </div>
          <h3 className="text-base font-bold text-text-primary truncate tracking-tight" title={node.name}>
            {node.name}
          </h3>
          <p className="text-xs font-mono text-text-muted truncate mt-0.5" title={node.file_path}>
            {node.file_path}
          </p>
        </div>

        <button
          onClick={onClose}
          className="w-7 h-7 flex items-center justify-center rounded-lg text-text-muted hover:text-text-primary hover:bg-white/[0.08] transition-colors flex-shrink-0"
          aria-label="Close details drawer"
        >
          ✕
        </button>
      </div>

      {/* Tabs */}
      <div className="flex items-center border-b border-white/[0.08] px-3 bg-surfaceHighlight/30 text-xs">
        <button
          onClick={() => setActiveTab('summary')}
          className={`py-2 px-2.5 font-medium border-b-2 transition-colors ${
            activeTab === 'summary'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-text-muted hover:text-text-primary'
          }`}
        >
          Overview
        </button>
        <button
          onClick={() => setActiveTab('dependencies')}
          className={`py-2 px-2.5 font-medium border-b-2 transition-colors flex items-center gap-1 ${
            activeTab === 'dependencies'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-text-muted hover:text-text-primary'
          }`}
        >
          <span>Depends On</span>
          <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-white/[0.08]">
            {outgoingConnections.length}
          </span>
        </button>
        <button
          onClick={() => setActiveTab('dependents')}
          className={`py-2 px-2.5 font-medium border-b-2 transition-colors flex items-center gap-1 ${
            activeTab === 'dependents'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-text-muted hover:text-text-primary'
          }`}
        >
          <span>Used By</span>
          <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-white/[0.08]">
            {incomingConnections.length}
          </span>
        </button>
        <button
          onClick={() => setActiveTab('related')}
          className={`py-2 px-2.5 font-medium border-b-2 transition-colors ${
            activeTab === 'related'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-text-muted hover:text-text-primary'
          }`}
        >
          Actions
        </button>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* TAB 1: Summary */}
        {activeTab === 'summary' && (
          <div className="space-y-4 text-xs">
            {/* Degree Chips */}
            <div className="grid grid-cols-2 gap-2">
              <div className="p-2.5 rounded-lg bg-surfaceHighlight/40 border border-white/[0.06]">
                <div className="text-[10px] uppercase font-semibold text-text-muted">In-Degree (Used By)</div>
                <div className="text-lg font-bold text-emerald-400 mt-0.5">{incomingConnections.length}</div>
              </div>
              <div className="p-2.5 rounded-lg bg-surfaceHighlight/40 border border-white/[0.06]">
                <div className="text-[10px] uppercase font-semibold text-text-muted">Out-Degree (Calls)</div>
                <div className="text-lg font-bold text-cyan-400 mt-0.5">{outgoingConnections.length}</div>
              </div>
            </div>

            {/* Line Range */}
            {node.start_line && (
              <div className="p-2.5 rounded-lg bg-surfaceHighlight/30 border border-white/[0.06] flex items-center justify-between">
                <span className="text-text-muted">Source Code Lines:</span>
                <span className="font-mono font-bold text-text-primary">
                  L{node.start_line} - L{node.end_line || node.start_line}
                </span>
              </div>
            )}

            {/* API Endpoint Spec if available */}
            {apiRoute && (
              <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 space-y-1">
                <span className="text-[10px] uppercase font-bold text-emerald-400 tracking-wider">
                  HTTP Endpoint
                </span>
                <div className="flex items-center gap-2 font-mono text-xs">
                  <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-bold uppercase">
                    {apiRoute.method || 'GET'}
                  </span>
                  <span className="text-text-primary font-semibold">{apiRoute.path}</span>
                </div>
              </div>
            )}

            {/* Signature */}
            {signature && (
              <div className="space-y-1">
                <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider">
                  Signature
                </span>
                <pre className="p-2.5 rounded-lg bg-black/40 border border-white/[0.06] font-mono text-[11px] text-primary overflow-x-auto whitespace-pre-wrap">
                  {signature}
                </pre>
              </div>
            )}

            {/* Docstring */}
            {docstring ? (
              <div className="space-y-1">
                <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider">
                  Documentation
                </span>
                <div className="p-2.5 rounded-lg bg-surfaceHighlight/30 border border-white/[0.06] text-text-secondary leading-relaxed italic whitespace-pre-line">
                  {docstring}
                </div>
              </div>
            ) : (
              <div className="p-2.5 rounded-lg bg-surfaceHighlight/20 border border-white/[0.04] text-text-muted italic text-center">
                No inline documentation string found in AST.
              </div>
            )}
          </div>
        )}

        {/* TAB 2: Dependencies (Outgoing) */}
        {activeTab === 'dependencies' && (
          <div className="space-y-2">
            {outgoingConnections.length === 0 ? (
              <div className="p-6 text-center text-text-muted text-xs">
                This entity has zero outbound dependencies.
              </div>
            ) : (
              outgoingConnections.map(({ edge, targetNode }) => (
                <div
                  key={edge.id}
                  onClick={() => onSelectNode && onSelectNode(targetNode.id)}
                  className="p-2.5 rounded-lg border border-white/[0.06] bg-surfaceHighlight/20 hover:bg-surfaceHighlight/60 hover:border-cyan-500/30 transition-all cursor-pointer group"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-text-primary group-hover:text-cyan-400 transition-colors text-xs truncate">
                      {targetNode.name}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 font-mono">
                      {edge.relation_type}
                    </span>
                  </div>
                  <div className="text-[11px] text-text-muted font-mono truncate mt-0.5">
                    {targetNode.file_path}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* TAB 3: Dependents (Incoming) */}
        {activeTab === 'dependents' && (
          <div className="space-y-2">
            {incomingConnections.length === 0 ? (
              <div className="p-6 text-center text-text-muted text-xs">
                No other components directly depend on this entity.
              </div>
            ) : (
              incomingConnections.map(({ edge, sourceNode }) => (
                <div
                  key={edge.id}
                  onClick={() => onSelectNode && onSelectNode(sourceNode.id)}
                  className="p-2.5 rounded-lg border border-white/[0.06] bg-surfaceHighlight/20 hover:bg-surfaceHighlight/60 hover:border-emerald-500/30 transition-all cursor-pointer group"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-text-primary group-hover:text-emerald-400 transition-colors text-xs truncate">
                      {sourceNode.name}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-mono">
                      {edge.relation_type}
                    </span>
                  </div>
                  <div className="text-[11px] text-text-muted font-mono truncate mt-0.5">
                    {sourceNode.file_path}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* TAB 4: Navigation & Cross-Module Actions */}
        {activeTab === 'related' && (
          <div className="space-y-3">
            <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider block">
              Cross-Platform Navigation
            </span>

            {/* Link to Topology / Architecture */}
            <Link
              to={`/repositories/${repositoryId}/topology`}
              className="flex items-center justify-between p-2.5 rounded-lg border border-white/[0.08] bg-surfaceHighlight/30 hover:bg-surfaceHighlight hover:border-primary/40 transition-all text-xs text-text-primary"
            >
              <div className="flex items-center gap-2">
                <span className="text-primary">🏛️</span>
                <span>Architecture Explorer</span>
              </div>
              <span className="text-text-muted">→</span>
            </Link>

            {/* Link to Codebase Guide */}
            <Link
              to={`/repositories/${repositoryId}/guide`}
              className="flex items-center justify-between p-2.5 rounded-lg border border-white/[0.08] bg-surfaceHighlight/30 hover:bg-surfaceHighlight hover:border-primary/40 transition-all text-xs text-text-primary"
            >
              <div className="flex items-center gap-2">
                <span className="text-emerald-400">📖</span>
                <span>Developer Onboarding Blueprint</span>
              </div>
              <span className="text-text-muted">→</span>
            </Link>

            {/* Link to Pull Requests */}
            <Link
              to={`/repositories/${repositoryId}/pull-requests`}
              className="flex items-center justify-between p-2.5 rounded-lg border border-white/[0.08] bg-surfaceHighlight/30 hover:bg-surfaceHighlight hover:border-info/40 transition-all text-xs text-text-primary"
            >
              <div className="flex items-center gap-2">
                <span className="text-info">🔀</span>
                <span>Pull Request Reviews</span>
              </div>
              <span className="text-text-muted">→</span>
            </Link>

            {/* Link to History */}
            <Link
              to={`/repositories/${repositoryId}/history`}
              className="flex items-center justify-between p-2.5 rounded-lg border border-white/[0.08] bg-surfaceHighlight/30 hover:bg-surfaceHighlight hover:border-purple-400/40 transition-all text-xs text-text-primary"
            >
              <div className="flex items-center gap-2">
                <span className="text-purple-400">📜</span>
                <span>Historical Code Intel & ADRs</span>
              </div>
              <span className="text-text-muted">→</span>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}

