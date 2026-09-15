import React from 'react';

export default function ReviewStateIndicator({ status, isPending, error, onTrigger }) {
  if (error) {
    return (
      <div className="p-8 bg-danger/10 border border-danger/20 rounded-2xl text-center backdrop-blur-sm shadow-inner animate-fade-in max-w-lg mx-auto mt-8">
        <h3 className="text-danger font-bold text-lg mb-2">Error Occurred</h3>
        <p className="text-danger/80 text-sm mb-6">{error.message || 'An error occurred fetching review state'}</p>
        <button onClick={onTrigger} className="px-5 py-2 bg-surfaceHighlight hover:bg-surfaceHighlight/80 text-white rounded-xl transition-colors text-sm font-medium border border-white/10 shadow-lg">
          Try Again
        </button>
      </div>
    );
  }

  if (isPending || status === 'pending' || status === 'running') {
    return (
      <div className="p-10 bg-surface/30 border border-primary/20 rounded-2xl flex flex-col items-center justify-center min-h-[300px] backdrop-blur-sm animate-fade-in shadow-inner max-w-lg mx-auto mt-8 relative overflow-hidden">
        <div className="absolute inset-0 bg-primary/5 animate-pulse-slow pointer-events-none"></div>
        <div className="relative z-10 flex flex-col items-center">
          <div className="relative mb-6">
            <div className="absolute inset-0 bg-primary rounded-full blur-xl opacity-30 animate-pulse-slow"></div>
            <div className="relative animate-spin h-14 w-14 border-4 border-primary/30 border-t-primary rounded-full"></div>
          </div>
          <h3 className="text-white font-bold text-xl mb-2 tracking-tight">
            {status === 'running' ? 'Analysis in Progress' : 'Review Queued'}
          </h3>
          <p className="text-gray-400 text-sm text-center max-w-sm leading-relaxed">
            {status === 'running' 
              ? 'The AI intelligence engine is currently deeply analyzing the codebase for risk, semantic conflicts, and security vulnerabilities...' 
              : 'Waiting for a background worker to pick up the review job from the queue...'}
          </p>
        </div>
      </div>
    );
  }

  if (status === 'failed') {
    return (
      <div className="p-8 bg-danger/10 border border-danger/20 rounded-2xl text-center backdrop-blur-sm shadow-inner animate-fade-in max-w-lg mx-auto mt-8">
        <div className="w-16 h-16 bg-danger/20 text-danger rounded-full flex items-center justify-center mx-auto mb-4 border border-danger/30">
          <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h3 className="text-danger font-bold text-lg mb-2">Review Failed</h3>
        <p className="text-danger/80 text-sm mb-6 max-w-sm mx-auto leading-relaxed">The background worker encountered an unexpected error while generating the intelligence report.</p>
        <button onClick={onTrigger} className="px-5 py-2.5 bg-danger hover:bg-danger/90 text-white rounded-xl transition-colors text-sm font-medium shadow-lg shadow-danger/25 border border-white/10">
          Retry Review
        </button>
      </div>
    );
  }

  if (status === 'cancelled') {
    return (
      <div className="p-8 bg-warning/10 border border-warning/20 rounded-2xl text-center backdrop-blur-sm shadow-inner animate-fade-in max-w-lg mx-auto mt-8">
        <h3 className="text-warning font-bold text-lg mb-2">Review Cancelled</h3>
        <p className="text-warning/80 text-sm mb-6 max-w-sm mx-auto">The automated review run was cancelled before completion.</p>
        <button onClick={onTrigger} className="px-5 py-2 bg-surfaceHighlight hover:bg-surfaceHighlight/80 text-white rounded-xl transition-colors text-sm font-medium border border-white/10 shadow-lg">
          Restart Review
        </button>
      </div>
    );
  }

  return (
    <div className="p-10 bg-surface/40 border border-white/5 rounded-2xl flex flex-col items-center justify-center text-center backdrop-blur-md animate-fade-in max-w-lg mx-auto mt-8 shadow-2xl">
      <div className="w-16 h-16 bg-gradient-to-br from-surfaceHighlight to-surface text-gray-400 rounded-2xl flex items-center justify-center mb-6 border border-white/10 shadow-inner">
        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 21h7a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v11m0 5l4.879-4.879m0 0a3 3 0 104.243-4.242 3 3 0 00-4.243 4.242z" />
        </svg>
      </div>
      <h3 className="text-white font-bold text-2xl tracking-tight mb-3">No Active Review</h3>
      <p className="text-gray-400 text-sm mb-8 max-w-md leading-relaxed">
        Initiate an AI-powered code review to analyze this pull request for complex semantic conflicts, security vulnerabilities, and architectural risks.
      </p>
      <button 
        onClick={onTrigger} 
        disabled={isPending}
        className="px-6 py-3 bg-primary hover:bg-primary-hover text-white rounded-xl transition-all font-medium shadow-lg shadow-primary/25 disabled:opacity-50 border border-white/10 flex items-center gap-2"
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        Generate Intelligence Report
      </button>
    </div>
  );
}
