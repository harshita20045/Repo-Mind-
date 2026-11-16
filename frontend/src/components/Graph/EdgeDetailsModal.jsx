import React from 'react';
import Modal from '../ui/Modal';

export default function EdgeDetailsModal({ edge, allNodes = [], onClose }) {
  if (!edge) return null;

  const sourceNode = allNodes.find((n) => n.id === edge.source || n.id === edge.source_node_id);
  const targetNode = allNodes.find((n) => n.id === edge.target || n.id === edge.target_node_id);

  const isInferred = edge.is_inferred || false;
  const evidence = edge.evidence || edge.metadata || {};

  return (
    <Modal
      isOpen={!!edge}
      onClose={onClose}
      title="Graph Relationship Inspection"
      subtitle="Architectural connection details between indexed components"
      size="sm"
    >
      <div className="space-y-4 text-xs">
        {/* Source and Target Chain */}
        <div className="p-3 rounded-lg bg-surfaceHighlight/40 border border-white/[0.08] flex items-center justify-between gap-3">
          <div className="min-w-0">
            <span className="text-[10px] uppercase font-bold text-text-muted block">Source Entity</span>
            <span className="font-semibold text-text-primary text-sm truncate block">
              {sourceNode?.name || `Node #${edge.source || edge.source_node_id}`}
            </span>
            <span className="font-mono text-[11px] text-text-muted truncate block">
              {sourceNode?.file_path}
            </span>
          </div>

          <div className="flex flex-col items-center flex-shrink-0">
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-primary/20 text-primary border border-primary/30 uppercase font-bold">
              {edge.relation_type}
            </span>
            <span className="text-text-muted text-sm mt-0.5">→</span>
          </div>

          <div className="min-w-0 text-right">
            <span className="text-[10px] uppercase font-bold text-text-muted block">Target Entity</span>
            <span className="font-semibold text-text-primary text-sm truncate block">
              {targetNode?.name || `Node #${edge.target || edge.target_node_id}`}
            </span>
            <span className="font-mono text-[11px] text-text-muted truncate block">
              {targetNode?.file_path}
            </span>
          </div>
        </div>

        {/* Verification Status */}
        <div className="flex items-center justify-between p-2.5 rounded-lg border border-white/[0.06] bg-surfaceHighlight/20">
          <span className="text-text-muted">Relationship Provenance:</span>
          {isInferred ? (
            <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium">
              Inferred Transitive Impact
            </span>
          ) : (
            <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
              Direct AST Extracted
            </span>
          )}
        </div>

        {/* Evidence details */}
        {evidence && Object.keys(evidence).length > 0 && (
          <div className="space-y-1.5">
            <span className="text-[10px] font-semibold uppercase text-text-muted tracking-wider block">
              Extraction Evidence
            </span>
            <pre className="p-2.5 rounded-lg bg-black/40 border border-white/[0.06] font-mono text-[11px] text-text-secondary overflow-x-auto whitespace-pre-wrap">
              {JSON.stringify(evidence, null, 2)}
            </pre>
          </div>
        )}

        <div className="flex justify-end pt-2">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-surfaceHighlight hover:bg-white/[0.08] text-text-primary text-xs font-medium transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </Modal>
  );
}

