import React, { useState } from 'react';
import TestExecutionResult from './TestExecutionResult';

export default function TestCodeViewer({ testCase, onExecute, isExecuting }) {
  const [copied, setCopied] = useState(false);

  if (!testCase) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(testCase.test_code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="mt-3 border border-border rounded-lg overflow-hidden bg-black/40">
      <div className="flex items-center justify-between px-3.5 py-2 bg-surfaceHighlight/50 border-b border-border">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono font-bold text-primary uppercase">
            {testCase.framework}
          </span>
          <span className="text-[11px] text-text-muted font-mono truncate max-w-xs">
            {testCase.test_file_path}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleCopy}
            className="flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium rounded bg-surfaceHighlight hover:bg-white/10 text-text-secondary hover:text-text-primary border border-border transition-colors"
          >
            {copied ? (
              <>
                <svg className="w-3.5 h-3.5 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-success">Copied</span>
              </>
            ) : (
              <>
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                <span>Copy Code</span>
              </>
            )}
          </button>

          <button
            type="button"
            disabled={isExecuting}
            onClick={() => onExecute(testCase.id)}
            className="flex items-center gap-1.5 px-3 py-1 text-[11px] font-semibold rounded bg-primary hover:bg-primary-hover text-white transition-colors disabled:opacity-50 shadow-sm"
          >
            {isExecuting ? (
              <>
                <svg className="animate-spin w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                <span>Running...</span>
              </>
            ) : (
              <>
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>Run in Sandbox</span>
              </>
            )}
          </button>
        </div>
      </div>

      <pre className="p-3 text-[12px] font-mono text-text-primary overflow-x-auto whitespace-pre leading-relaxed">
        <code>{testCase.test_code}</code>
      </pre>

      <div className="p-3 bg-surface border-t border-border">
        <TestExecutionResult testCase={testCase} />
      </div>
    </div>
  );
}

