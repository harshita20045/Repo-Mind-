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

  const [activeTab, setActiveTab] = useState('prs'); // prs | hotspots | adrs | compare
  const [prSearch, setPrSearch] = useState('');
  const [prState, setPrState] = useState('all');
  const [compareFilePath, setCompareFilePath] = useState('');
  const [compareInput, setCompareInput] = useState('');

  // 1. Fetch repository metadata
  const { data: repo, isLoading: loadingRepo } = useQuery({
    queryKey: ['repository', repoId],
    queryFn: () => orgApi.getRepository(repoId),
    enabled: !!repoId,
  });

  // 2. Fetch Historical PRs
  const { data: historicalPrs = [], isLoading: loadingPrs } = useQuery({
    queryKey: ['historicalPrs', repoId, prSearch, prState],
    queryFn: () => historyApi.getHistoricalPrs(repoId, { q: prSearch || undefined, state: prState }),
    enabled: !!repoId && activeTab === 'prs',
  });

  // 3. Fetch Historical Commits
  const { data: historicalCommits = [], isLoading: loadingCommits } = useQuery({
    queryKey: ['historicalCommits', repoId, prSearch],
    queryFn: () => historyApi.getPreviousChanges(repoId, { q: prSearch || undefined, limit: 15 }),
    enabled: !!repoId && activeTab === 'prs',
  });

  // 4. Fetch Recurring Hotspots
  const { data: hotspots = [], isLoading: loadingHotspots } = useQuery({
    queryKey: ['recurringHotspots', repoId],
    queryFn: () => historyApi.getRecurringIssues(repoId),
    enabled: !!repoId && activeTab === 'hotspots',
  });

  // 5. Fetch ADRs
  const { data: adrs = [], isLoading: loadingAdrs } = useQuery({
    queryKey: ['adrs', repoId],
    queryFn: () => historyApi.getAdrs(repoId),
    enabled: !!repoId && activeTab === 'adrs',
  });

  // 6. Change Comparison Query
  const { data: comparison, isLoading: loadingComparison, refetch: runCompare } = useQuery({
    queryKey: ['changeComparison', repoId, compareFilePath],
    queryFn: () => historyApi.compareChanges(repoId, { file_path: compareFilePath }),
    enabled: !!repoId && !!compareFilePath && activeTab === 'compare',
  });

  // 7. Trigger Index Mutation
  const { mutate: triggerIndex, isPending: indexing } = useMutation({
    mutationFn: () => historyApi.triggerIndex(repoId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['historicalPrs', repoId] });
      queryClient.invalidateQueries({ queryKey: ['historicalCommits', repoId] });
      queryClient.invalidateQueries({ queryKey: ['recurringHotspots', repoId] });
      queryClient.invalidateQueries({ queryKey: ['adrs', repoId] });
    },
  });

  const handleRunComparison = (e) => {
    e.preventDefault();
    if (!compareInput.trim()) return;
    setCompareFilePath(compareInput.trim());
  };

  if (loadingRepo) {
    return <PageLoader message="Loading historical code intelligence…" />;
  }

  const getSeverityBadge = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical': return <Badge variant="critical">Critical Hotspot</Badge>;
      case 'high': return <Badge variant="warning">High Churn</Badge>;
      case 'medium': return <Badge variant="primary">Medium Churn</Badge>;
      default: return <Badge variant="default">Low Churn</Badge>;
    }
  };

  return (
    <div className="flex flex-col gap-6 animate-slide-up max-w-7xl mx-auto pb-12">
      {/* Repository Unified Sub-Navigation */}
      <RepositoryNav repositoryId={repoId} currentTab="history" />

      {/* Breadcrumb & Navigation */}
      <div className="flex items-center gap-2 text-xs text-text-muted">
        <Link to="/repositories" className="hover:text-text-primary transition-colors">Repositories</Link>
        <span>/</span>
        <span className="text-text-secondary">{repo?.github_owner}/{repo?.github_name}</span>
        <span>/</span>
        <span className="text-text-primary font-medium">Historical Intelligence</span>
      </div>

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/[0.08]">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-text-primary tracking-tight">Historical Code Intelligence</h1>
            <Badge variant="primary" size="sm">History & Decisions</Badge>
          </div>
          <p className="text-sm text-text-muted mt-1 max-w-2xl leading-relaxed">
            Surface previous engineering decisions, analyze recurring bug hotspots, and inspect Architecture Decision Records (ADRs) to prevent regressions.
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
            <Button variant="ghost" size="sm">Back to PRs</Button>
          </Link>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-white/[0.08] pb-1 overflow-x-auto no-scrollbar" role="tablist">
        {[
          { id: 'prs', label: 'PR & Change Search', icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' },
          { id: 'hotspots', label: 'Recurring Issues & Hotspots', icon: 'M13 10V3L4 14h7v7l9-11h-7z' },
          { id: 'adrs', label: 'Architecture Decisions (ADRs)', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
          { id: 'compare', label: 'Change Evolution & Decisions', icon: 'M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4' },
        ].map(tab => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
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

      {/* TAB 1: PR & CHANGE SEARCH */}
      {activeTab === 'prs' && (
        <div className="space-y-6">
          {/* Search bar & filters */}
          <div className="flex flex-col sm:flex-row items-center gap-3">
            <div className="relative flex-1 w-full">
              <input
                type="text"
                placeholder="Search historical PRs, commit messages, or files…"
                value={prSearch}
                onChange={e => setPrSearch(e.target.value)}
                className="w-full bg-surface border border-white/[0.08] rounded-lg px-4 py-2 pl-9 text-sm text-text-primary focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary placeholder-text-muted"
              />
              <svg className="w-4 h-4 text-text-muted absolute left-3 top-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <select
              value={prState}
              onChange={e => setPrState(e.target.value)}
              className="bg-surface border border-white/[0.08] text-text-secondary text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <option value="all">All States</option>
              <option value="merged">Merged</option>
              <option value="closed">Closed</option>
              <option value="open">Open</option>
            </select>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* PRs Column */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-text-primary uppercase tracking-wider flex items-center gap-2">
                <span>Pull Request History</span>
                <span className="text-xs font-mono text-text-muted">({historicalPrs.length})</span>
              </h3>

              {loadingPrs ? (
                <div className="p-8 text-center text-text-muted text-sm">Loading historical PRs…</div>
              ) : historicalPrs.length === 0 ? (
                <EmptyState
                  title="No historical PRs found"
                  description="No pull requests match your search filter."
                  className="py-8"
                />
              ) : (
                <div className="space-y-3">
                  {historicalPrs.map(pr => (
                    <Card key={pr.id} className="p-4 hover:border-white/15 transition-all">
                      <div className="flex items-start justify-between gap-3">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-mono text-xs text-primary font-bold">#{pr.github_number}</span>
                            <span className="text-sm font-semibold text-text-primary">{pr.title}</span>
                            <Badge variant={pr.state === 'merged' ? 'success' : pr.state === 'open' ? 'primary' : 'default'} size="sm">
                              {pr.state}
                            </Badge>
                          </div>
                          <p className="text-xs text-text-muted">
                            Author: <span className="text-text-secondary font-mono">{pr.github_author_login || pr.author || 'developer'}</span> · Branch: <span className="font-mono">{pr.source_branch || pr.default_branch || 'main'}</span>
                          </p>
                          {pr.summary && (
                            <p className="text-xs text-text-secondary line-clamp-2 mt-1">{pr.summary}</p>
                          )}
                        </div>
                        <div className="text-right text-xs text-text-muted font-mono flex-shrink-0">
                          <span className="text-success font-medium">+{pr.additions}</span> / <span className="text-error font-medium">-{pr.deletions}</span>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </div>

            {/* Commits Column */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-text-primary uppercase tracking-wider flex items-center gap-2">
                <span>Commit Modifications & Bugfixes</span>
                <span className="text-xs font-mono text-text-muted">({historicalCommits.length})</span>
              </h3>

              {loadingCommits ? (
                <div className="p-8 text-center text-text-muted text-sm">Loading commits…</div>
              ) : historicalCommits.length === 0 ? (
                <EmptyState
                  title="No commit records found"
                  description="Sync history or adjust search filters to view commit history."
                  className="py-8"
                />
              ) : (
                <div className="space-y-3">
                  {historicalCommits.map(c => (
                    <Card key={c.id} className="p-4 hover:border-white/15 transition-all">
                      <div className="flex items-start justify-between gap-2">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-mono text-xs bg-white/5 border border-white/10 px-1.5 py-0.5 rounded text-text-muted">
                              {c.commit_sha ? c.commit_sha.slice(0, 8) : '—'}
                            </span>
                            {c.is_bugfix && (
                              <Badge variant="critical" size="sm">Bugfix</Badge>
                            )}
                            <span className="text-xs text-text-muted font-mono">{c.committed_at?.slice(0, 10)}</span>
                          </div>
                          <p className="text-sm font-medium text-text-primary">{(c.commit_message || c.message || '').split('\n')[0]}</p>
                          {(c.original_decision_rationale || c.original_decision) && (
                            <p className="text-xs text-text-muted italic border-l-2 border-primary/30 pl-2 mt-1">
                              "{c.original_decision_rationale || c.original_decision}"
                            </p>
                          )}
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: RECURRING ISSUES & HOTSPOTS */}
      {activeTab === 'hotspots' && (
        <div className="space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-text-primary uppercase tracking-wider">
              Recurring Bug Hotspots & Problem Areas
            </h3>
            <p className="text-xs text-text-muted mt-0.5">
              Files with high bugfix churn or recurring review findings. Exercise extra caution and regression testing when modifying these components.
            </p>
          </div>

          {loadingHotspots ? (
            <div className="p-12 text-center text-text-muted text-sm">Computing recurring issue hotspots…</div>
          ) : hotspots.length === 0 ? (
            <EmptyState
              title="No recurring hotspots detected"
              description="No files currently exceed the recurring bug or finding thresholds."
              className="py-12"
            />
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {hotspots.map(h => (
                <Card key={h.id} className="p-5 space-y-3 border-l-4 border-l-primary hover:border-white/20 transition-all">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono text-sm font-bold text-text-primary">{h.file_path}</span>
                        {getSeverityBadge(h.severity)}
                      </div>
                      <p className="text-xs text-text-muted mt-1">
                        Total Commits: <span className="font-mono text-text-secondary">{h.total_commits}</span> · Bugfix Commits: <span className="font-mono text-error font-medium">{h.bugfix_commits_count}</span> · Review Findings: <span className="font-mono text-warning font-medium">{h.recurring_findings_count}</span>
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
                          setCompareFilePath(h.file_path);
                          setCompareInput(h.file_path);
                          setActiveTab('compare');
                        }}
                      >
                        Inspect History
                      </Button>
                    </div>
                  </div>

                  {/* References & Reasons */}
                  {h.historical_references && h.historical_references.length > 0 && (
                    <div className="bg-surfaceHighlight/40 border border-white/[0.06] rounded-lg p-3 space-y-1.5">
                      <div className="text-[11px] font-semibold text-text-muted uppercase">Past Patches & Findings:</div>
                      {h.historical_references.map((ref, idx) => (
                        <div key={idx} className="text-xs text-text-secondary flex items-start gap-2">
                          <span className="font-mono text-primary flex-shrink-0">• {ref.ref}:</span>
                          <span className="text-text-muted">{ref.reason}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: ARCHITECTURE DECISION RECORDS (ADRs) */}
      {activeTab === 'adrs' && (
        <div className="space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-text-primary uppercase tracking-wider">
              Architecture Decision Records (ADRs)
            </h3>
            <p className="text-xs text-text-muted mt-0.5">
              Historical architectural decisions, patterns, and framework choices indexed from repository documentation.
            </p>
          </div>

          {loadingAdrs ? (
            <div className="p-12 text-center text-text-muted text-sm">Indexing Architecture Decision Records…</div>
          ) : adrs.length === 0 ? (
            <EmptyState
              title="No ADRs found"
              description="Click 'Sync History & ADRs' above to index architecture records from docs/02-architecture/."
              className="py-12"
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {adrs.map(adr => (
                <Card key={adr.id} className="p-5 space-y-3 hover:border-white/20 transition-all flex flex-col justify-between">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-mono text-xs font-bold text-primary">{adr.adr_number}</span>
                      <Badge variant={adr.status === 'Confirmed' ? 'success' : 'default'} size="sm">
                        {adr.status}
                      </Badge>
                    </div>
                    <h4 className="text-base font-semibold text-text-primary">{adr.title}</h4>
                    <p className="text-xs text-text-secondary leading-relaxed bg-surfaceHighlight/40 border border-white/[0.06] rounded-lg p-3">
                      <strong>Decision:</strong> {adr.decision}
                    </p>
                    {adr.reason && (
                      <p className="text-xs text-text-muted">
                        <strong>Reason:</strong> {adr.reason}
                      </p>
                    )}
                    {adr.consequences && (
                      <p className="text-xs text-text-muted">
                        <strong>Consequences:</strong> {adr.consequences}
                      </p>
                    )}
                  </div>
                  <div className="pt-2 border-t border-white/[0.06] flex items-center justify-between text-[11px] text-text-muted">
                    <span className="font-mono truncate max-w-[200px]">{adr.file_source || 'docs/architecture'}</span>
                    {adr.affected_modules && adr.affected_modules.length > 0 && (
                      <span className="text-text-secondary">{adr.affected_modules.length} modules governed</span>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 4: CHANGE EVOLUTION & DECISION COMPARISON */}
      {activeTab === 'compare' && (
        <div className="space-y-6">
          <form onSubmit={handleRunComparison} className="flex gap-2">
            <input
              type="text"
              placeholder="Enter file path to inspect (e.g. backend/app/auth/service.py)…"
              value={compareInput}
              onChange={e => setCompareInput(e.target.value)}
              className="flex-1 bg-surface border border-white/[0.08] rounded-lg px-4 py-2 text-sm text-text-primary focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary placeholder-text-muted font-mono"
            />
            <Button type="submit" variant="primary" disabled={!compareInput.trim() || loadingComparison}>
              {loadingComparison ? 'Analyzing…' : 'Inspect File History'}
            </Button>
          </form>

          {loadingComparison ? (
            <div className="p-12 text-center text-text-muted text-sm">Comparing changes with repository history…</div>
          ) : !compareFilePath ? (
            <EmptyState
              title="Select a file to inspect"
              description="Enter a file path above or click 'Inspect History' on any recurring hotspot to examine previous decisions."
              className="py-12"
            />
          ) : comparison ? (
            <div className="space-y-6">
              {/* Guidance Banner */}
              <div className={`p-4 rounded-xl border ${
                comparison.is_hotspot
                  ? 'bg-warning/10 border-warning/30 text-warning'
                  : 'bg-primary/10 border-primary/20 text-text-primary'
              }`}>
                <div className="font-semibold text-sm mb-1">Historical Guidance & Constraints:</div>
                <p className="text-xs leading-relaxed">{comparison.summary_guidance}</p>
              </div>

              {/* Governing ADRs */}
              {comparison.governing_adrs && comparison.governing_adrs.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider">
                    Governing Architecture Decisions:
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {comparison.governing_adrs.map(adr => (
                      <Card key={adr.id} className="p-3 bg-surface border border-white/[0.08]">
                        <div className="font-mono text-xs font-bold text-primary">{adr.adr_number}: {adr.title}</div>
                        <p className="text-xs text-text-secondary mt-1">{adr.decision}</p>
                      </Card>
                    ))}
                  </div>
                </div>
              )}

              {/* Historical Changes Timeline */}
              <div className="space-y-3">
                <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider">
                  Timeline of Previous Changes ({comparison.historical_changes.length}):
                </h4>
                {comparison.historical_changes.length === 0 ? (
                  <p className="text-xs text-text-muted">No prior commit records found for this specific file.</p>
                ) : (
                  <div className="space-y-3">
                    {comparison.historical_changes.map((item, idx) => (
                      <Card key={idx} className="p-4 space-y-2">
                        <div className="flex items-center justify-between gap-2 flex-wrap">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs text-primary font-bold">{item.reference}</span>
                            <span className="text-xs text-text-muted">by {item.author || 'developer'}</span>
                            {item.is_bugfix && <Badge variant="critical" size="sm">Bugfix</Badge>}
                          </div>
                          <span className="font-mono text-xs text-text-muted">{item.date}</span>
                        </div>
                        <div>
                          <div className="text-xs font-semibold text-text-secondary">Original Decision:</div>
                          <p className="text-xs text-text-primary mt-0.5">{item.original_decision}</p>
                        </div>
                        {item.supporting_evidence && (
                          <div className="bg-surfaceHighlight/50 rounded p-2 text-xs font-mono text-text-muted whitespace-pre-wrap">
                            {item.supporting_evidence}
                          </div>
                        )}
                        {item.risk_warning && (
                          <div className="text-xs text-error bg-error/10 border border-error/20 rounded p-2 font-medium">
                            {item.risk_warning}
                          </div>
                        )}
                      </Card>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
