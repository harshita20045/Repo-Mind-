import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reviewApi } from '../lib/api';
import ReviewStateIndicator from '../components/Review/ReviewStateIndicator';
import FindingList from '../components/Review/FindingList';
import ChatAssistant from '../components/Review/ChatAssistant';
import RiskAssessment from '../components/Review/RiskAssessment';
import ConflictList from '../components/Review/ConflictList';

export default function ReviewPage({ user }) {
  const { rid, prid } = useParams();
  const queryClient = useQueryClient();
  const [activeRunId, setActiveRunId] = useState(null);
  const [activeTab, setActiveTab] = useState('findings');

  // Poll for the review run status if we have an active run ID
  const { data: runData, error: runError } = useQuery({
    queryKey: ['reviewRun', activeRunId],
    queryFn: () => reviewApi.getReviewRun(activeRunId),
    enabled: !!activeRunId,
    refetchInterval: (query) => {
      if (!query.state.data) return 2000;
      const status = query.state.data.status;
      if (['completed', 'failed', 'cancelled'].includes(status)) {
        return false;
      }
      return 2000;
    },
  });

  // Mutation to trigger a new review
  const { mutate: triggerReview, isPending: isTriggering, error: triggerError } = useMutation({
    mutationFn: () => reviewApi.triggerReview(prid),
    onSuccess: (data) => {
      setActiveRunId(data.job_id);
    },
  });

  const currentStatus = runData?.status || null;
  const error = triggerError || runError;

  const tabs = [
    { id: 'risk', label: 'Risk Assessment', badge: 'Critical' },
    { id: 'findings', label: 'Findings', badge: '5' },
    { id: 'conflicts', label: 'Conflicts', badge: '1' },
    { id: 'chat', label: 'AI Assistant', badge: null }
  ];

  return (
    <div className="space-y-6 animate-slide-up">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <Link to="/repositories" className="text-gray-400 hover:text-white transition-colors">
              backend-api
            </Link>
            <span className="text-gray-600">/</span>
            <span className="text-white font-medium">PR #{prid}</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Implement Payment Gateway Integration</h1>
        </div>
        
        <div className="flex items-center gap-3">
          <button className="px-4 py-2 bg-surfaceHighlight/50 hover:bg-surfaceHighlight text-white rounded-lg font-medium transition-colors border border-white/10">
            Dismiss All
          </button>
          <button className="px-4 py-2 bg-danger/10 hover:bg-danger/20 text-danger rounded-lg font-medium transition-colors border border-danger/20">
            Request Changes
          </button>
          <button className="px-4 py-2 bg-success hover:bg-success/90 text-white rounded-lg font-medium transition-colors shadow-lg shadow-success/20 border border-white/10">
            Approve PR
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* Left Column - Tabs & Content */}
        <div className="lg:col-span-3 space-y-6">
          
          {/* Tabs */}
          <div className="flex gap-2 border-b border-white/5 pb-px">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`relative px-4 py-2.5 text-sm font-medium transition-colors flex items-center gap-2 rounded-t-lg ${
                  activeTab === tab.id 
                    ? 'text-primary bg-surface/50 border-t border-l border-r border-white/5 backdrop-blur-md' 
                    : 'text-gray-400 hover:text-gray-200 hover:bg-white/5 border border-transparent'
                }`}
              >
                {tab.label}
                {tab.badge && (
                  <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                    activeTab === tab.id ? 'bg-primary/20 text-primary' : 'bg-surfaceHighlight text-gray-300'
                  }`}>
                    {tab.badge}
                  </span>
                )}
                {activeTab === tab.id && (
                  <span className="absolute bottom-[-1px] left-0 w-full h-px bg-surface"></span>
                )}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div className="bg-surface/50 backdrop-blur-md border border-white/5 rounded-2xl rounded-tl-none p-6 min-h-[500px]">
            {(!activeRunId || currentStatus !== 'completed') && activeTab !== 'chat' ? (
              <div className="max-w-2xl">
                <ReviewStateIndicator 
                  status={currentStatus} 
                  isPending={isTriggering} 
                  error={error} 
                  onTrigger={() => triggerReview()} 
                />
              </div>
            ) : (
              <div>
                {activeTab === 'findings' && <FindingList findings={runData?.findings || []} />}
                {activeTab === 'risk' && <RiskAssessment riskData={runData?.risk_assessment} />}
                {activeTab === 'conflicts' && <ConflictList conflicts={runData?.conflicts || []} />}
                {activeTab === 'chat' && (
                  <ChatAssistant 
                    organizationId={runData?.organization_id || 1} 
                    repositoryId={runData?.repository_id || 1} 
                    contextType="pr" 
                    contextId={prid} 
                  />
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Column - PR Metadata Sidebar */}
        <div className="space-y-6">
          <div className="bg-surface/50 backdrop-blur-md border border-white/5 rounded-2xl p-5">
            <h3 className="text-sm font-bold text-gray-300 uppercase tracking-wider mb-4">Risk Profile</h3>
            <div className="flex items-center gap-4 mb-4">
              <div className="relative w-16 h-16 flex items-center justify-center rounded-full border-4 border-danger/30">
                <span className="text-xl font-bold text-danger">85</span>
              </div>
              <div>
                <div className="text-danger font-bold">Critical Risk</div>
                <div className="text-xs text-gray-400">Blast radius: 4 modules</div>
              </div>
            </div>
            <div className="space-y-2 text-sm text-gray-300">
              <div className="flex justify-between">
                <span className="text-gray-400">Security:</span>
                <span className="text-danger font-medium">High</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Architecture:</span>
                <span className="text-warning font-medium">Medium</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Tests:</span>
                <span className="text-success font-medium">Low</span>
              </div>
            </div>
          </div>
          
          <div className="bg-surface/50 backdrop-blur-md border border-white/5 rounded-2xl p-5">
            <h3 className="text-sm font-bold text-gray-300 uppercase tracking-wider mb-3">PR Details</h3>
            <div className="space-y-3 text-sm">
              <div>
                <div className="text-gray-500 mb-0.5">Author</div>
                <div className="flex items-center gap-2 text-gray-300">
                  <div className="w-5 h-5 rounded-full bg-gradient-to-tr from-accent to-primary flex items-center justify-center text-[10px] font-bold text-white">J</div>
                  Jane Doe
                </div>
              </div>
              <div>
                <div className="text-gray-500 mb-0.5">Branch</div>
                <div className="font-mono text-gray-300 bg-white/5 px-2 py-1 rounded inline-block text-xs">feature/payment-gw</div>
              </div>
              <div>
                <div className="text-gray-500 mb-0.5">Changes</div>
                <div className="text-gray-300"><span className="text-success">+452</span> <span className="text-danger">-12</span> in 8 files</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
