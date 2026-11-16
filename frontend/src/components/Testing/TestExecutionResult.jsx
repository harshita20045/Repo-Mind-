import React from 'react';

export default function TestExecutionResult({ testCase }) {
  if (!testCase) return null;

  const status = testCase.execution_status || 'pending';
  const result = testCase.execution_result || {};

  const STATUS_CONFIG = {
    passed: {
      label: 'Verified Passed',
      badge: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
      icon: (
        <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      ),
    },
    failed: {
      label: 'Assertion Failed',
      badge: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
      icon: (
        <svg className="w-4 h-4 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      ),
    },
    running: {
      label: 'Executing in Sandbox...',
      badge: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
      icon: (
        <svg className="animate-spin w-4 h-4 text-blue-400" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
      ),
    },
    error: {
      label: 'Sandbox Error / Security Rejection',
      badge: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
      icon: (
        <svg className="w-4 h-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      ),
    },
    pending: {
      label: 'Generated (Not Executed)',
      badge: 'bg-surfaceHighlight text-text-muted border-border',
      icon: (
        <svg className="w-4 h-4 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
  };

  const currentCfg = STATUS_CONFIG[status] || STATUS_CONFIG.pending;

  return (
    <div className="mt-3 bg-surfaceHighlight/30 border border-border rounded-lg p-3.5 space-y-2">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          {currentCfg.icon}
          <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider border ${currentCfg.badge}`}>
            {currentCfg.label}
          </span>
          {result.duration_ms !== undefined && (
            <span className="text-[11px] text-text-muted font-mono">
              ({result.duration_ms}ms)
            </span>
          )}
        </div>

        <div className="flex items-center gap-2 text-[11px] font-mono text-text-secondary">
          {testCase.security_reviewed && (
            <span className="inline-flex items-center gap-1 text-emerald-400">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              AST Security Verified
            </span>
          )}
        </div>
      </div>

      {status === 'pending' && (
        <p className="text-[11px] text-text-muted">
          This test has been generated according to scenario specifications but has not yet been executed in the isolated sandbox. Click <strong>"Run in Sandbox"</strong> below to execute and verify assertions.
        </p>
      )}

      {status === 'passed' && (
        <div className="text-[12px] text-emerald-400 font-mono flex items-center gap-2">
          <span>✓ All assertions passed cleanly in isolated environment (exit code 0).</span>
        </div>
      )}

      {status === 'failed' && (
        <div className="space-y-1.5">
          <div className="text-[11px] font-semibold text-rose-400 uppercase tracking-wider">
            Failure Output / Traceback:
          </div>
          <pre className="text-[11px] font-mono bg-black/40 border border-rose-500/30 text-rose-300 p-2.5 rounded overflow-x-auto whitespace-pre-wrap max-h-48">
            {result.failure_details || result.stderr || result.stdout || 'Test assertions failed.'}
          </pre>
        </div>
      )}

      {status === 'error' && (
        <div className="space-y-1.5">
          <div className="text-[11px] font-semibold text-amber-400 uppercase tracking-wider">
            Security Rejection / Error Details:
          </div>
          <pre className="text-[11px] font-mono bg-black/40 border border-amber-500/30 text-amber-300 p-2.5 rounded overflow-x-auto whitespace-pre-wrap max-h-48">
            {result.failure_details || result.stderr || 'Execution aborted due to security violation or environment error.'}
          </pre>
        </div>
      )}
    </div>
  );
}

