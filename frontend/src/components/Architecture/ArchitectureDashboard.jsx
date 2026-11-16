import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { architectureApi } from '../../lib/api';
import ArchitectureHealthOverview from './ArchitectureHealthOverview';
import ArchitectureViolationsList from './ArchitectureViolationsList';
import CircularDependencyGraph from './CircularDependencyGraph';
import FlowAnalysisViewer from './FlowAnalysisViewer';
import ArchitectureRuleManager from './ArchitectureRuleManager';
import MermaidViewer from '../Onboarding/MermaidViewer';
import { SectionCard } from '../ui/Card';

export default function ArchitectureDashboard({ repositoryId }) {
  const [activeSubTab, setActiveSubTab] = useState('overview');
  const queryClient = useQueryClient();

  // Queries
  const { data: analysis, isLoading: loadingAnalysis } = useQuery({
    queryKey: ['architecture-analysis', repositoryId],
    queryFn: () => architectureApi.getLatestAnalysis(repositoryId),
    enabled: !!repositoryId,
  });

  const { data: rules = [], isLoading: loadingRules } = useQuery({
    queryKey: ['architecture-rules', repositoryId],
    queryFn: () => architectureApi.getRules(repositoryId),
    enabled: !!repositoryId,
  });

  const { data: circularDeps = [], isLoading: loadingCycles } = useQuery({
    queryKey: ['architecture-circular', repositoryId],
    queryFn: () => architectureApi.getCircularDependencies(repositoryId),
    enabled: !!repositoryId && (activeSubTab === 'circular' || activeSubTab === 'overview'),
  });

  const { data: flows = [], isLoading: loadingFlows } = useQuery({
    queryKey: ['architecture-flows', repositoryId],
    queryFn: () => architectureApi.getFlows(repositoryId),
    enabled: !!repositoryId && activeSubTab === 'flows',
  });

  // Mutations
  const triggerAuditMutation = useMutation({
    mutationFn: () => architectureApi.triggerAnalysis(repositoryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['architecture-analysis', repositoryId] });
      queryClient.invalidateQueries({ queryKey: ['architecture-circular', repositoryId] });
      queryClient.invalidateQueries({ queryKey: ['architecture-flows', repositoryId] });
    },
  });

  const createRuleMutation = useMutation({
    mutationFn: (payload) => architectureApi.createRule(repositoryId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['architecture-rules', repositoryId] });
    },
  });

  const updateRuleMutation = useMutation({
    mutationFn: ({ ruleId, payload }) => architectureApi.updateRule(repositoryId, ruleId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['architecture-rules', repositoryId] });
    },
  });

  const deleteRuleMutation = useMutation({
    mutationFn: (ruleId) => architectureApi.deleteRule(repositoryId, ruleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['architecture-rules', repositoryId] });
    },
  });

  const resetRulesMutation = useMutation({
    mutationFn: () => architectureApi.resetRules(repositoryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['architecture-rules', repositoryId] });
    },
  });

  const violations = analysis?.violations || [];
  const isMutating =
    createRuleMutation.isPending ||
    updateRuleMutation.isPending ||
    deleteRuleMutation.isPending ||
    resetRulesMutation.isPending;

  const subTabs = [
    { id: 'overview', label: 'Overview & Topology' },
    {
      id: 'violations',
      label: 'Rule Violations',
      count: violations.length,
      alert: violations.some((v) => v.severity === 'critical'),
    },
    {
      id: 'circular',
      label: 'Circular Dependencies',
      count: circularDeps.length,
      alert: circularDeps.length > 0,
    },
    {
      id: 'flows',
      label: 'Execution Flows',
      count: flows.length,
    },
    {
      id: 'rules',
      label: 'Rule Governance',
      count: rules.length,
    },
  ];

  if (loadingAnalysis && !analysis) {
    return (
      <div className="p-8 text-center text-text-muted space-y-3">
        <div className="w-8 h-8 rounded-full border-2 border-primary border-t-transparent animate-spin mx-auto" />
        <p className="text-xs">Auditing repository architecture design...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Sub-tab Navigation */}
      <div className="flex items-center gap-2 border-b border-border pb-2 overflow-x-auto">
        {subTabs.map((tab) => (
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
          <ArchitectureHealthOverview
            analysis={analysis}
            onTriggerAudit={() => triggerAuditMutation.mutate()}
            isAuditing={triggerAuditMutation.isPending}
          />

          {/* Mermaid Architecture Topology Flowchart */}
          <SectionCard title="Architecture Layer Topology">
            {analysis?.mermaid_diagram ? (
              <div className="p-2 overflow-x-auto">
                <MermaidViewer chart={analysis.mermaid_diagram} />
              </div>
            ) : (
              <div className="p-6 text-center text-text-muted text-xs">
                No topology diagram generated yet.
              </div>
            )}
          </SectionCard>

          {/* Quick Violations Preview if any */}
          {violations.length > 0 && (
            <SectionCard title={`Active Rule Violations (${violations.length})`}>
              <ArchitectureViolationsList violations={violations.slice(0, 5)} />
            </SectionCard>
          )}
        </div>
      )}

      {activeSubTab === 'violations' && (
        <ArchitectureViolationsList violations={violations} />
      )}

      {activeSubTab === 'circular' && (
        <CircularDependencyGraph circularDependencies={circularDeps} />
      )}

      {activeSubTab === 'flows' && (
        <FlowAnalysisViewer flows={flows} />
      )}

      {activeSubTab === 'rules' && (
        <ArchitectureRuleManager
          rules={rules}
          onCreateRule={(payload) => createRuleMutation.mutate(payload)}
          onUpdateRule={(ruleId, payload) => updateRuleMutation.mutate({ ruleId, payload })}
          onDeleteRule={(ruleId) => deleteRuleMutation.mutate(ruleId)}
          onResetRules={() => resetRulesMutation.mutate()}
          isMutating={isMutating}
        />
      )}
    </div>
  );
}
