import React from 'react';

export default function FlowAnalysisViewer({ flows = [] }) {
  if (flows.length === 0) {
    return (
      <div className="bg-surface border border-border rounded-lg p-8 text-center text-text-muted text-[13px]">
        No execution flows cataloged. Ensure repository has been scanned and routes indexed.
      </div>
    );
  }

  const cleanFlows = flows.filter(f => !f.is_leaky);
  const leakyFlows = flows.filter(f => f.is_leaky);

  return (
    <div className="space-y-4">
      {/* Summary Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-surface border border-border rounded-lg p-4">
        <div>
          <h3 className="text-sm font-semibold text-text-primary">
            API-to-Service-to-Database Flow Inspection
          </h3>
          <p className="text-[12px] text-text-secondary mt-0.5">
            Traces endpoint execution chains to identify leaky controllers bypassing the service layer.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="px-2.5 py-1 rounded bg-success/10 text-success border border-success/20">
            {cleanFlows.length} Clean Flows
          </span>
          {leakyFlows.length > 0 && (
            <span className="px-2.5 py-1 rounded bg-danger/10 text-danger border border-danger/20 font-bold">
              {leakyFlows.length} Leaky Bypasses
            </span>
          )}
        </div>
      </div>

      {/* Leaky Flows Alert Section */}
      {leakyFlows.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-danger flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-danger animate-pulse" />
            <span>Leaky Abstraction Endpoints</span>
          </h4>
          {leakyFlows.map((flow, idx) => (
            <div
              key={idx}
              className="bg-surface border border-danger/30 rounded-lg p-4 transition-colors hover:border-danger/50"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono uppercase bg-danger/10 text-danger border border-danger/20">
                    Direct DB Access
                  </span>
                  <span className="font-mono text-xs font-semibold text-text-primary">
                    {flow.endpoint_name}
                  </span>
                </div>
                <span className="font-mono text-[11px] text-text-muted">
                  {flow.route_file}
                </span>
              </div>

              <div className="flex items-center gap-2 text-xs font-mono my-2.5 bg-surfaceHighlight/50 p-2.5 rounded border border-border">
                <span className="px-2 py-0.5 rounded bg-surface border border-border text-text-primary">
                  {flow.endpoint_name}
                </span>
                <span className="text-danger font-bold">→ ⚠️ Direct Bypass →</span>
                <span className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/20 font-bold">
                  {flow.model_name || 'DB Query'}
                </span>
              </div>

              <p className="text-[12px] text-text-secondary leading-relaxed mb-2">
                {flow.evidence}
              </p>

              {flow.suggested_fix && (
                <div className="flex items-start gap-2 bg-primary/5 border border-primary/20 rounded p-2 text-[12px]">
                  <span className="text-primary font-semibold flex-shrink-0 text-[11px] uppercase tracking-wider">
                    Remediation:
                  </span>
                  <span className="text-text-secondary">{flow.suggested_fix}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Clean Flows Section */}
      <div className="space-y-3">
        <h4 className="text-xs font-bold uppercase tracking-wider text-text-muted">
          Clean Multi-Tier Flows ({cleanFlows.length})
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {cleanFlows.map((flow, idx) => (
            <div
              key={idx}
              className="bg-surface border border-border rounded-lg p-3.5 space-y-2 hover:border-white/20 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-semibold text-text-primary">
                  {flow.endpoint_name}
                </span>
                <span className="text-[10px] font-bold uppercase px-1.5 py-0.5 rounded bg-success/10 text-success border border-success/20">
                  Clean Flow
                </span>
              </div>

              <div className="flex items-center gap-1.5 text-[11px] font-mono text-text-muted">
                <span className="text-text-primary truncate max-w-[120px]">{flow.endpoint_path}</span>
                <span>→</span>
                <span className="text-primary truncate max-w-[120px]">{flow.service_name || 'Service'}</span>
                <span>→</span>
                <span className="text-text-secondary truncate max-w-[120px]">{flow.model_name || 'DB'}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
