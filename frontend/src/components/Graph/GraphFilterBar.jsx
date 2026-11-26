import React from 'react';

export default function GraphFilterBar({
  graphMode = 'all',
  onGraphModeChange,
  availableModes = [],
  nodeTypeFilter = 'all',
  onNodeTypeFilterChange,
  searchQuery = '',
  onSearchQueryChange,
  totalNodes = 0,
  totalEdges = 0,
  visibleNodes = 0,
  visibleEdges = 0,
}) {
  const nodeTypes = [
    { id: 'all', label: 'All Entities' },
    { id: 'module', label: 'Modules' },
    { id: 'file', label: 'Files' },
    { id: 'class', label: 'Classes' },
    { id: 'function', label: 'Functions' },
    { id: 'api_endpoint', label: 'APIs' },
    { id: 'db_model', label: 'DB Models' },
  ];

  return (
    <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 p-3 bg-surface/80 border-b border-border backdrop-blur-md">
      {/* Left: Mode selector or tabs */}
      <div className="flex items-center gap-2 flex-wrap">
        {availableModes.length > 0 && (
          <div className="flex items-center rounded-lg bg-surfaceHighlight/50 border border-border p-0.5">
            {availableModes.map((m) => (
              <button
                key={m.id}
                onClick={() => onGraphModeChange && onGraphModeChange(m.id)}
                className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${
                  graphMode === m.id
                    ? 'bg-primary text-background font-bold shadow-sm'
                    : 'text-text-muted hover:text-text-primary'
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>
        )}

        {/* Node Type Filter */}
        <select
          value={nodeTypeFilter}
          onChange={(e) => onNodeTypeFilterChange && onNodeTypeFilterChange(e.target.value)}
          className="bg-surfaceHighlight/60 border border-border text-xs rounded-lg px-2.5 py-1.5 text-text-primary focus:outline-none focus:ring-1 focus:ring-primary/40"
          aria-label="Filter by node type"
        >
          {nodeTypes.map((t) => (
            <option key={t.id} value={t.id} className="bg-surface text-text-primary">
              {t.label}
            </option>
          ))}
        </select>
      </div>

      {/* Right: Search input & Stats indicator */}
      <div className="flex items-center gap-3">
        {/* Search Input */}
        <div className="relative min-w-[200px]">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchQueryChange && onSearchQueryChange(e.target.value)}
            placeholder="Search entity or file..."
            className="w-full bg-surfaceHighlight/50 border border-border text-xs rounded-lg pl-8 pr-3 py-1.5 text-text-primary focus:outline-none focus:ring-1 focus:ring-primary/40 placeholder-text-muted transition-all"
          />
          <svg
            className="w-3.5 h-3.5 text-text-muted absolute left-2.5 top-1/2 -translate-y-1/2"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          {searchQuery && (
            <button
              onClick={() => onSearchQueryChange('')}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary text-xs"
              aria-label="Clear search"
            >
              ×
            </button>
          )}
        </div>

        {/* Stats Chips */}
        <div className="flex items-center gap-2 text-xs font-mono text-text-muted border-l border-border pl-3">
          <span title={`${visibleNodes} visible of ${totalNodes} total nodes`}>
            <span className="text-text-primary font-semibold">{visibleNodes}</span>
            <span className="text-[10px] opacity-60">/{totalNodes}</span> nodes
          </span>
          <span className="text-white/20">•</span>
          <span title={`${visibleEdges} visible of ${totalEdges} total edges`}>
            <span className="text-text-primary font-semibold">{visibleEdges}</span> edges
          </span>
        </div>
      </div>
    </div>
  );
}

