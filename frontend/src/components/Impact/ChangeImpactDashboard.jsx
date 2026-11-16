import React, { useState } from 'react';
import ImpactOverview from './ImpactOverview';
import BreakingChangesList from './BreakingChangesList';
import AffectedComponentList from './AffectedComponentList';
import ImpactGraphViewer from './ImpactGraphViewer';
import TestRecommendations from './TestRecommendations';

export default function ChangeImpactDashboard({
  impactData,
  isLoading = false,
  repositoryId,
  pullRequestId,
}) {
  const [activeSubTab, setActiveSubTab] = useState('overview');

  if (isLoading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-28 bg-surfaceHighlight/30 rounded-lg border border-border" />
        <div className="grid grid-cols-4 gap-4">
          <div className="h-24 bg-surfaceHighlight/30 rounded-lg border border-border" />
          <div className="h-24 bg-surfaceHighlight/30 rounded-lg border border-border" />
          <div className="h-24 bg-surfaceHighlight/30 rounded-lg border border-border" />
          <div className="h-24 bg-surfaceHighlight/30 rounded-lg border border-border" />
        </div>
        <div className="h-64 bg-surfaceHighlight/30 rounded-lg border border-border" />
      </div>
    );
  }

  if (!impactData || (!impactData.id && impactData.directly_affected_count === 0 && !impactData.affected_components?.length)) {
    return (
      <div className="bg-surface border border-border rounded-lg p-10 text-center space-y-3">
        <div className="w-12 h-12 rounded-full bg-surfaceHighlight mx-auto flex items-center justify-center text-text-muted">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <h3 className="text-base font-semibold text-text-primary">
          No Change Impact Data
        </h3>
        <p className="text-[13px] text-text-secondary max-w-md mx-auto">
          No blast radius analysis has been performed yet for this pull request. Analysis runs automatically when the PR review pipeline is executed.
        </p>
      </div>
    );
  }

  const subTabs = [
    { id: 'overview', label: 'Overview' },
    {
      id: 'affected',
      label: 'Affected Components',
      count: impactData.affected_components?.length || (impactData.directly_affected_count + impactData.indirectly_affected_count),
    },
    {
      id: 'breaking',
      label: 'Breaking Changes',
      count: impactData.breaking_changes?.length || impactData.breaking_changes_count,
      alert: (impactData.breaking_changes?.length || impactData.breaking_changes_count) > 0,
    },
    { id: 'graph', label: 'Dependency Graph' },
    {
      id: 'tests',
      label: 'Recommended Tests',
      count: impactData.test_recommendations?.length || 0,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Sub-tab Navigation */}
      <div className="flex items-center gap-2 border-b border-border pb-2 overflow-x-auto">
        {subTabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveSubTab(tab.id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
              activeSubTab === tab.id
                ? 'bg-surfaceHighlight text-text-primary font-semibold border border-border shadow-sm'
                : 'text-text-muted hover:text-text-primary hover:bg-white/[0.02]'
            }`}
          >
            <span>{tab.label}</span>
            {tab.count !== undefined && tab.count !== null && (
              <span
                className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ${
                  tab.alert
                    ? 'bg-danger/20 text-danger border border-danger/30'
                    : activeSubTab === tab.id
                    ? 'bg-primary/20 text-primary'
                    : 'bg-surfaceHighlight text-text-muted'
                }`}
              >
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Panels */}
      {activeSubTab === 'overview' && (
        <div className="space-y-6">
          <ImpactOverview impactData={impactData} />
          {impactData.breaking_changes && impactData.breaking_changes.length > 0 && (
            <BreakingChangesList breakingChanges={impactData.breaking_changes} />
          )}
          <ImpactGraphViewer graphVisualization={impactData.graph_visualization} />
        </div>
      )}

      {activeSubTab === 'affected' && (
        <AffectedComponentList affectedComponents={impactData.affected_components || []} />
      )}

      {activeSubTab === 'breaking' && (
        <BreakingChangesList breakingChanges={impactData.breaking_changes || []} />
      )}

      {activeSubTab === 'graph' && (
        <ImpactGraphViewer graphVisualization={impactData.graph_visualization} />
      )}

      {activeSubTab === 'tests' && (
        <TestRecommendations testRecommendations={impactData.test_recommendations || []} />
      )}
    </div>
  );
}
