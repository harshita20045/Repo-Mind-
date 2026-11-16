import React, { useState, useMemo } from 'react';
import { SeverityBadge } from '../ui/Badge';

const TIER_CONFIG = {
  directly_affected: {
    label: 'Direct Dependent',
    color: 'border-rose-500/30 bg-rose-500/5 text-rose-300',
    badge: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
  },
  indirectly_affected: {
    label: 'Indirect Dependent',
    color: 'border-amber-500/30 bg-amber-500/5 text-amber-300',
    badge: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  },
  potentially_affected: {
    label: 'Potentially Affected',
    color: 'border-cyan-500/30 bg-cyan-500/5 text-cyan-300',
    badge: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  },
  no_identified_impact: {
    label: 'No Identified Impact',
    color: 'border-white/10 bg-white/5 text-text-muted',
    badge: 'bg-white/5 text-text-muted border-white/10',
  },
};

export default function AffectedComponentList({ affectedComponents = [] }) {
  const [filterTier, setFilterTier] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  const counts = useMemo(() => {
    return {
      all: affectedComponents.length,
      directly_affected: affectedComponents.filter(c => c.impact_tier === 'directly_affected').length,
      indirectly_affected: affectedComponents.filter(c => c.impact_tier === 'indirectly_affected').length,
      potentially_affected: affectedComponents.filter(c => c.impact_tier === 'potentially_affected').length,
    };
  }, [affectedComponents]);

  const filteredComponents = useMemo(() => {
    return affectedComponents.filter(item => {
      if (filterTier !== 'all' && item.impact_tier !== filterTier) {
        return false;
      }
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const matchesName = item.component_name?.toLowerCase().includes(query);
        const matchesFile = item.file_path?.toLowerCase().includes(query);
        const matchesReason = item.reason?.toLowerCase().includes(query);
        const matchesType = item.node_type?.toLowerCase().includes(query);
        return matchesName || matchesFile || matchesReason || matchesType;
      }
      return true;
    });
  }, [affectedComponents, filterTier, searchQuery]);

  return (
    <div className="space-y-4">
      {/* Filtering and Search Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-surface border border-border rounded-lg p-3">
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
          <button
            onClick={() => setFilterTier('all')}
            className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
              filterTier === 'all'
                ? 'bg-primary/10 text-primary border border-primary/20'
                : 'text-text-muted hover:text-text-primary'
            }`}
          >
            All ({counts.all})
          </button>
          <button
            onClick={() => setFilterTier('directly_affected')}
            className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
              filterTier === 'directly_affected'
                ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                : 'text-text-muted hover:text-text-primary'
            }`}
          >
            Direct ({counts.directly_affected})
          </button>
          <button
            onClick={() => setFilterTier('indirectly_affected')}
            className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
              filterTier === 'indirectly_affected'
                ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                : 'text-text-muted hover:text-text-primary'
            }`}
          >
            Indirect ({counts.indirectly_affected})
          </button>
          <button
            onClick={() => setFilterTier('potentially_affected')}
            className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
              filterTier === 'potentially_affected'
                ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                : 'text-text-muted hover:text-text-primary'
            }`}
          >
            Potential ({counts.potentially_affected})
          </button>
        </div>

        <div className="relative min-w-[200px]">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search component or file..."
            className="w-full bg-surfaceHighlight border border-border rounded px-3 py-1.5 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary"
          />
        </div>
      </div>

      {/* Component Cards */}
      {filteredComponents.length === 0 ? (
        <div className="bg-surface border border-border rounded-lg p-6 text-center text-text-muted text-[13px]">
          {searchQuery ? 'No affected components match your search filter.' : 'No components identified in this impact category.'}
        </div>
      ) : (
        <div className="space-y-3">
          {filteredComponents.map((item, idx) => {
            const tier = TIER_CONFIG[item.impact_tier] || TIER_CONFIG.no_identified_impact;
            return (
              <div
                key={idx}
                className="bg-surface border border-border rounded-lg p-4 transition-all hover:border-white/20"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider border ${tier.badge}`}>
                      {tier.label}
                    </span>
                    <SeverityBadge severity={item.severity || 'medium'} />
                    {item.node_type && (
                      <span className="text-[10px] uppercase font-bold font-mono px-1.5 py-0.5 rounded bg-surfaceHighlight text-text-muted border border-border">
                        {item.node_type}
                      </span>
                    )}
                    <span className="font-mono text-xs font-semibold text-text-primary">
                      {item.component_name}
                    </span>
                  </div>
                  <span className="font-mono text-[11px] text-text-muted truncate max-w-sm" title={item.file_path}>
                    {item.file_path}{item.line_number ? `:${item.line_number}` : ''}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[12px] my-2">
                  <div className="bg-surfaceHighlight/30 border border-border rounded p-2.5">
                    <span className="text-text-muted block text-[11px] font-medium uppercase tracking-wider mb-1">
                      Relationship
                    </span>
                    <span className="text-text-primary font-mono text-[11px]">
                      {item.relationship || 'Downstream dependent'}
                    </span>
                  </div>

                  <div className="bg-surfaceHighlight/30 border border-border rounded p-2.5">
                    <span className="text-text-muted block text-[11px] font-medium uppercase tracking-wider mb-1">
                      Why Affected
                    </span>
                    <span className="text-text-secondary">
                      {item.reason}
                    </span>
                  </div>
                </div>

                {item.suggested_verification && (
                  <div className="mt-2 text-[12px] bg-primary/5 border border-primary/20 rounded p-2.5 flex items-start gap-2">
                    <span className="text-primary font-semibold flex-shrink-0 text-[11px] uppercase tracking-wider">
                      Suggested Verification:
                    </span>
                    <span className="text-text-secondary">{item.suggested_verification}</span>
                  </div>
                )}

                {item.evidence && (
                  <div className="mt-2 text-[11px] font-mono text-text-muted bg-surfaceHighlight/60 p-2 rounded border border-border">
                    <span className="text-text-muted font-sans font-medium uppercase text-[10px] tracking-wider block mb-0.5">Supporting Evidence</span>
                    {item.evidence}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
