import React, { useState } from 'react';
import TestCodeViewer from './TestCodeViewer';

const CATEGORY_THEMES = {
  positive: {
    label: 'Positive Flow',
    badge: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  },
  negative: {
    label: 'Negative / Error',
    badge: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
  },
  boundary: {
    label: 'Boundary / Limits',
    badge: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  },
  validation: {
    label: 'Input Validation',
    badge: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
  },
  authentication: {
    label: 'Authentication (401)',
    badge: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  },
  authorization: {
    label: 'Authorization / RBAC (403)',
    badge: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  },
  integration: {
    label: 'E2E Integration',
    badge: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  },
  regression: {
    label: 'Downstream Regression',
    badge: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
  },
};

const PRIORITY_BADGES = {
  critical: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
  high: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
  medium: 'bg-blue-500/20 text-blue-300 border-blue-500/40',
  low: 'bg-surfaceHighlight text-text-muted border-border',
};

export default function TestScenarioCard({
  scenario,
  onGenerateCode,
  isGenerating,
  onExecuteTest,
  executingTestId,
}) {
  const [isExpanded, setIsExpanded] = useState(false);

  const categoryConfig = CATEGORY_THEMES[scenario.category] || {
    label: scenario.category,
    badge: 'bg-surfaceHighlight text-text-primary border-border',
  };

  const priorityBadge = PRIORITY_BADGES[scenario.priority] || PRIORITY_BADGES.medium;
  const hasGeneratedTest = scenario.generated_tests && scenario.generated_tests.length > 0;
  const latestTest = hasGeneratedTest ? scenario.generated_tests[scenario.generated_tests.length - 1] : null;

  return (
    <div className="bg-surface border border-border rounded-lg p-4 transition-all hover:border-white/20 space-y-3">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider border ${categoryConfig.badge}`}>
            {categoryConfig.label}
          </span>
          <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${priorityBadge}`}>
            {scenario.priority}
          </span>
          <span className="font-mono text-xs font-semibold text-text-primary">
            {scenario.target_symbol}
          </span>
          {scenario.coverage_gap && (
            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              Missing Test Coverage
            </span>
          )}
        </div>

        <span className="font-mono text-[11px] text-text-muted truncate max-w-xs">
          Target: {scenario.target_file}
        </span>
      </div>

      {/* Scenario Title and Description */}
      <div>
        <h4 className="text-[13px] font-semibold text-text-primary leading-snug mb-1">
          {scenario.title}
        </h4>
        <p className="text-[12px] text-text-secondary leading-relaxed">
          {scenario.description}
        </p>
      </div>

      {/* Edge Case Notes */}
      {scenario.edge_case_notes && (
        <div className="bg-surfaceHighlight/40 border border-border/80 rounded p-2.5 flex items-start gap-2">
          <svg className="w-3.5 h-3.5 text-accent mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div className="text-[11px] text-text-secondary leading-normal">
            <strong className="text-text-primary font-semibold">Edge Case Consideration:</strong> {scenario.edge_case_notes}
          </div>
        </div>
      )}

      {/* Suggested Assertions Collapsible */}
      {scenario.suggested_assertions && scenario.suggested_assertions.length > 0 && (
        <div className="space-y-1">
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-1.5 text-[11px] font-medium text-text-muted hover:text-text-primary transition-colors"
          >
            <svg
              className={`w-3.5 h-3.5 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
            <span>{isExpanded ? 'Hide Suggested Assertions' : `View ${scenario.suggested_assertions.length} Suggested Assertions`}</span>
          </button>

          {isExpanded && (
            <ul className="mt-2 space-y-1 pl-4 border-l-2 border-primary/30 text-[11px] text-text-secondary font-mono">
              {scenario.suggested_assertions.map((assertion, idx) => (
                <li key={idx} className="leading-relaxed">
                  • {assertion}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Impacted APIs & Services */}
      {(scenario.impacted_endpoints?.length > 0 || scenario.impacted_services?.length > 0) && (
        <div className="flex items-center gap-2 flex-wrap text-[11px] pt-1">
          {scenario.impacted_endpoints?.length > 0 && (
            <span className="inline-flex items-center gap-1 text-primary">
              <span className="font-semibold">Impacted API:</span>
              <code className="font-mono bg-primary/10 border border-primary/20 px-1.5 py-0.5 rounded text-[10px]">
                {scenario.impacted_endpoints[0]}
              </code>
            </span>
          )}
          {scenario.existing_test_file && (
            <span className="inline-flex items-center gap-1 text-text-muted">
              <span>Related Test File:</span>
              <code className="font-mono bg-surfaceHighlight border border-border px-1.5 py-0.5 rounded text-[10px]">
                {scenario.existing_test_file}
              </code>
            </span>
          )}
        </div>
      )}

      {/* Action / Test Generation */}
      <div className="pt-2 border-t border-border flex items-center justify-between flex-wrap gap-2">
        <div className="text-[11px] text-text-muted">
          {hasGeneratedTest ? (
            <span className="text-emerald-400 font-medium">✓ Test code generated</span>
          ) : (
            <span>No code generated yet</span>
          )}
        </div>

        {!hasGeneratedTest ? (
          <button
            type="button"
            disabled={isGenerating}
            onClick={() => onGenerateCode(scenario.id)}
            className="flex items-center gap-1.5 px-3 py-1 text-[11px] font-semibold rounded bg-surfaceHighlight hover:bg-white/10 text-primary border border-primary/30 hover:border-primary transition-all disabled:opacity-50"
          >
            {isGenerating ? (
              <>
                <svg className="animate-spin w-3.5 h-3.5 text-primary" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth={3} />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                <span>Generating Test Code...</span>
              </>
            ) : (
              <>
                <svg className="w-3.5 h-3.5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                </svg>
                <span>Generate Test Code</span>
              </>
            )}
          </button>
        ) : (
          <button
            type="button"
            disabled={isGenerating}
            onClick={() => onGenerateCode(scenario.id)}
            className="text-[11px] font-medium text-text-muted hover:text-text-primary transition-colors underline"
          >
            Regenerate Code
          </button>
        )}
      </div>

      {/* Generated Test Code Display & Sandbox Runner */}
      {hasGeneratedTest && latestTest && (
        <TestCodeViewer
          testCase={latestTest}
          onExecute={onExecuteTest}
          isExecuting={executingTestId === latestTest.id}
        />
      )}
    </div>
  );
}

