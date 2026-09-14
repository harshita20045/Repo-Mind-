import React from 'react';

export default function ReviewStateIndicator({ status, isPending, error, onTrigger }) {
  if (error) {
    return (
      <div className="p-6 bg-red-500/10 border border-red-500/20 rounded-xl text-center">
        <h3 className="text-red-400 font-semibold mb-2">Error</h3>
        <p className="text-red-300/80 text-sm mb-4">{error.message || 'An error occurred fetching review state'}</p>
        <button onClick={onTrigger} className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors text-sm font-medium">
          Try Again
        </button>
      </div>
    );
  }

  if (isPending || status === 'pending' || status === 'running') {
    return (
      <div className="p-8 bg-slate-900/50 border border-indigo-500/20 rounded-xl flex flex-col items-center justify-center min-h-[200px]">
        <div className="animate-spin h-10 w-10 border-4 border-indigo-600 border-t-transparent rounded-full mb-4"></div>
        <h3 className="text-indigo-400 font-medium text-lg mb-1">
          {status === 'running' ? 'Analysis in Progress' : 'Review Queued'}
        </h3>
        <p className="text-slate-400 text-sm">
          {status === 'running' 
            ? 'The review engine is currently analyzing the code...' 
            : 'Waiting for a worker to pick up the review job...'}
        </p>
      </div>
    );
  }

  if (status === 'failed') {
    return (
      <div className="p-6 bg-red-500/10 border border-red-500/20 rounded-xl text-center">
        <h3 className="text-red-400 font-semibold mb-2">Review Failed</h3>
        <p className="text-red-300/80 text-sm mb-4">The background worker encountered an error while reviewing the pull request.</p>
        <button onClick={onTrigger} className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors text-sm font-medium">
          Retry Review
        </button>
      </div>
    );
  }

  if (status === 'cancelled') {
    return (
      <div className="p-6 bg-orange-500/10 border border-orange-500/20 rounded-xl text-center">
        <h3 className="text-orange-400 font-semibold mb-2">Review Cancelled</h3>
        <p className="text-orange-300/80 text-sm mb-4">The review run was cancelled before it could complete.</p>
        <button onClick={onTrigger} className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors text-sm font-medium">
          Restart Review
        </button>
      </div>
    );
  }

  return (
    <div className="p-8 bg-slate-900/50 border border-slate-800 rounded-xl flex flex-col items-center justify-center text-center">
      <div className="w-12 h-12 bg-slate-800 text-slate-400 rounded-full flex items-center justify-center mb-4">
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 21h7a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v11m0 5l4.879-4.879m0 0a3 3 0 104.243-4.242 3 3 0 00-4.243 4.242z" />
        </svg>
      </div>
      <h3 className="text-white font-medium text-lg mb-2">No active review</h3>
      <p className="text-slate-400 text-sm mb-6 max-w-md">
        Start an AI-powered code review to analyze this pull request for bugs, security vulnerabilities, style issues, and more.
      </p>
      <button 
        onClick={onTrigger} 
        disabled={isPending}
        className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-colors font-medium shadow-lg shadow-indigo-600/20 disabled:opacity-50"
      >
        Run Review
      </button>
    </div>
  );
}
