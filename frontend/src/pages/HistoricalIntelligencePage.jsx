import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { historyApi, orgApi } from '../lib/api';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import EmptyState from '../components/ui/EmptyState';
import { PageLoader } from '../components/ui/LoadingSkeleton';
import RepositoryNav from '../components/Layout/RepositoryNav';

export default function HistoricalIntelligencePage() {
  const { rid } = useParams();
  const repoId = parseInt(rid);
  const queryClient = useQueryClient();

  // Active navigation tab
  const [activeTab, setActiveTab] = useState('overview'); // overview | modules | adrs | impact | bugs | similar_prs | hotspots

  // Filters & State
  const [milestoneCategory, setMilestoneCategory] = useState('all');
  const [selectedModule, setSelectedModule] = useState('orders');
  const [adrCategory, setAdrCategory] = useState('all');
  const [adrType, setAdrType] = useState('all');
  const [impactTarget, setImpactTarget] = useState('app/services/order_service.py');
  const [similarPrQuery, setSimilarPrQuery] = useState('');
  const [hotspotCompareFile, setHotspotCompareFile] = useState('');

  // 1. Fetch repository metadata
  const { data: repo, isLoading: loadingRepo } = useQuery({
    queryKey: ['repository', repoId],
    queryFn: () => orgApi.getRepository(repoId),
    enabled: !!repoId,
  });

  // 2. Fetch Evolution Overview Metrics
  const { data: evolutionOverview, isLoading: loadingOverview } = useQuery({
    queryKey: ['evolutionOverview', repoId],
    queryFn: () => historyApi.getEvolutionOverview(repoId),
    enabled: !!repoId,
  });

  // 3. Fetch Evolution Milestones
  const { data: milestones = [], isLoading: loadingMilestones } = useQuery({
    queryKey: ['evolutionMilestones', repoId, milestoneCategory],
    queryFn: () => historyApi.getEvolutionMilestones(repoId, { category: milestoneCategory !== 'all' ? milestoneCategory : undefined }),
    enabled: !!repoId && activeTab === 'overview',
  });

  // 4. Fetch Module Evolution
  const { data: moduleEvolution, isLoading: loadingModuleEvolution } = useQuery({
    queryKey: ['moduleEvolution', repoId, selectedModule],
    queryFn: () => historyApi.getModuleEvolution(repoId, selectedModule),
    enabled: !!repoId && activeTab === 'modules',
  });

  // 5. Fetch Architecture Decision Records (ADRs)
  const { data: adrs = [], isLoading: loadingAdrs } = useQuery({
    queryKey: ['adrs', repoId],
    queryFn: () => historyApi.getAdrs(repoId),
    enabled: !!repoId && activeTab === 'adrs',
  });

  // 6. Fetch Historical Bug Lessons
  const { data: bugLessons = [], isLoading: loadingBugLessons } = useQuery({
    queryKey: ['bugLessons', repoId],
    queryFn: () => historyApi.getBugLessons(repoId),
    enabled: !!repoId && activeTab === 'bugs',
  });

  // 7. Impact Analysis Mutation
  const { mutate: runImpactAnalysis, data: impactResult, isPending: analyzingImpact } = useMutation({
    mutationFn: (target) => historyApi.runImpactAnalysis(repoId, { file_path: target, module_name: target }),
  });

  // 8. Similar PR Search Query
  const { data: similarPrs = [], isLoading: loadingSimilarPrs, refetch: runSimilarPrSearch } = useQuery({
    queryKey: ['similarPrs', repoId, similarPrQuery],
    queryFn: () => historyApi.searchSimilarPrs(repoId, { query: similarPrQuery || undefined, limit: 12 }),
    enabled: !!repoId && activeTab === 'similar_prs',
  });

  // 9. Fetch Recurring Hotspots
  const { data: hotspots = [], isLoading: loadingHotspots } = useQuery({
    queryKey: ['recurringHotspots', repoId],
    queryFn: () => historyApi.getRecurringIssues(repoId),
    enabled: !!repoId && activeTab === 'hotspots',
  });

  // 10. File Change Comparison Query
  const { data: comparison, isLoading: loadingComparison, refetch: runCompare } = useQuery({
    queryKey: ['changeComparison', repoId, hotspotCompareFile],
    queryFn: () => historyApi.compareChanges(repoId, { file_path: hotspotCompareFile }),
    enabled: !!repoId && !!hotspotCompareFile && activeTab === 'hotspots',
  });

  // 11. Trigger Index Mutation
  const { mutate: triggerIndex, isPending: indexing } = useMutation({
    mutationFn: () => historyApi.triggerIndex(repoId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evolutionOverview', repoId] });
      queryClient.invalidateQueries({ queryKey: ['evolutionMilestones', repoId] });
      queryClient.invalidateQueries({ queryKey: ['moduleEvolution', repoId] });
      queryClient.invalidateQueries({ queryKey: ['adrs', repoId] });
      queryClient.invalidateQueries({ queryKey: ['bugLessons', repoId] });
      queryClient.invalidateQueries({ queryKey: ['recurringHotspots', repoId] });
    },
  });

  if (loadingRepo) {
    return <PageLoader message="Loading historical code intelligence…" />;
  }

  const getCategoryBadge = (cat) => {
    switch (cat?.toLowerCase()) {
      case 'architecture': return <Badge variant="primary">Architecture</Badge>;
      case 'api': return <Badge variant="info">API Contract</Badge>;
      case 'database': return <Badge variant="warning">Database</Badge>;
      case 'security': return <Badge variant="critical">Security</Badge>;
      case 'dependency': return <Badge variant="default">Dependency</Badge>;
      case 'performance': return <Badge variant="success">Performance</Badge>;
      default: return <Badge variant="default">{cat}</Badge>;
    }
  };

  const filteredAdrs = adrs.filter(a => {
    const matchCat = adrCategory === 'all' || (a.decision_category?.toLowerCase() === adrCategory.toLowerCase());
    const matchType = adrType === 'all' || (a.decision_type?.toLowerCase() === adrType.toLowerCase());
    return matchCat && matchType;
  });

  return (
    <div className="flex flex-col gap-6 animate-slide-up max-w-7xl mx-auto pb-12">
      {/* Sub-Navigation Bar */}
      <RepositoryNav repositoryId={repoId} currentTab="history" />

      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-text-muted">
        <Link to="/repositories" className="hover:text-text-primary transition-colors">Repositories</Link>
        <span>/</span>
        <span className="text-text-secondary">{repo?.github_owner}/{repo?.github_name}</span>
        <span>/</span>
        <span className="text-text-primary font-medium">Historical Intelligence</span>
      </div>

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-text-primary tracking-tight">Historical Engineering Intelligence</h1>
            <Badge variant="primary" size="sm">Architecture & Evolution</Badge>
          </div>
          <p className="text-sm text-text-muted mt-1 max-w-3xl leading-relaxed">
            Understand how this repository evolved over time. Trace major architectural refactorings, API contract shifts, database schema migrations, engineering decisions (ADRs), and historical bug resolutions.
          </p>
        </div>
        <div className="flex items-center gap-3 flex-shrink-0">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => triggerIndex()}
            disabled={indexing}
            aria-label="Re-index history"
          >
            {indexing ? 'Indexing History…' : 'Sync History & ADRs'}
          </Button>
          <Link to={`/repositories/${repoId}/pull-requests`}>
            <Button variant="ghost" size="sm">Pull Requests</Button>
          </Link>
        </div>
      </div>

      {/* Top Evolution Dimension Metric Cards */}
      {evolutionOverview && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <Card className="p-3 text-center border-l-2 border-l-primary hover:border-primary/50 transition-all">
            <div className="text-[11px] font-semibold text-text-muted uppercase">Architecture</div>
            <div className="text-xl font-bold font-mono text-primary mt-0.5">{evolutionOverview.architecture_changes_count}</div>
            <div className="text-[10px] text-text-muted">Refactorings</div>
          </Card>
          <Card className="p-3 text-center border-l-2 border-l-blue-400 hover:border-blue-400/50 transition-all">
            <div className="text-[11px] font-semibold text-text-muted uppercase">API Contracts</div>
            <div className="text-xl font-bold font-mono text-blue-400 mt-0.5">{evolutionOverview.api_changes_count}</div>
            <div className="text-[10px] text-text-muted">RFC 7807 & Keys</div>
          </Card>
          <Card className="p-3 text-center border-l-2 border-l-amber-400 hover:border-amber-400/50 transition-all">
            <div className="text-[11px] font-semibold text-text-muted uppercase">Database</div>
            <div className="text-xl font-bold font-mono text-amber-400 mt-0.5">{evolutionOverview.database_changes_count}</div>
            <div className="text-[10px] text-text-muted">Cents & Locks</div>
          </Card>
          <Card className="p-3 text-center border-l-2 border-l-purple-400 hover:border-purple-400/50 transition-all">
            <div className="text-[11px] font-semibold text-text-muted uppercase">Dependencies</div>
            <div className="text-xl font-bold font-mono text-purple-400 mt-0.5">{evolutionOverview.dependency_changes_count}</div>
            <div className="text-[10px] text-text-muted">Pydantic & HTTPX</div>
          </Card>
          <Card className="p-3 text-center border-l-2 border-l-rose-500 hover:border-rose-500/50 transition-all">
            <div className="text-[11px] font-semibold text-text-muted uppercase">Security</div>
            <div className="text-xl font-bold font-mono text-rose-500 mt-0.5">{evolutionOverview.security_changes_count}</div>
            <div className="text-[10px] text-text-muted">Tokens & Rate Limits</div>
          </Card>
          <Card className="p-3 text-center border-l-2 border-l-emerald-400 hover:border-emerald-400/50 transition-all">
            <div className="text-[11px] font-semibold text-text-muted uppercase">Performance</div>
            <div className="text-xl font-bold font-mono text-emerald-400 mt-0.5">{evolutionOverview.performance_changes_count}</div>
            <div className="text-[10px] text-text-muted">Indexes & Async</div>
          </Card>
        </div>
      )}

      {/* Main Tabs Navigation */}
      <div className="flex items-center gap-2 border-b border-border pb-1 overflow-x-auto no-scrollbar" role="tablist">
        {[
          { id: 'overview', label: 'Architecture Evolution', icon: 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15' },
          { id: 'modules', label: 'Module History', icon: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10' },
          { id: 'adrs', label: 'Decisions (ADRs)', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
          { id: 'impact', label: 'Historical Impact', icon: 'M13 10V3L4 14h7v7l9-11h-7z' },
          { id: 'bugs', label: 'Bug Lessons', icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z' },
          { id: 'similar_prs', label: 'Similar PR Explorer', icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z' },
          { id: 'hotspots', label: 'Hotspots & Churn', icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' },
        ].map(tab => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
              activeTab === tab.id
                ? 'bg-primary/10 text-primary border border-primary/20 shadow-sm'
                : 'text-text-muted hover:text-text-secondary hover:bg-surfaceHighlight/50'
            }`}
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d={tab.icon} />
            </svg>
            {tab.label}
          </button>
        ))}
      </div>

      {/* =========================================================================
          TAB 1: ARCHITECTURE EVOLUTION TIMELINE
         ========================================================================= */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 className="text-base font-semibold text-text-primary">Chronological Architecture & System Milestones</h3>
              <p className="text-xs text-text-muted">Key engineering changes that shaped the current codebase architecture.</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-text-muted">Dimension:</span>
              <select
                value={milestoneCategory}
                onChange={e => setMilestoneCategory(e.target.value)}
                className="bg-surface border border-border text-text-secondary text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="all">All Dimensions</option>
                <option value="architecture">Architecture</option>
                <option value="api">API Contracts</option>
                <option value="database">Database & Schemas</option>
                <option value="dependency">Dependencies</option>
                <option value="security">Security & Auth</option>
                <option value="performance">Performance & Scalability</option>
              </select>
            </div>
          </div>

          {loadingMilestones ? (
            <div className="p-12 text-center text-text-muted text-sm">Loading evolution milestones…</div>
          ) : milestones.length === 0 ? (
            <EmptyState title="No milestones match filter" description="Select another evolution dimension." className="py-12" />
          ) : (
            <div className="relative border-l-2 border-border/80 pl-6 space-y-6 ml-3">
              {milestones.map((m, idx) => (
                <div key={m.id} className="relative group">
                  {/* Timeline dot */}
                  <div className="absolute -left-[31px] top-1.5 w-3.5 h-3.5 rounded-full bg-surface border-2 border-primary group-hover:scale-125 transition-all" />

                  <Card className="p-5 space-y-4 hover:border-primary/40 transition-all">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border/60 pb-3">
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-sm font-bold text-text-primary">{m.title}</span>
                          {getCategoryBadge(m.category)}
                          <Badge variant="default" size="sm">Module: {m.module_name}</Badge>
                          {m.pr_id && (
                            <span className="font-mono text-xs text-primary font-bold">PR #{m.pr_id}</span>
                          )}
                        </div>
                        <div className="text-xs text-text-muted mt-1">
                          Date: <span className="font-mono text-text-secondary">{m.milestone_date?.slice(0, 10)}</span>
                          {m.commit_sha && (
                            <span> · Commit: <span className="font-mono text-text-muted">{m.commit_sha.slice(0, 8)}</span></span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* What changed & Why */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="bg-surfaceHighlight/40 border border-border/60 rounded-lg p-3 space-y-1">
                        <div className="text-[11px] font-semibold text-text-muted uppercase">Previous Approach:</div>
                        <p className="text-xs text-text-secondary leading-relaxed">{m.previous_approach}</p>
                      </div>
                      <div className="bg-primary/5 border border-primary/20 rounded-lg p-3 space-y-1">
                        <div className="text-[11px] font-semibold text-primary uppercase">Current Implementation:</div>
                        <p className="text-xs text-text-primary leading-relaxed">{m.current_approach}</p>
                      </div>
                    </div>

                    {/* Problem Solved & Consequences */}
                    <div className="space-y-2 text-xs">
                      <div>
                        <strong className="text-text-primary">Problem Solved: </strong>
                        <span className="text-text-secondary">{m.problem_solved}</span>
                      </div>
                      {m.business_context && (
                        <div>
                          <strong className="text-text-primary">Business Context: </strong>
                          <span className="text-text-muted">{m.business_context}</span>
                        </div>
                      )}
                      {m.consequences && (
                        <div>
                          <strong className="text-text-primary">Consequences & Trade-offs: </strong>
                          <span className="text-text-muted">{m.consequences}</span>
                        </div>
                      )}
                      {m.lessons_learned && (
                        <div className="bg-surfaceHighlight/70 border-l-2 border-l-primary/60 p-2 rounded text-text-secondary italic">
                          "{m.lessons_learned}"
                        </div>
                      )}
                    </div>

                    {/* Affected Files */}
                    {m.affected_files && m.affected_files.length > 0 && (
                      <div className="pt-2 border-t border-border/60 flex items-center gap-2 flex-wrap text-[11px]">
                        <span className="text-text-muted font-semibold">Affected Files:</span>
                        {m.affected_files.map((f, i) => (
                          <span key={i} className="font-mono bg-surface border border-border px-1.5 py-0.5 rounded text-text-muted">
                            {f}
                          </span>
                        ))}
                      </div>
                    )}
                  </Card>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* =========================================================================
          TAB 2: MODULE EVOLUTION DEEP DIVE
         ========================================================================= */}
      {activeTab === 'modules' && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 className="text-base font-semibold text-text-primary">Component & Module Evolution Tracking</h3>
              <p className="text-xs text-text-muted">Inspect how a single module transitioned from initial design to current enterprise state.</p>
            </div>
            <div className="flex items-center gap-1.5 bg-surface border border-border rounded-lg p-1">
              {[
                { id: 'orders', label: 'Order Processing' },
                { id: 'auth', label: 'Authentication' },
                { id: 'users', label: 'User Management' },
                { id: 'core', label: 'Core / API Infrastructure' },
              ].map(m => (
                <button
                  key={m.id}
                  onClick={() => setSelectedModule(m.id)}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                    selectedModule === m.id
                      ? 'bg-primary text-white shadow-sm'
                      : 'text-text-muted hover:text-text-primary'
                  }`}
                >
                  {m.label}
                </button>
              ))}
            </div>
          </div>

          {loadingModuleEvolution ? (
            <div className="p-12 text-center text-text-muted text-sm">Loading module lifecycle…</div>
          ) : moduleEvolution ? (
            <div className="space-y-6">
              {/* Architecture Shift Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card className="p-4 space-y-2 border-l-4 border-l-text-muted bg-surface">
                  <div className="text-xs font-semibold text-text-muted uppercase">Original Implementation</div>
                  <p className="text-xs text-text-secondary leading-relaxed">{moduleEvolution.original_architecture}</p>
                </Card>
                <Card className="p-4 space-y-2 border-l-4 border-l-primary bg-primary/5">
                  <div className="text-xs font-semibold text-primary uppercase">Current Implementation</div>
                  <p className="text-xs text-text-primary leading-relaxed">{moduleEvolution.current_architecture}</p>
                </Card>
              </div>

              {/* Critical Cautions & Hotspot Warnings */}
              {moduleEvolution.critical_cautions && moduleEvolution.critical_cautions.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider">Engineering Warnings & Hotspots</h4>
                  <div className="space-y-2">
                    {moduleEvolution.critical_cautions.map((c, i) => (
                      <div key={i} className="p-3 rounded-lg border border-warning/30 bg-warning/10 text-warning text-xs flex items-center gap-2">
                        <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                        <span>{c}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Module Milestones */}
              <div className="space-y-3">
                <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider">
                  Evolution Milestones Touching {moduleEvolution.display_name} ({moduleEvolution.evolution_milestones.length})
                </h4>
                <div className="space-y-3">
                  {moduleEvolution.evolution_milestones.map(m => (
                    <Card key={m.id} className="p-4 space-y-2">
                      <div className="flex items-center justify-between gap-2 flex-wrap">
                        <span className="text-sm font-bold text-text-primary">{m.title}</span>
                        <div className="flex items-center gap-2">
                          {getCategoryBadge(m.category)}
                          <span className="text-xs font-mono text-text-muted">{m.milestone_date?.slice(0, 10)}</span>
                        </div>
                      </div>
                      <p className="text-xs text-text-secondary leading-relaxed">{m.problem_solved}</p>
                      <div className="text-[11px] text-text-muted">
                        <strong>Reason: </strong> {m.reason_for_change}
                      </div>
                    </Card>
                  ))}
                </div>
              </div>

              {/* Governing Decisions */}
              {moduleEvolution.governing_decisions && moduleEvolution.governing_decisions.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider">Governing Architecture Decisions</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {moduleEvolution.governing_decisions.map(a => (
                      <Card key={a.id} className="p-3 bg-surface border border-border">
                        <div className="font-mono text-xs font-bold text-primary">{a.adr_number}: {a.title}</div>
                        <p className="text-xs text-text-secondary mt-1">{a.decision}</p>
                      </Card>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </div>
      )}

      {/* =========================================================================
          TAB 3: ARCHITECTURE DECISION RECORDS (15-ATTRIBUTE FRAMEWORK)
         ========================================================================= */}
      {activeTab === 'adrs' && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 className="text-base font-semibold text-text-primary">Architecture Decision Records (ADRs)</h3>
              <p className="text-xs text-text-muted">Structured 15-attribute engineering decision knowledge repository.</p>
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <select
                value={adrCategory}
                onChange={e => setAdrCategory(e.target.value)}
                className="bg-surface border border-border text-text-secondary text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="all">All Categories</option>
                <option value="architecture">Architecture</option>
                <option value="frontend">Frontend</option>
                <option value="framework">Framework</option>
                <option value="database">Database</option>
                <option value="ai_llm">AI / LLM</option>
                <option value="security">Security</option>
                <option value="performance">Performance</option>
                <option value="concurrency">Concurrency</option>
                <option value="api_contract">API Contract</option>
              </select>
              <select
                value={adrType}
                onChange={e => setAdrType(e.target.value)}
                className="bg-surface border border-border text-text-secondary text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="all">All Types</option>
                <option value="documented">Documented</option>
                <option value="synthetic_demo">Synthetic Demo</option>
              </select>
            </div>
          </div>

          {loadingAdrs ? (
            <div className="p-12 text-center text-text-muted text-sm">Indexing Architecture Decision Records…</div>
          ) : filteredAdrs.length === 0 ? (
            <EmptyState title="No decisions match filter" description="Adjust category or decision type filter." className="py-12" />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredAdrs.map(adr => (
                <Card key={adr.id} className="p-5 space-y-4 hover:border-primary/40 transition-all flex flex-col justify-between">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-primary">{adr.adr_number}</span>
                        <Badge variant="primary" size="sm">{adr.decision_category || 'architecture'}</Badge>
                        <Badge variant="default" size="sm">{adr.decision_type}</Badge>
                      </div>
                      <Badge variant={adr.status === 'Confirmed' ? 'success' : 'default'} size="sm">
                        {adr.status}
                      </Badge>
                    </div>

                    <h4 className="text-base font-bold text-text-primary">{adr.title}</h4>

                    {adr.original_problem && (
                      <div className="text-xs text-text-secondary">
                        <strong className="text-text-primary">Problem: </strong>
                        <span>{adr.original_problem}</span>
                      </div>
                    )}

                    <div className="text-xs text-text-secondary leading-relaxed bg-surfaceHighlight/50 border border-border rounded-lg p-3">
                      <strong className="text-primary">Decision: </strong>
                      <span>{adr.decision}</span>
                    </div>

                    {adr.options_considered && adr.options_considered.length > 0 && (
                      <div className="text-xs text-text-muted">
                        <strong>Alternatives Considered: </strong>
                        <span>{adr.options_considered.join(', ')}</span>
                      </div>
                    )}

                    {adr.advantages && adr.advantages.length > 0 && (
                      <div className="text-xs space-y-1 bg-success/5 border border-success/20 rounded p-2 text-text-secondary">
                        <strong className="text-success">Advantages:</strong>
                        <ul className="list-disc list-inside space-y-0.5 text-[11px]">
                          {adr.advantages.map((adv, i) => (
                            <li key={i}>{adv}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {adr.trade_offs && adr.trade_offs.length > 0 && (
                      <div className="text-xs space-y-1 bg-warning/5 border border-warning/20 rounded p-2 text-text-secondary">
                        <strong className="text-warning">Trade-offs & Constraints:</strong>
                        <ul className="list-disc list-inside space-y-0.5 text-[11px]">
                          {adr.trade_offs.map((to, i) => (
                            <li key={i}>{to}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {adr.consequences && (
                      <p className="text-xs text-text-muted">
                        <strong>Consequences: </strong> {adr.consequences}
                      </p>
                    )}
                  </div>

                  <div className="pt-3 border-t border-border flex items-center justify-between text-[11px] text-text-muted">
                    <span className="font-mono truncate max-w-[200px]">{adr.file_source || 'docs/architecture'}</span>
                    {adr.related_prs && adr.related_prs.length > 0 && (
                      <span className="text-primary font-mono font-medium">PRs: {adr.related_prs.join(', ')}</span>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* =========================================================================
          TAB 4: HISTORICAL IMPACT ANALYZER
         ========================================================================= */}
      {activeTab === 'impact' && (
        <div className="space-y-6">
          <div className="bg-surface border border-border rounded-xl p-5 space-y-4">
            <div>
              <h3 className="text-base font-semibold text-text-primary">Historical Impact Analyzer</h3>
              <p className="text-xs text-text-muted mt-0.5">
                Predict architectural ripple effects, verify connected APIs, and retrieve past bug lessons before modifying code.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-3">
              <input
                type="text"
                placeholder="Enter file path (e.g. app/services/order_service.py) or module (orders, auth, users)..."
                value={impactTarget}
                onChange={e => setImpactTarget(e.target.value)}
                className="flex-1 bg-surfaceHighlight/50 border border-border rounded-lg px-4 py-2 text-sm text-text-primary font-mono focus:outline-none focus:ring-1 focus:ring-primary"
              />
              <Button
                variant="primary"
                onClick={() => runImpactAnalysis(impactTarget)}
                disabled={!impactTarget.trim() || analyzingImpact}
              >
                {analyzingImpact ? 'Analyzing Impact…' : 'Run Impact Analysis'}
              </Button>
            </div>

            <div className="flex items-center gap-2 text-xs text-text-muted">
              <span>Quick inspect:</span>
              {['app/services/order_service.py', 'app/dependencies.py', 'app/services/user_service.py'].map(f => (
                <button
                  key={f}
                  onClick={() => {
                    setImpactTarget(f);
                    runImpactAnalysis(f);
                  }}
                  className="font-mono underline hover:text-text-primary text-[11px]"
                >
                  {f.split('/').pop()}
                </button>
              ))}
            </div>
          </div>

          {analyzingImpact ? (
            <div className="p-12 text-center text-text-muted text-sm">Synthesizing historical dependencies and bug lessons…</div>
          ) : impactResult ? (
            <div className="space-y-6 animate-fade-in">
              {/* Hotspot & Status Banner */}
              <div className={`p-4 rounded-xl border ${
                impactResult.is_hotspot
                  ? 'bg-warning/10 border-warning/30 text-warning'
                  : 'bg-primary/10 border-primary/20 text-text-primary'
              }`}>
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <span className="font-bold text-sm">
                      {impactResult.is_hotspot ? '⚠️ High-Risk Recurring Hotspot' : 'Verified Stable Component'}
                    </span>
                    <p className="text-xs mt-1">
                      Target Module: <span className="font-mono font-bold uppercase">{impactResult.target_module}</span> · Hotspot Score: <span className="font-mono">{impactResult.hotspot_score}</span>
                    </p>
                  </div>
                  {impactResult.is_hotspot && (
                    <Badge variant="warning">Exercise Strict Caution</Badge>
                  )}
                </div>
              </div>

              {/* Verified vs Inferred Impact Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card className="p-4 space-y-3 border-l-4 border-l-success">
                  <div className="text-xs font-semibold text-success uppercase">Verified Direct Dependencies</div>
                  <ul className="space-y-1.5 text-xs text-text-secondary">
                    {impactResult.verified_dependencies.map((d, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-success font-bold">•</span>
                        <span>{d}</span>
                      </li>
                    ))}
                  </ul>
                </Card>

                <Card className="p-4 space-y-3 border-l-4 border-l-amber-400">
                  <div className="text-xs font-semibold text-amber-400 uppercase">Inferred Potential Architectural Impacts</div>
                  <ul className="space-y-1.5 text-xs text-text-secondary">
                    {impactResult.inferred_potential_impacts.map((d, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-amber-400 font-bold">•</span>
                        <span>{d}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              </div>

              {/* Connected APIs & DB Dependencies */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card className="p-4 space-y-2">
                  <div className="text-xs font-semibold text-text-muted uppercase">Connected API Endpoints:</div>
                  <div className="flex flex-wrap gap-2">
                    {impactResult.connected_apis.map((api, i) => (
                      <span key={i} className="font-mono text-xs bg-surfaceHighlight border border-border px-2 py-1 rounded text-primary">
                        {api}
                      </span>
                    ))}
                  </div>
                </Card>

                <Card className="p-4 space-y-2">
                  <div className="text-xs font-semibold text-text-muted uppercase">Database Dependencies:</div>
                  <div className="flex flex-wrap gap-2">
                    {impactResult.database_dependencies.map((dbDep, i) => (
                      <span key={i} className="font-mono text-xs bg-surfaceHighlight border border-border px-2 py-1 rounded text-amber-400">
                        {dbDep}
                      </span>
                    ))}
                  </div>
                </Card>
              </div>

              {/* Historical Bug Warnings */}
              {impactResult.historical_bugs_and_warnings && impactResult.historical_bugs_and_warnings.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider">
                    Past Bug Incidents on this Module ({impactResult.historical_bugs_and_warnings.length})
                  </h4>
                  <div className="space-y-3">
                    {impactResult.historical_bugs_and_warnings.map(b => (
                      <Card key={b.id} className="p-4 space-y-2 border-l-4 border-l-critical">
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-sm font-bold text-text-primary">{b.issue_title}</span>
                          <Badge variant="critical" size="sm">{b.issue_category}</Badge>
                        </div>
                        <p className="text-xs text-text-secondary"><strong>Root Cause:</strong> {b.root_cause}</p>
                        <p className="text-xs text-success"><strong>Prevention:</strong> {b.prevention_recommendations}</p>
                      </Card>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommended Regression Tests */}
              <Card className="p-4 space-y-2 bg-surface">
                <div className="text-xs font-semibold text-text-muted uppercase">Mandatory Regression Verification:</div>
                <div className="space-y-1">
                  {impactResult.relevant_regression_tests.map((t, i) => (
                    <div key={i} className="font-mono text-xs bg-surfaceHighlight/60 p-2 rounded text-text-secondary">
                      pytest {t}
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          ) : null}
        </div>
      )}

      {/* =========================================================================
          TAB 5: HISTORICAL BUG & LESSON INTELLIGENCE
         ========================================================================= */}
      {activeTab === 'bugs' && (
        <div className="space-y-6">
          <div>
            <h3 className="text-base font-semibold text-text-primary">Historical Bug & Lesson Knowledge Base</h3>
            <p className="text-xs text-text-muted">
              Documented software defects, root causes, resolutions, and preventive rules to avoid recurring mistakes.
            </p>
          </div>

          {loadingBugLessons ? (
            <div className="p-12 text-center text-text-muted text-sm">Loading historical bug lessons…</div>
          ) : bugLessons.length === 0 ? (
            <EmptyState title="No bug lessons documented" description="Sync history or run reviews." className="py-12" />
          ) : (
            <div className="space-y-4">
              {bugLessons.map(b => (
                <Card key={b.id} className="p-5 space-y-3 border-l-4 border-l-critical hover:border-critical/60 transition-all">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-base font-bold text-text-primary">{b.issue_title}</span>
                      <Badge variant="critical" size="sm">{b.issue_category}</Badge>
                      <Badge variant="default" size="sm">Module: {b.module_name}</Badge>
                      {b.related_pr_number && (
                        <span className="font-mono text-xs text-primary font-bold">Resolved in PR #{b.related_pr_number}</span>
                      )}
                    </div>
                    <span className="text-xs text-text-muted font-mono">{b.occurred_at?.slice(0, 10)}</span>
                  </div>

                  <p className="text-xs text-text-secondary leading-relaxed">{b.description}</p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    <div className="bg-critical/5 border border-critical/20 rounded-lg p-3">
                      <strong className="text-critical uppercase text-[11px]">Root Cause:</strong>
                      <p className="text-text-secondary mt-1">{b.root_cause}</p>
                    </div>
                    <div className="bg-success/5 border border-success/20 rounded-lg p-3">
                      <strong className="text-success uppercase text-[11px]">Resolution Details:</strong>
                      <p className="text-text-secondary mt-1">{b.resolution_details}</p>
                    </div>
                  </div>

                  <div className="bg-primary/5 border border-primary/20 rounded-lg p-3 text-xs">
                    <strong className="text-primary uppercase text-[11px]">Preventative Rule for Future PRs:</strong>
                    <p className="text-text-primary mt-1">{b.prevention_recommendations}</p>
                  </div>

                  {b.tests_added && b.tests_added.length > 0 && (
                    <div className="text-[11px] text-text-muted flex items-center gap-2 flex-wrap">
                      <strong>Regression Tests:</strong>
                      {b.tests_added.map((t, i) => (
                        <span key={i} className="font-mono bg-surface border border-border px-1.5 py-0.5 rounded text-text-secondary">
                          {t}
                        </span>
                      ))}
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* =========================================================================
          TAB 6: INTELLIGENT SIMILAR PR EXPLORER
         ========================================================================= */}
      {activeTab === 'similar_prs' && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row items-center gap-3">
            <div className="relative flex-1 w-full">
              <input
                type="text"
                placeholder="Search historical PRs by title, change category, or touched files…"
                value={similarPrQuery}
                onChange={e => setSimilarPrQuery(e.target.value)}
                className="w-full bg-surface border border-border rounded-lg px-4 py-2 pl-9 text-sm text-text-primary focus:outline-none focus:ring-1 focus:ring-primary font-mono placeholder-text-muted"
              />
              <svg className="w-4 h-4 text-text-muted absolute left-3 top-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <Button variant="primary" onClick={() => runSimilarPrSearch()}>Search PR Knowledge</Button>
          </div>

          {loadingSimilarPrs ? (
            <div className="p-12 text-center text-text-muted text-sm">Searching historical pull requests…</div>
          ) : similarPrs.length === 0 ? (
            <EmptyState title="No matching PRs found" description="Try another search keyword." className="py-12" />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {similarPrs.map(pr => (
                <Card key={pr.pr_id} className="p-5 space-y-3 hover:border-primary/40 transition-all flex flex-col justify-between">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-mono text-xs font-bold text-primary">PR #{pr.github_number}</span>
                      <Badge variant="primary" size="sm">{pr.change_category}</Badge>
                      <Badge variant="success" size="sm">{pr.outcome}</Badge>
                    </div>

                    <h4 className="text-sm font-bold text-text-primary">{pr.title}</h4>

                    <div className="text-xs text-text-secondary bg-surfaceHighlight/50 border border-border rounded-lg p-2.5">
                      <strong className="text-primary">Relevance Reason: </strong>
                      <span>{pr.relevance_reason}</span>
                    </div>

                    <div className="text-xs text-text-muted">
                      <strong>What Changed: </strong> {pr.what_changed}
                    </div>

                    <div className="text-xs bg-primary/5 border border-primary/20 rounded p-2 text-text-secondary">
                      <strong className="text-primary">Key Lesson: </strong>
                      <span>{pr.lessons_relevant_to_current_work}</span>
                    </div>
                  </div>

                  {pr.evidence_snippets && pr.evidence_snippets.length > 0 && (
                    <div className="pt-2 border-t border-border space-y-1 text-[11px] font-mono text-text-muted">
                      {pr.evidence_snippets.map((ev, i) => (
                        <div key={i} className="truncate">• {ev}</div>
                      ))}
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* =========================================================================
          TAB 7: RECURRING HOTSPOTS & CHURN
         ========================================================================= */}
      {activeTab === 'hotspots' && (
        <div className="space-y-6">
          <div>
            <h3 className="text-base font-semibold text-text-primary">Recurring Bug Hotspots & Code Churn</h3>
            <p className="text-xs text-text-muted">Files with high bugfix churn or recurring review findings.</p>
          </div>

          {loadingHotspots ? (
            <div className="p-12 text-center text-text-muted text-sm">Computing recurring issue hotspots…</div>
          ) : hotspots.length === 0 ? (
            <EmptyState title="No hotspots detected" description="No files exceed recurrence threshold." className="py-12" />
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {hotspots.map(h => (
                <Card key={h.id} className="p-5 space-y-3 border-l-4 border-l-primary hover:border-primary/40 transition-all">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono text-sm font-bold text-text-primary">{h.file_path}</span>
                        <Badge variant={h.severity === 'critical' ? 'critical' : h.severity === 'high' ? 'warning' : 'default'}>
                          {h.severity}
                        </Badge>
                      </div>
                      <p className="text-xs text-text-muted mt-1">
                        Total Commits: <span className="font-mono text-text-secondary">{h.total_commits}</span> · Bugfix Commits: <span className="font-mono text-critical font-medium">{h.bugfix_commits_count}</span> · Review Findings: <span className="font-mono text-warning font-medium">{h.recurring_findings_count}</span>
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <div className="text-xs text-text-muted uppercase">Hotspot Score</div>
                        <div className="text-lg font-bold font-mono text-primary">{h.hotspot_score}</div>
                      </div>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => {
                          setHotspotCompareFile(h.file_path);
                          runCompare();
                        }}
                      >
                        Inspect Changes
                      </Button>
                    </div>
                  </div>

                  {h.historical_references && h.historical_references.length > 0 && (
                    <div className="bg-surfaceHighlight/50 border border-border rounded-lg p-3 space-y-1 text-xs">
                      <div className="text-[11px] font-semibold text-text-muted uppercase">Past Patches:</div>
                      {h.historical_references.map((r, i) => (
                        <div key={i} className="text-text-secondary flex items-start gap-2">
                          <span className="font-mono text-primary font-bold">• {r.ref}:</span>
                          <span className="text-text-muted">{r.reason}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )}

          {/* Comparison Result if Selected */}
          {comparison && (
            <Card className="p-5 space-y-4 border-primary/40 animate-fade-in mt-6">
              <h4 className="text-sm font-bold text-text-primary">
                Historical Change Timeline for `{hotspotCompareFile}` ({comparison.total_historical_changes} changes)
              </h4>
              <div className="space-y-3">
                {comparison.historical_changes.map((item, idx) => (
                  <div key={idx} className="p-3 rounded-lg bg-surfaceHighlight/50 border border-border space-y-1 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-bold text-primary">{item.reference}</span>
                      <span className="font-mono text-text-muted">{item.date}</span>
                    </div>
                    <p className="text-text-primary"><strong>Decision: </strong>{item.original_decision}</p>
                    {item.risk_warning && (
                      <p className="text-critical bg-critical/10 p-1.5 rounded">{item.risk_warning}</p>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
