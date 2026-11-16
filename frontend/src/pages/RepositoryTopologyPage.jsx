import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { intelligenceApi, orgApi } from '../lib/api';
import MermaidViewer from '../components/Onboarding/MermaidViewer';
import { Button } from '../components/ui/Button';
import { StatusBadge, Badge } from '../components/ui/Badge';
import { SectionCard } from '../components/ui/Card';
import { TableRowSkeleton } from '../components/ui/LoadingSkeleton';
import ArchitectureDashboard from '../components/Architecture/ArchitectureDashboard';

export default function RepositoryTopologyPage() {
  const { rid } = useParams();
  const repoId = parseInt(rid, 10);
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState('architecture'); // architecture, graph, symbols, dependencies
  const [symbolSearch, setSymbolSearch] = useState('');
  const [symbolFilter, setSymbolFilter] = useState('');
  const [nodeTypeFilter, setNodeTypeFilter] = useState('');
  const [depSearch, setDepSearch] = useState('');
  const [actionMsg, setActionMsg] = useState(null);

  // Queries
  const { data: repo, isLoading: loadingRepo } = useQuery({
    queryKey: ['repository', repoId],
    queryFn: () => orgApi.getRepository(repoId),
    enabled: !!repoId,
  });

  const { data: summary, isLoading: loadingSummary, refetch: refetchSummary } = useQuery({
    queryKey: ['intelligence-summary', repoId],
    queryFn: () => intelligenceApi.getSummary(repoId),
    enabled: !!repoId,
  });

  const { data: graphData, isLoading: loadingGraph } = useQuery({
    queryKey: ['intelligence-graph', repoId, nodeTypeFilter],
    queryFn: () => intelligenceApi.getGraph(repoId, { nodeType: nodeTypeFilter, limit: 150 }),
    enabled: !!repoId && activeTab === 'graph',
  });

  const { data: symbols = [], isLoading: loadingSymbols } = useQuery({
    queryKey: ['intelligence-symbols', repoId, symbolFilter, symbolSearch],
    queryFn: () => intelligenceApi.getSymbols(repoId, { symbolType: symbolFilter, search: symbolSearch, limit: 100 }),
    enabled: !!repoId && activeTab === 'symbols',
  });

  const { data: dependencies = [], isLoading: loadingDeps } = useQuery({
    queryKey: ['intelligence-dependencies', repoId],
    queryFn: () => intelligenceApi.getDependencies(repoId),
    enabled: !!repoId && (activeTab === 'dependencies' || activeTab === 'architecture'),
  });

  // Re-index Mutation
  const triggerIndexMutation = useMutation({
    mutationFn: () => intelligenceApi.triggerIndex(repoId),
    onSuccess: (data) => {
      setActionMsg(data.message || 'Indexing triggered successfully.');
      queryClient.invalidateQueries({ queryKey: ['intelligence-summary', repoId] });
      queryClient.invalidateQueries({ queryKey: ['repository', repoId] });
      setTimeout(() => setActionMsg(null), 5000);
    },
    onError: (err) => {
      setActionMsg(`Failed to trigger indexing: ${err.message}`);
    },
  });

  const stats = summary?.stats || {};
  const frameworks = summary?.frameworks || [];
  const entryPoints = summary?.entry_points || [];

  return (
    <div className="space-y-6 animate-slide-up">
      {/* Breadcrumb & Navigation */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-text-muted">
          <Link to="/repositories" className="hover:text-primary transition-colors">Repositories</Link>
          <span>/</span>
          <span className="text-text-primary font-medium">{repo?.github_name || `Repository #${repoId}`}</span>
          <span>/</span>
          <span className="text-primary font-medium">Topology & Architecture</span>
        </div>
        <div className="flex items-center gap-2">
          <Link to={`/repositories/${repoId}/guide`}>
            <Button variant="secondary" size="sm">Codebase Guide</Button>
          </Link>
          <Button
            variant="primary"
            size="sm"
            onClick={() => triggerIndexMutation.mutate()}
            disabled={triggerIndexMutation.isPending || repo?.index_status === 'indexing'}
          >
            {triggerIndexMutation.isPending ? 'Queuing...' : 'Re-Index Repository'}
          </Button>
        </div>
      </div>

      {actionMsg && (
        <div className="p-3.5 rounded-lg bg-primary/10 border border-primary/20 text-sm text-primary flex items-center justify-between">
          <span>{actionMsg}</span>
          <button onClick={() => setActionMsg(null)} className="text-xs opacity-70 hover:opacity-100">Dismiss</button>
        </div>
      )}

      {/* Header Banner */}
      <div className="rounded-xl border border-white/[0.08] bg-surface/50 p-6 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-text-primary tracking-tight">
                {repo ? `${repo.github_owner}/${repo.github_name}` : 'Repository Intelligence'}
              </h1>
              <StatusBadge status={repo?.index_status || 'indexed'} label={repo?.index_status || 'Indexed'} />
            </div>
            <p className="text-sm text-text-muted mt-1.5 max-w-2xl">
              {summary?.architecture_summary || 'Deep structural architecture map, AST symbols, package dependencies, and relational call graph.'}
            </p>
          </div>
          <div className="flex flex-wrap gap-2 items-center">
            {frameworks.map((fw) => (
              <Badge key={fw} variant="neutral" className="bg-primary/10 text-primary border-primary/20">
                {fw}
              </Badge>
            ))}
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6 pt-6 border-t border-white/[0.06]">
          <div>
            <div className="text-xs uppercase font-semibold text-text-muted">Primary Language</div>
            <div className="text-lg font-bold text-text-primary mt-1">
              {summary?.primary_language || 'Detecting...'}
            </div>
          </div>
          <div>
            <div className="text-xs uppercase font-semibold text-text-muted">Indexed Symbols</div>
            <div className="text-lg font-bold text-text-primary mt-1">
              {stats.nodes_count ?? stats.symbol_count ?? '—'}
            </div>
          </div>
          <div>
            <div className="text-xs uppercase font-semibold text-text-muted">Graph Relationships</div>
            <div className="text-lg font-bold text-text-primary mt-1">
              {stats.edges_count ?? stats.edge_count ?? '—'}
            </div>
          </div>
          <div>
            <div className="text-xs uppercase font-semibold text-text-muted">Dependencies</div>
            <div className="text-lg font-bold text-text-primary mt-1">
              {dependencies.length || stats.dependencies_count || 0}
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex items-center gap-2 border-b border-white/[0.08] pb-1">
        <button
          onClick={() => setActiveTab('architecture')}
          className={`px-4 py-2 text-sm font-medium rounded-lg transition-all ${
            activeTab === 'architecture'
              ? 'bg-primary/15 text-primary border border-primary/30'
              : 'text-text-muted hover:text-text-primary hover:bg-white/[0.04]'
          }`}
        >
          Architecture & Subsystems
        </button>
        <button
          onClick={() => setActiveTab('graph')}
          className={`px-4 py-2 text-sm font-medium rounded-lg transition-all ${
            activeTab === 'graph'
              ? 'bg-primary/15 text-primary border border-primary/30'
              : 'text-text-muted hover:text-text-primary hover:bg-white/[0.04]'
          }`}
        >
          Code Knowledge Graph
        </button>
        <button
          onClick={() => setActiveTab('symbols')}
          className={`px-4 py-2 text-sm font-medium rounded-lg transition-all ${
            activeTab === 'symbols'
              ? 'bg-primary/15 text-primary border border-primary/30'
              : 'text-text-muted hover:text-text-primary hover:bg-white/[0.04]'
          }`}
        >
          Symbols & Methods
        </button>
        <button
          onClick={() => setActiveTab('dependencies')}
          className={`px-4 py-2 text-sm font-medium rounded-lg transition-all ${
            activeTab === 'dependencies'
              ? 'bg-primary/15 text-primary border border-primary/30'
              : 'text-text-muted hover:text-text-primary hover:bg-white/[0.04]'
          }`}
        >
          Package Dependencies ({dependencies.length})
        </button>
      </div>

      {/* Tab 1: Architecture Intelligence & Health */}
      {activeTab === 'architecture' && (
        <ArchitectureDashboard repositoryId={repoId} />
      )}

      {/* Tab 2: Code Knowledge Graph */}
      {activeTab === 'graph' && (
        <SectionCard
          title="Knowledge Graph Relationships"
          action={
            <select
              value={nodeTypeFilter}
              onChange={(e) => setNodeTypeFilter(e.target.value)}
              className="bg-surfaceHighlight/40 border border-white/[0.09] text-xs rounded-lg px-2.5 py-1.5 text-text-primary focus:outline-none"
            >
              <option value="">All Node Types</option>
              <option value="api_endpoint">API Endpoints</option>
              <option value="db_model">Database Models</option>
              <option value="class">Classes</option>
              <option value="function">Functions</option>
              <option value="file">Files</option>
              <option value="module">Modules</option>
            </select>
          }
        >
          {loadingGraph ? (
            <div className="p-8 text-center text-text-muted">Loading graph nodes and edges...</div>
          ) : graphData?.nodes?.length === 0 ? (
            <div className="p-8 text-center text-text-muted">No nodes found for this filter.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-white/[0.08] text-xs font-semibold text-text-muted uppercase">
                    <th className="py-2.5 px-3">Type</th>
                    <th className="py-2.5 px-3">Entity Name</th>
                    <th className="py-2.5 px-3">File Path</th>
                    <th className="py-2.5 px-3">Lines</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.04]">
                  {graphData?.nodes?.map((n) => (
                    <tr key={n.id} className="hover:bg-white/[0.02]">
                      <td className="py-2 px-3">
                        <span className="text-xs px-2 py-0.5 rounded bg-white/[0.06] font-mono">{n.node_type}</span>
                      </td>
                      <td className="py-2 px-3 font-semibold text-text-primary">{n.name}</td>
                      <td className="py-2 px-3 font-mono text-xs text-text-muted">{n.file_path}</td>
                      <td className="py-2 px-3 text-xs text-text-muted">{n.start_line ? `L${n.start_line}-L${n.end_line}` : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </SectionCard>
      )}

      {/* Tab 3: Symbols & Methods */}
      {activeTab === 'symbols' && (
        <SectionCard
          title="Extracted AST Symbols"
          action={
            <div className="flex items-center gap-2">
              <input
                type="text"
                placeholder="Search symbol..."
                value={symbolSearch}
                onChange={(e) => setSymbolSearch(e.target.value)}
                className="bg-surfaceHighlight/40 border border-white/[0.09] text-xs rounded-lg px-3 py-1.5 text-text-primary focus:outline-none"
              />
              <select
                value={symbolFilter}
                onChange={(e) => setSymbolFilter(e.target.value)}
                className="bg-surfaceHighlight/40 border border-white/[0.09] text-xs rounded-lg px-2.5 py-1.5 text-text-primary focus:outline-none"
              >
                <option value="">All Types</option>
                <option value="class">Class</option>
                <option value="function">Function</option>
                <option value="method">Method</option>
                <option value="api_endpoint">API Endpoint</option>
                <option value="db_model">DB Model</option>
              </select>
            </div>
          }
        >
          {loadingSymbols ? (
            <div className="p-8 text-center text-text-muted">Loading symbols...</div>
          ) : symbols.length === 0 ? (
            <div className="p-8 text-center text-text-muted">No matching symbols found.</div>
          ) : (
            <div className="space-y-3">
              {symbols.map((sym, idx) => (
                <div key={idx} className="p-3.5 rounded-lg border border-white/[0.06] bg-surfaceHighlight/20 flex flex-col gap-1.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-bold text-text-primary">{sym.name}</span>
                      <Badge variant="neutral">{sym.symbol_type}</Badge>
                      {sym.parent_symbol && (
                        <span className="text-xs text-text-muted font-mono">in {sym.parent_symbol}</span>
                      )}
                    </div>
                    <span className="text-xs text-text-muted font-mono">
                      {sym.start_line ? `L${sym.start_line} - L${sym.end_line}` : ''}
                    </span>
                  </div>
                  {sym.signature && (
                    <div className="text-xs font-mono text-text-muted bg-black/20 p-1.5 rounded">
                      {sym.signature}
                    </div>
                  )}
                  {sym.docstring && (
                    <p className="text-xs text-text-secondary italic line-clamp-2">{sym.docstring}</p>
                  )}
                  <div className="text-xs text-text-muted font-mono">{sym.file_path}</div>
                </div>
              ))}
            </div>
          )}
        </SectionCard>
      )}

      {/* Tab 4: Package Dependencies */}
      {activeTab === 'dependencies' && (
        <SectionCard
          title="Cataloged Package Dependencies"
          action={
            <input
              type="text"
              placeholder="Search package..."
              value={depSearch}
              onChange={(e) => setDepSearch(e.target.value)}
              className="bg-surfaceHighlight/40 border border-white/[0.09] text-xs rounded-lg px-3 py-1.5 text-text-primary focus:outline-none"
            />
          }
        >
          {loadingDeps ? (
            <div className="p-8 text-center text-text-muted">Loading dependencies...</div>
          ) : dependencies.length === 0 ? (
            <div className="p-8 text-center text-text-muted">No external package dependencies cataloged.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-white/[0.08] text-xs font-semibold text-text-muted uppercase">
                    <th className="py-2.5 px-3">Ecosystem</th>
                    <th className="py-2.5 px-3">Package Name</th>
                    <th className="py-2.5 px-3">Version Spec</th>
                    <th className="py-2.5 px-3">Scope</th>
                    <th className="py-2.5 px-3">Manifest File</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.04]">
                  {dependencies
                    .filter((d) => !depSearch || d.package_name.toLowerCase().includes(depSearch.toLowerCase()))
                    .map((d, i) => (
                      <tr key={i} className="hover:bg-white/[0.02]">
                        <td className="py-2 px-3">
                          <span className="text-xs px-2 py-0.5 rounded font-mono uppercase bg-primary/10 text-primary border border-primary/20">
                            {d.ecosystem}
                          </span>
                        </td>
                        <td className="py-2 px-3 font-semibold text-text-primary">{d.package_name}</td>
                        <td className="py-2 px-3 font-mono text-xs text-text-muted">{d.version_spec || 'any'}</td>
                        <td className="py-2 px-3">
                          <span className={`text-xs px-2 py-0.5 rounded ${d.is_dev ? 'bg-amber-500/10 text-amber-400' : 'bg-emerald-500/10 text-emerald-400'}`}>
                            {d.is_dev ? 'Development' : 'Production'}
                          </span>
                        </td>
                        <td className="py-2 px-3 font-mono text-xs text-text-muted">{d.file_path || '—'}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          )}
        </SectionCard>
      )}
    </div>
  );
}
