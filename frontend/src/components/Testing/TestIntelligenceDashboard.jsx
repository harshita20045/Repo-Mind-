import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { testingApi } from '../../lib/api';
import TestScenarioCard from './TestScenarioCard';
import EngineeringGraphEngine from '../Graph/EngineeringGraphEngine';

const CATEGORIES = [
  { id: 'all', label: 'All Categories' },
  { id: 'positive', label: 'Positive' },
  { id: 'negative', label: 'Negative' },
  { id: 'boundary', label: 'Boundary' },
  { id: 'validation', label: 'Validation' },
  { id: 'authentication', label: 'Authentication' },
  { id: 'authorization', label: 'Authorization' },
  { id: 'integration', label: 'Integration' },
  { id: 'regression', label: 'Regression' },
];

export default function TestIntelligenceDashboard({ repositoryId, pullRequestId }) {
  const queryClient = useQueryClient();
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [coverageGapOnly, setCoverageGapOnly] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('scenarios'); // scenarios | existing | regression
  const [generatingScenarioId, setGeneratingScenarioId] = useState(null);
  const [executingTestId, setExecutingTestId] = useState(null);

  // 1. Fetch dashboard data
  const {
    data: dashboardData,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['testIntelligenceDashboard', pullRequestId],
    queryFn: () => testingApi.getTestDashboard(pullRequestId),
    enabled: !!pullRequestId,
  });

  // 2. Generate test code mutation
  const { mutate: generateCode } = useMutation({
    mutationFn: (scenarioId) => testingApi.generateTestCase(scenarioId),
    onMutate: (scenarioId) => setGeneratingScenarioId(scenarioId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['testIntelligenceDashboard', pullRequestId] });
      setGeneratingScenarioId(null);
    },
    onError: (err) => {
      alert(`Test code generation failed: ${err.message}`);
      setGeneratingScenarioId(null);
    },
  });

  // 3. Execute test mutation
  const { mutate: executeTest } = useMutation({
    mutationFn: (testId) => testingApi.executeGeneratedTest(testId),
    onMutate: (testId) => setExecutingTestId(testId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['testIntelligenceDashboard', pullRequestId] });
      setExecutingTestId(null);
    },
    onError: (err) => {
      alert(`Test sandbox execution failed: ${err.message}`);
      setExecutingTestId(null);
    },
  });

  // 4. Trigger re-analysis mutation
  const { mutate: triggerAnalysis, isPending: isAnalyzing } = useMutation({
    mutationFn: () => testingApi.triggerTestAnalysis(repositoryId, { pull_request_id: pullRequestId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['testIntelligenceDashboard', pullRequestId] });
    },
    onError: (err) => alert(`Analysis failed: ${err.message}`),
  });

  const scenarios = dashboardData?.scenarios || [];
  const existingTests = dashboardData?.existing_tests || [];
  const regressionFiles = dashboardData?.regression_test_files || [];

  const { testGraphNodes, testGraphEdges } = useMemo(() => {
    const nodeMap = new Map();
    const edgeList = [];

    scenarios.forEach((sc, idx) => {
      const targetKey = sc.target_symbol || sc.target_file || `target_${idx}`;
      const targetId = `sym_${targetKey.replace(/[^a-zA-Z0-9_-]/g, '_')}`;

      if (!nodeMap.has(targetId)) {
        nodeMap.set(targetId, {
          id: targetId,
          node_key: targetKey,
          name: sc.target_symbol || (sc.target_file?.split('/').pop() || targetKey),
          node_type: sc.target_symbol ? 'function' : 'file',
          file_path: sc.target_file || '',
          metadata: {
            title: sc.target_symbol ? `Symbol: ${sc.target_symbol}` : `File: ${sc.target_file}`,
          },
        });
      }

      const scId = `sc_${sc.id || idx}`;
      nodeMap.set(scId, {
        id: scId,
        node_key: `scenario:${sc.title}`,
        name: sc.title?.length > 25 ? `${sc.title.substring(0, 25)}...` : sc.title,
        node_type: 'test',
        file_path: sc.target_file || '',
        metadata: {
          category: sc.category,
          coverage_gap: sc.coverage_gap,
          description: sc.description,
          status: sc.test_case?.sandbox_result || 'recommended',
        },
      });

      edgeList.push({
        id: `sc_edge_${idx}`,
        source: scId,
        target: targetId,
        source_node_id: scId,
        target_node_id: targetId,
        relation_type: sc.coverage_gap ? 'COVERS_GAP' : 'TESTS',
        evidence: `Scenario: ${sc.category} test for ${targetKey}`,
        is_inferred: false,
      });
    });

    existingTests.forEach((et, idx) => {
      const etId = `et_${idx}`;
      nodeMap.set(etId, {
        id: etId,
        node_key: et.test_name || `test_${idx}`,
        name: et.test_name || (et.test_file?.split('/').pop() || `Test ${idx + 1}`),
        node_type: 'test',
        file_path: et.test_file || '',
        metadata: {
          framework: et.framework,
          file: et.test_file,
        },
      });

      if (et.target_symbol) {
        const tgtId = `sym_${et.target_symbol.replace(/[^a-zA-Z0-9_-]/g, '_')}`;
        edgeList.push({
          id: `et_edge_${idx}`,
          source: etId,
          target: tgtId,
          source_node_id: etId,
          target_node_id: tgtId,
          relation_type: 'COVERS_EXISTING',
          evidence: `Existing test: ${et.test_name}`,
          is_inferred: false,
        });
      }
    });

    return { testGraphNodes: Array.from(nodeMap.values()), testGraphEdges: edgeList };
  }, [scenarios, existingTests]);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-3">
        <svg className="animate-spin w-8 h-8 text-primary" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth={3} />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
        <span className="text-sm font-medium text-text-muted">
          Analyzing code changes & generating test intelligence scenarios...
        </span>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-danger/10 border border-danger/30 rounded-lg p-5 text-center space-y-3">
        <p className="text-sm text-danger font-medium">
          Failed to load test intelligence: {error?.message || 'Unknown error'}
        </p>
        <button
          type="button"
          onClick={() => refetch()}
          className="px-3 py-1 text-xs font-semibold rounded bg-surfaceHighlight hover:bg-white/10 text-text-primary border border-border"
        >
          Retry
        </button>
      </div>
    );
  }

  // Filter scenarios
  const filteredScenarios = scenarios.filter((sc) => {
    if (selectedCategory !== 'all' && sc.category !== selectedCategory) return false;
    if (coverageGapOnly && !sc.coverage_gap) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        sc.target_symbol.toLowerCase().includes(q) ||
        sc.target_file.toLowerCase().includes(q) ||
        sc.title.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Top Header & Re-Analyze */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-bold text-text-primary flex items-center gap-2">
            <span>RepoMind AI Test Intelligence</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary font-mono font-bold">
              v2.0
            </span>
          </h2>
          <p className="text-xs text-text-muted mt-0.5">
            Automated test scenario recommendation, coverage gap detection, and sandboxed test execution.
          </p>
        </div>

        <button
          type="button"
          disabled={isAnalyzing}
          onClick={() => triggerAnalysis()}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded bg-surfaceHighlight hover:bg-white/10 text-text-primary border border-border transition-colors disabled:opacity-50"
        >
          {isAnalyzing ? (
            <>
              <svg className="animate-spin w-3.5 h-3.5 text-primary" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth={3} />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <span>Analyzing...</span>
            </>
          ) : (
            <>
              <svg className="w-3.5 h-3.5 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>Re-Analyze Tests</span>
            </>
          )}
        </button>
      </div>

      {/* KPI Overview Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-surface border border-border rounded-lg p-3.5 shadow-sm">
          <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider block mb-1">
            Recommended Scenarios
          </span>
          <span className="text-2xl font-bold font-mono text-text-primary">
            {dashboardData?.total_scenarios_count || 0}
          </span>
        </div>

        <div className="bg-surface border border-border rounded-lg p-3.5 shadow-sm">
          <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider block mb-1">
            Missing Coverage Gaps
          </span>
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold font-mono text-amber-400">
              {dashboardData?.coverage_gaps_count || 0}
            </span>
            {(dashboardData?.coverage_gaps_count || 0) > 0 && (
              <span className="text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                Action Required
              </span>
            )}
          </div>
        </div>

        <div className="bg-surface border border-border rounded-lg p-3.5 shadow-sm">
          <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider block mb-1">
            Generated Tests
          </span>
          <span className="text-2xl font-bold font-mono text-primary">
            {dashboardData?.generated_tests_count || 0}
          </span>
        </div>

        <div className="bg-surface border border-border rounded-lg p-3.5 shadow-sm">
          <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider block mb-1">
            Sandbox Verified Passed
          </span>
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold font-mono text-emerald-400">
              {dashboardData?.passed_tests_count || 0}
            </span>
            <span className="text-[11px] text-text-muted font-mono">
              / {dashboardData?.generated_tests_count || 0}
            </span>
          </div>
        </div>
      </div>

      {/* Sub-tabs: Scenarios | Existing Tests | Regression Suites */}
      <div className="flex items-center gap-2 border-b border-border pb-2">
        <button
          type="button"
          onClick={() => setActiveTab('scenarios')}
          className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
            activeTab === 'scenarios'
              ? 'bg-primary text-white shadow-sm'
              : 'text-text-muted hover:text-text-primary hover:bg-surfaceHighlight'
          }`}
        >
          Test Scenarios ({scenarios.length})
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('existing')}
          className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
            activeTab === 'existing'
              ? 'bg-primary text-white shadow-sm'
              : 'text-text-muted hover:text-text-primary hover:bg-surfaceHighlight'
          }`}
        >
          Existing Tests ({existingTests.length})
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('regression')}
          className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
            activeTab === 'regression'
              ? 'bg-primary text-white shadow-sm'
              : 'text-text-muted hover:text-text-primary hover:bg-surfaceHighlight'
          }`}
        >
          Regression Suites ({regressionFiles.length})
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('graph')}
          className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
            activeTab === 'graph'
              ? 'bg-primary text-white shadow-sm'
              : 'text-text-muted hover:text-text-primary hover:bg-surfaceHighlight'
          }`}
        >
          Coverage Graph ({testGraphNodes.length})
        </button>
      </div>

      {/* Main Tab 1: Scenarios View */}
      {activeTab === 'scenarios' && (
        <div className="space-y-4">
          {/* Controls: Category Filter + Search + Coverage Gap Toggle */}
          <div className="space-y-3">
            <div className="flex items-center gap-1.5 flex-wrap">
              {CATEGORIES.map((cat) => (
                <button
                  key={cat.id}
                  type="button"
                  onClick={() => setSelectedCategory(cat.id)}
                  className={`px-2.5 py-1 text-[11px] font-semibold rounded-full border transition-all ${
                    selectedCategory === cat.id
                      ? 'bg-primary/20 text-primary border-primary/50'
                      : 'bg-surfaceHighlight border-border text-text-secondary hover:text-text-primary'
                  }`}
                >
                  {cat.label}
                  {cat.id !== 'all' && dashboardData?.category_counts?.[cat.id] !== undefined && (
                    <span className="ml-1 text-[10px] opacity-75">
                      ({dashboardData.category_counts[cat.id]})
                    </span>
                  )}
                </button>
              ))}
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="relative flex-1 max-w-sm">
                <input
                  type="text"
                  placeholder="Filter by function name, file path..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-surfaceHighlight border border-border text-text-primary text-xs rounded-md pl-8 pr-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary placeholder-text-muted"
                />
                <svg
                  className="w-3.5 h-3.5 text-text-muted absolute left-2.5 top-2"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>

              <label className="flex items-center gap-2 cursor-pointer text-xs text-text-secondary select-none">
                <input
                  type="checkbox"
                  checked={coverageGapOnly}
                  onChange={(e) => setCoverageGapOnly(e.target.checked)}
                  className="rounded border-border text-primary focus:ring-primary focus:ring-offset-0 bg-surfaceHighlight"
                />
                <span>Missing Coverage Gaps Only</span>
              </label>
            </div>
          </div>

          {/* Scenarios List */}
          {filteredScenarios.length === 0 ? (
            <div className="bg-surface border border-border rounded-lg p-8 text-center text-text-muted text-xs">
              No test scenarios matching the selected filters.
            </div>
          ) : (
            <div className="space-y-3">
              {filteredScenarios.map((sc) => (
                <TestScenarioCard
                  key={sc.id}
                  scenario={sc}
                  onGenerateCode={generateCode}
                  isGenerating={generatingScenarioId === sc.id}
                  onExecuteTest={executeTest}
                  executingTestId={executingTestId}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Main Tab 2: Existing Repository Tests View */}
      {activeTab === 'existing' && (
        <div className="space-y-3">
          <div className="text-xs text-text-muted">
            Discovered test files across the repository used to benchmark test coverage.
          </div>

          {existingTests.length === 0 ? (
            <div className="bg-surface border border-border rounded-lg p-8 text-center text-text-muted text-xs">
              No existing test files discovered in repository documents.
            </div>
          ) : (
            <div className="bg-surface border border-border rounded-lg overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead className="bg-surfaceHighlight/50 border-b border-border text-[11px] text-text-muted uppercase font-semibold">
                  <tr>
                    <th className="py-2.5 px-4">Test File Path</th>
                    <th className="py-2.5 px-4">Framework</th>
                    <th className="py-2.5 px-4">Target Symbols</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {existingTests.map((t, idx) => (
                    <tr key={idx} className="hover:bg-white/[0.02] transition-colors">
                      <td className="py-2.5 px-4 font-mono font-medium text-text-primary">
                        {t.test_file}
                      </td>
                      <td className="py-2.5 px-4 font-mono uppercase text-primary text-[11px]">
                        {t.test_framework}
                      </td>
                      <td className="py-2.5 px-4 text-text-secondary">
                        {t.tested_symbols.length > 0 ? (
                          <div className="flex items-center gap-1.5 flex-wrap">
                            {t.tested_symbols.map((sym, sidx) => (
                              <span key={sidx} className="font-mono text-[11px] px-1.5 py-0.5 rounded bg-surfaceHighlight border border-border">
                                {sym}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className="text-text-muted italic">General test suite</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Main Tab 3: Regression Test Suites View */}
      {activeTab === 'regression' && (
        <div className="space-y-3">
          <div className="bg-primary/10 border border-primary/20 rounded-lg p-4 space-y-2">
            <h4 className="text-xs font-bold text-primary uppercase tracking-wider flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <span>Regression Test Requirements</span>
            </h4>
            <p className="text-xs text-text-secondary leading-relaxed">
              Based on the Code Knowledge Graph and Change Impact traversal, these existing test suites MUST be executed during continuous integration to ensure changed interfaces have not caused downstream regressions.
            </p>
          </div>

          {regressionFiles.length === 0 ? (
            <div className="bg-surface border border-border rounded-lg p-8 text-center text-text-muted text-xs">
              No existing regression test suites identified for this change set.
            </div>
          ) : (
            <div className="space-y-2">
              {regressionFiles.map((rf, idx) => (
                <div
                  key={idx}
                  className="bg-surface border border-border rounded-lg p-3 flex items-center justify-between gap-3 font-mono text-xs"
                >
                  <span className="text-text-primary font-medium">{rf}</span>
                  <code className="text-[11px] text-primary bg-primary/10 border border-primary/20 px-2 py-0.5 rounded">
                    {rf.endsWith('.py') ? `pytest ${rf}` : `npm test -- ${rf}`}
                  </code>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Main Tab 4: Interactive Test Coverage Graph */}
      {activeTab === 'graph' && (
        <div className="bg-surface border border-border rounded-lg overflow-hidden space-y-2">
          <div className="p-3 bg-surfaceHighlight/40 border-b border-border flex items-center justify-between text-xs text-text-secondary">
            <span>
              Test-to-Symbol Coverage: <strong className="text-text-primary font-mono">{testGraphNodes.length}</strong> nodes across scenarios and target code
            </span>
            <span className="text-[11px] text-text-muted">
              Select any node to view coverage metadata and tests
            </span>
          </div>
          <EngineeringGraphEngine
            nodes={testGraphNodes}
            edges={testGraphEdges}
            height="520px"
            availableModes={['all', 'function', 'test']}
            graphMode="test"
          />
        </div>
      )}
    </div>
  );
}

