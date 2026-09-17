import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reviewApi, githubApi, orgApi, mlApi } from '../lib/api';
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

  const { data: mlPrediction } = useQuery({
    queryKey: ['mlPrediction', prid],
    queryFn: () => mlApi.getPrPrediction(prid),
    enabled: !!prid,
    retry: false,
  });

  const { data: prData, isLoading: loadingPr } = useQuery({
    queryKey: ['pullRequest', prid],
    queryFn: () => githubApi.getPullRequest(prid),
    enabled: !!prid,
  });

  const { data: repoData } = useQuery({
    queryKey: ['repository', rid],
    queryFn: () => orgApi.getRepository(rid),
    enabled: !!rid,
  });

  const { mutate: submitDecision, isPending: isSubmittingDecision } = useMutation({
    mutationFn: (decision) => reviewApi.approveReviewRun(activeRunId, decision),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reviewRun', activeRunId] });
    },
    onError: (err) => {
      alert(`Failed to submit decision: ${err.message}`);
    }
  });

  // Automatically fetch existing review run on mount
  React.useEffect(() => {
    if (!activeRunId) {
      triggerReview();
    }
  }, [prid]);

  const handleDecision = (action) => {
    if (!activeRunId || currentStatus !== 'completed') {
      alert("Review must be completed first.");
      return;
    }
    const note = prompt(`Enter optional note for your ${action}:`);
    if (note === null) return; // cancelled
    submitDecision({ action, note });
  };

  const currentStatus = runData?.status || null;
  const error = triggerError || runError;
  const existingDecision = runData?.human_decisions?.length > 0 ? runData.human_decisions[runData.human_decisions.length - 1] : null;

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
            <Link to={`/repositories/${rid}/pull-requests`} className="text-gray-400 hover:text-white transition-colors">
              {repoData?.github_name || 'repository'}
            </Link>
            <span className="text-gray-600">/</span>
            <span className="text-white font-medium">PR #{prData?.github_number || prid}</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white">{prData?.title || 'Loading Pull Request...'}</h1>
        </div>
        
        <div className="flex items-center gap-3">
          {existingDecision && (
            <div className={`px-3 py-1.5 rounded-lg text-sm font-medium border ${
              existingDecision.action === 'approve' 
                ? 'bg-success/10 text-success border-success/20' 
                : 'bg-danger/10 text-danger border-danger/20'
            }`}>
              {existingDecision.action === 'approve' ? 'Approved' : 'Changes Requested'}
            </div>
          )}
          <button 
            onClick={() => handleDecision('reject')}
            disabled={isSubmittingDecision || currentStatus !== 'completed'}
            className="px-4 py-2 bg-danger/10 hover:bg-danger/20 text-danger rounded-lg font-medium transition-colors border border-danger/20 disabled:opacity-50"
          >
            Request Changes
          </button>
          <button 
            onClick={() => handleDecision('approve')}
            disabled={isSubmittingDecision || currentStatus !== 'completed'}
            className="px-4 py-2 bg-success hover:bg-success/90 text-white rounded-lg font-medium transition-colors shadow-lg shadow-success/20 border border-white/10 disabled:opacity-50"
          >
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
              <div className={`relative w-16 h-16 flex items-center justify-center rounded-full border-4 ${
                runData?.risk_assessment?.score > 70 ? 'border-danger/30 text-danger' : 
                runData?.risk_assessment?.score > 40 ? 'border-warning/30 text-warning' : 
                'border-success/30 text-success'
              }`}>
                <span className="text-xl font-bold">{runData?.risk_assessment?.score || '--'}</span>
              </div>
              <div>
                <div className={`font-bold ${
                  runData?.risk_assessment?.score > 70 ? 'text-danger' : 
                  runData?.risk_assessment?.score > 40 ? 'text-warning' : 
                  'text-success'
                }`}>
                  {runData?.risk_assessment?.score > 70 ? 'High Risk' : 
                   runData?.risk_assessment?.score > 40 ? 'Medium Risk' : 
                   runData?.risk_assessment?.score ? 'Low Risk' : 'Pending'}
                </div>
                <div className="text-xs text-gray-400">
                  {runData?.risk_assessment?.summary || 'Waiting for review...'}
                </div>
              </div>
            </div>
          </div>
          
          <div className="bg-surface/50 backdrop-blur-md border border-white/5 rounded-2xl p-5">
            <h3 className="text-sm font-bold text-gray-300 uppercase tracking-wider mb-3">ML Delay Prediction</h3>
            <div className="space-y-3 text-sm">
              <div>
                <div className="text-gray-500 mb-0.5">Prediction Category</div>
                <div className="flex items-center gap-2 text-gray-300">
                  {mlPrediction ? (
                    <span className={mlPrediction.predicted_delay_category === 'SLOW' ? 'text-warning font-bold' : 'text-success font-bold'}>
                      {mlPrediction.predicted_delay_category}
                    </span>
                  ) : (
                    <span className="text-gray-500 italic">Not Available</span>
                  )}
                </div>
              </div>
              {mlPrediction && mlPrediction.confidence_score && (
                <div>
                  <div className="text-gray-500 mb-0.5">Confidence Score</div>
                  <div className="text-gray-300\">{(mlPrediction.confidence_score * 100).toFixed(0)}%</div>
                </div>
              )}
            </div>
          </div>

          <div className="bg-surface/50 backdrop-blur-md border border-white/5 rounded-2xl p-5">
            <h3 className="text-sm font-bold text-gray-300 uppercase tracking-wider mb-3">PR Details</h3>
            <div className="space-y-3 text-sm">
              <div>
                <div className="text-gray-500 mb-0.5">Author</div>
                <div className="flex items-center gap-2 text-gray-300">
                  <div className="w-5 h-5 rounded-full bg-gradient-to-tr from-accent to-primary flex items-center justify-center text-[10px] font-bold text-white">
                    {prData?.author?.charAt(0).toUpperCase() || 'U'}
                  </div>
                  {prData?.author || 'Unknown'}
                </div>
              </div>
              <div>
                <div className="text-gray-500 mb-0.5">Commit SHA</div>
                <div className="font-mono text-gray-300 bg-white/5 px-2 py-1 rounded inline-block text-xs">
                  {prData?.head_sha ? prData.head_sha.substring(0, 7) : 'unknown'}
                </div>
              </div>
              <div>
                <div className="text-gray-500 mb-0.5">Status</div>
                <div className="text-gray-300 capitalize">{prData?.state || 'unknown'}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
