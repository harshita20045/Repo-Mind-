import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reviewApi } from '../lib/api';
import ReviewStateIndicator from '../components/Review/ReviewStateIndicator';
import FindingList from '../components/Review/FindingList';

export default function ReviewPage({ user, onLogout }) {
  const { rid, prid } = useParams();
  const queryClient = useQueryClient();
  const [activeRunId, setActiveRunId] = useState(null);

  // Poll for the review run status if we have an active run ID
  const { data: runData, error: runError } = useQuery({
    queryKey: ['reviewRun', activeRunId],
    queryFn: () => reviewApi.getReviewRun(activeRunId),
    enabled: !!activeRunId,
    // Stop polling if we reach a terminal state
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

  const handleLogout = async () => {
    try {
      const { authApi } = await import('../lib/api');
      await authApi.logout();
    } catch (e) {}
    onLogout();
  };

  const currentStatus = runData?.status || null;
  const isTerminal = ['completed', 'failed', 'cancelled'].includes(currentStatus);
  const error = triggerError || runError;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur px-6 py-4 flex justify-between items-center">
        <div className="flex items-center gap-4">
          <Link to="/" className="text-slate-400 hover:text-white transition">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </Link>
          <div>
            <h1 className="text-lg font-bold text-white leading-none">Code Review</h1>
            <span className="text-xs text-slate-400">PR #{prid} &middot; Repo #{rid}</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <p className="text-xs font-semibold text-slate-200 hidden sm:block">{user.email}</p>
          <button
            onClick={handleLogout}
            className="px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition"
          >
            Sign Out
          </button>
        </div>
      </header>

      <main className="max-w-5xl mx-auto p-8 space-y-6">
        {(!activeRunId || currentStatus !== 'completed') && (
          <ReviewStateIndicator 
            status={currentStatus} 
            isPending={isTriggering} 
            error={error} 
            onTrigger={() => triggerReview()} 
          />
        )}

        {activeRunId && currentStatus === 'completed' && (
          <FindingList findings={runData?.findings} />
        )}
      </main>
    </div>
  );
}
