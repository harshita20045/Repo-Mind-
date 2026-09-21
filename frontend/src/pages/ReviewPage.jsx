import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reviewApi, githubApi, orgApi, mlApi } from '../lib/api';
import { useOutletContext } from 'react-router-dom';
import { usePermissions, Permissions } from '../hooks/usePermissions';
import ReviewStateIndicator from '../components/Review/ReviewStateIndicator';
import FindingList from '../components/Review/FindingList';
import ChatAssistant from '../components/Review/ChatAssistant';
import RiskAssessment from '../components/Review/RiskAssessment';
import ConflictList from '../components/Review/ConflictList';
import { RiskBadge, StatusBadge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import Modal from '../components/ui/Modal';

// ─── Tab button ────────────────────────────────────────────────────────────────
function Tab({ id, label, isActive, count, onClick }) {
  return (
    <button
      role="tab"
      aria-selected={isActive}
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-all duration-150 ${
        isActive
          ? 'text-primary border-primary'
          : 'text-text-muted border-transparent hover:text-text-secondary hover:border-white/20'
      }`}
    >
      {label}
      {count !== null && count !== undefined && (
        <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${
          isActive ? 'bg-primary/15 text-primary' : 'bg-white/5 text-text-muted'
        }`}>
          {count}
        </span>
      )}
    </button>
  );
}

// ─── PR sidebar detail row ─────────────────────────────────────────────────────
function DetailRow({ label, children }) {
  return (
    <div>
      <div className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-1">{label}</div>
      <div className="text-sm text-text-secondary">{children}</div>
    </div>
  );
}

// ─── Risk gauge (compact sidebar version) ─────────────────────────────────────
function RiskGauge({ score, level }) {
  const isHigh = score > 70;
  const isMed = score > 40;
  const color = isHigh ? 'text-danger' : isMed ? 'text-warning' : score > 0 ? 'text-success' : 'text-text-muted';
  const trackColor = isHigh ? 'text-danger' : isMed ? 'text-warning' : score > 0 ? 'text-success' : 'text-text-muted';
  const r = 30;
  const circ = 2 * Math.PI * r;
  const filled = circ - (circ * (score || 0)) / 100;

  return (
    <div className="flex items-center gap-4">
      <div className="relative w-20 h-20 flex-shrink-0">
        <svg className="w-20 h-20 -rotate-90" viewBox="0 0 68 68" aria-hidden="true">
          <circle cx="34" cy="34" r={r} fill="none" stroke="currentColor" strokeWidth="6" className="text-white/5" />
          <circle
            cx="34" cy="34" r={r}
            fill="none" stroke="currentColor" strokeWidth="6"
            strokeDasharray={circ}
            strokeDashoffset={filled}
            strokeLinecap="round"
            className={`${trackColor} transition-all duration-1000`}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-xl font-bold tabular-nums leading-none ${color}`}>{score ?? '—'}</span>
          <span className="text-2xs text-text-muted">/ 100</span>
        </div>
      </div>
      <div>
        <div className={`text-sm font-bold ${color}`}>
          {isHigh ? 'High Risk' : isMed ? 'Medium Risk' : score > 0 ? 'Low Risk' : 'Pending'}
        </div>
        {level && (
          <div className="text-xs text-text-muted capitalize mt-0.5">{level}</div>
        )}
      </div>
    </div>
  );
}

// ─── Approval Modal ────────────────────────────────────────────────────────────
function ApprovalModal({ isOpen, action, onClose, onSubmit, isLoading }) {
  const [note, setNote] = useState('');
  const isApprove = action === 'approve';

  React.useEffect(() => {
    if (!isOpen) setNote('');
  }, [isOpen]);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isApprove ? 'Approve Pull Request' : 'Request Changes'}
      subtitle={isApprove
        ? 'Confirm AI risk findings reviewed and PR is safe to merge.'
        : 'Specify changes needed before this PR can be merged.'}
      size="sm"
    >
      <div className="space-y-4">
        <div className={`flex items-start gap-3 p-3 rounded-lg border text-sm ${
          isApprove
            ? 'bg-success/8 border-success/20 text-success'
            : 'bg-danger/8 border-danger/20 text-danger'
        }`}>
          {isApprove ? (
            <svg className="w-4 h-4 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          ) : (
            <svg className="w-4 h-4 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )}
          <span>{isApprove ? 'This will mark the PR as approved for merge.' : 'This will request changes and block merging.'}</span>
        </div>

        <div>
          <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
            Note <span className="text-text-muted font-normal normal-case">(optional)</span>
          </label>
          <textarea
            value={note}
            onChange={e => setNote(e.target.value)}
            placeholder={isApprove ? 'LGTM — reviewed risk findings.' : 'Please address the security vulnerabilities before merging.'}
            rows={3}
            className="w-full bg-surfaceHighlight/40 border border-white/[0.09] text-text-primary text-sm rounded-lg px-3.5 py-2.5 focus:outline-none focus:ring-2 focus:ring-primary/40 placeholder-text-muted resize-none transition-all"
          />
        </div>

        <div className="flex gap-3 justify-end pt-1">
          <Button variant="ghost" size="sm" onClick={onClose} disabled={isLoading}>Cancel</Button>
          <Button
            variant={isApprove ? 'success-solid' : 'danger-solid'}
            size="sm"
            loading={isLoading}
            onClick={() => onSubmit({ action, note })}
          >
            {isApprove ? 'Approve PR' : 'Request Changes'}
          </Button>
        </div>
      </div>
    </Modal>
  );
}

// ─── Main Review Page ─────────────────────────────────────────────────────────
export default function ReviewPage() {
  const { rid, prid } = useParams();
  const queryClient = useQueryClient();
  const { memberships } = useOutletContext();
  const { can } = usePermissions(memberships);

  const [activeRunId, setActiveRunId] = useState(null);
  const [activeTab, setActiveTab] = useState('findings');
  const [approvalModal, setApprovalModal] = useState({ isOpen: false, action: null });

  const canApprove = can(Permissions.PRS_APPROVE);
  const canReview = can(Permissions.PRS_REVIEW);

  // ─── Queries ───────────────────────────────────────────────────────────────
  const { data: runData, error: runError } = useQuery({
    queryKey: ['reviewRun', activeRunId],
    queryFn: () => reviewApi.getReviewRun(activeRunId),
    enabled: !!activeRunId,
    refetchInterval: (query) => {
      if (!query.state.data) return 2000;
      const s = query.state.data.status;
      return ['completed', 'failed', 'cancelled'].includes(s) ? false : 2000;
    },
  });

  const { mutate: triggerReview, isPending: isTriggering, error: triggerError } = useMutation({
    mutationFn: () => reviewApi.triggerReview(prid),
    onSuccess: (data) => setActiveRunId(data.job_id),
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
      setApprovalModal({ isOpen: false, action: null });
    },
    onError: (err) => {
      console.error('Decision failed:', err.message);
    },
  });

  React.useEffect(() => {
    if (!activeRunId) triggerReview();
  }, [prid]);

  // ─── Derived state ─────────────────────────────────────────────────────────
  const currentStatus = runData?.status || null;
  const isCompleted = currentStatus === 'completed';
  const error = triggerError || runError;
  const existingDecision = runData?.human_decisions?.length > 0
    ? runData.human_decisions[runData.human_decisions.length - 1]
    : null;

  const findings = runData?.findings || [];
  const conflicts = runData?.conflicts || [];
  const riskScore = runData?.risk_assessment?.risk_score;

  // ─── Tab config ────────────────────────────────────────────────────────────
  const tabs = [
    { id: 'findings', label: 'Findings', count: isCompleted ? findings.length : null },
    { id: 'risk', label: 'Risk Assessment', count: null },
    { id: 'conflicts', label: 'Conflicts', count: isCompleted ? conflicts.length : null },
    { id: 'chat', label: 'AI Assistant', count: null },
  ];

  // ─── Risk summary bar color ────────────────────────────────────────────────
  const riskLevel = riskScore > 70 ? 'high' : riskScore > 40 ? 'medium' : riskScore > 0 ? 'low' : null;

  return (
    <div className="space-y-5 animate-slide-up">

      {/* PR Header */}
      <div className="bg-surface border border-white/[0.07] rounded-xl p-5">
        <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-xs text-text-muted mb-2">
              <Link to="/repositories" className="hover:text-text-secondary transition-colors">Repositories</Link>
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
              <Link to={`/repositories/${rid}/pull-requests`} className="hover:text-text-secondary transition-colors font-mono">
                {repoData?.github_name || `repo-${rid}`}
              </Link>
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
              <span className="font-mono">PR #{prData?.github_number || prid}</span>
            </div>
            <h1 className="text-xl font-bold text-text-primary tracking-tight leading-snug">
              {loadingPr ? (
                <span className="skeleton inline-block h-7 w-96 rounded" />
              ) : (
                prData?.title || 'Pull Request'
              )}
            </h1>
            {prData && (
              <div className="flex items-center gap-3 mt-2">
                <StatusBadge status={prData.state} label={prData.state} />
                <span className="text-xs text-text-muted">by <span className="text-text-secondary font-medium">{prData.author}</span></span>
                {prData.head_sha && (
                  <span className="font-mono text-xs text-text-muted bg-white/5 border border-white/[0.07] px-2 py-0.5 rounded">
                    {prData.head_sha.substring(0, 7)}
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Decision area */}
          <div className="flex items-center gap-3 flex-shrink-0 flex-wrap">
            {existingDecision && (
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-semibold border ${
                existingDecision.action === 'approve'
                  ? 'bg-success/8 text-success border-success/20'
                  : 'bg-danger/8 text-danger border-danger/20'
              }`}>
                {existingDecision.action === 'approve' ? (
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                )}
                {existingDecision.action === 'approve' ? 'Approved' : 'Changes Requested'}
              </div>
            )}

            {(canReview || canApprove) && (
              <>
                <Button
                  variant="danger"
                  size="sm"
                  disabled={!isCompleted || isSubmittingDecision}
                  onClick={() => setApprovalModal({ isOpen: true, action: 'reject' })}
                >
                  Request Changes
                </Button>
                {canApprove && (
                  <Button
                    variant="success-solid"
                    size="sm"
                    disabled={!isCompleted || isSubmittingDecision}
                    onClick={() => setApprovalModal({ isOpen: true, action: 'approve' })}
                  >
                    Approve PR
                  </Button>
                )}
              </>
            )}
          </div>
        </div>

        {/* Risk summary bar */}
        {isCompleted && riskLevel && (
          <div className={`mt-4 pt-4 border-t border-white/[0.06] flex items-center gap-3 text-xs`}>
            <span className="text-text-muted font-medium">Overall Risk</span>
            <RiskBadge level={riskLevel} />
            {runData?.risk_assessment?.explanation && (
              <span className="text-text-muted truncate hidden lg:block">
                {runData.risk_assessment.explanation.substring(0, 100)}…
              </span>
            )}
          </div>
        )}
      </div>

      {/* Main workspace: 3-col-wide + 1-col-sidebar */}
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-5">

        {/* Left: Tabs + content */}
        <div className="xl:col-span-3 space-y-0">
          {/* Tab bar */}
          <div
            className="flex gap-0 border-b border-white/[0.07] bg-surface rounded-t-xl px-2 pt-1 overflow-x-auto"
            role="tablist"
            aria-label="Review sections"
          >
            {tabs.map(tab => (
              <Tab
                key={tab.id}
                id={tab.id}
                label={tab.label}
                count={tab.count}
                isActive={activeTab === tab.id}
                onClick={() => setActiveTab(tab.id)}
              />
            ))}
          </div>

          {/* Tab content */}
          <div className="bg-surface border border-t-0 border-white/[0.07] rounded-b-xl p-6 min-h-[480px]">
            {activeTab === 'chat' ? (
              <ChatAssistant
                organizationId={runData?.organization_id || memberships?.[0]?.organization_id}
                repositoryId={runData?.repository_id || parseInt(rid)}
                contextType="pr"
                contextId={prid}
              />
            ) : !isCompleted ? (
              <ReviewStateIndicator
                status={currentStatus}
                isPending={isTriggering}
                error={error}
                onTrigger={() => triggerReview()}
              />
            ) : (
              <div className="animate-fade-in">
                {activeTab === 'findings' && <FindingList findings={findings} />}
                {activeTab === 'risk' && <RiskAssessment riskData={runData?.risk_assessment} />}
                {activeTab === 'conflicts' && <ConflictList conflicts={conflicts} />}
              </div>
            )}
          </div>
        </div>

        {/* Right: metadata sidebar */}
        <div className="space-y-4">
          {/* Risk profile */}
          <div className="bg-surface border border-white/[0.07] rounded-xl p-4">
            <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-4">Risk Profile</h3>
            {isCompleted && runData?.risk_assessment ? (
              <>
                <RiskGauge
                  score={runData.risk_assessment.risk_score}
                  level={runData.risk_assessment.security_risk_level}
                />
                {runData.risk_assessment.explanation && (
                  <p className="text-xs text-text-muted mt-3 leading-relaxed line-clamp-4">
                    {runData.risk_assessment.explanation}
                  </p>
                )}
              </>
            ) : (
              <div className="text-xs text-text-muted italic">
                {currentStatus === 'running' || currentStatus === 'pending' || isTriggering
                  ? 'Analyzing...'
                  : 'Awaiting analysis'}
              </div>
            )}
          </div>

          {/* ML Prediction */}
          <div className="bg-surface border border-white/[0.07] rounded-xl p-4">
            <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-3">ML Delay Prediction</h3>
            <div className="space-y-2.5 text-sm">
              <DetailRow label="Category">
                {mlPrediction ? (
                  <span className={`font-bold ${mlPrediction.predicted_delay_category === 'SLOW' ? 'text-warning' : 'text-success'}`}>
                    {mlPrediction.predicted_delay_category}
                  </span>
                ) : (
                  <span className="text-text-muted italic text-xs">Insufficient data</span>
                )}
              </DetailRow>
              {mlPrediction?.confidence_score != null && (
                <DetailRow label="Confidence">
                  <span className="text-text-secondary">
                    {(mlPrediction.confidence_score * 100).toFixed(0)}%
                  </span>
                </DetailRow>
              )}
            </div>
          </div>

          {/* PR Details */}
          <div className="bg-surface border border-white/[0.07] rounded-xl p-4">
            <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-3">PR Details</h3>
            <div className="space-y-3">
              <DetailRow label="Author">
                <div className="flex items-center gap-2">
                  <div className="w-5 h-5 rounded-full bg-gradient-to-br from-accent/30 to-primary/30 border border-white/10 flex items-center justify-center text-2xs font-bold text-white flex-shrink-0">
                    {prData?.author?.charAt(0).toUpperCase() || 'U'}
                  </div>
                  {prData?.author || '—'}
                </div>
              </DetailRow>
              <DetailRow label="State">
                {prData?.state
                  ? <StatusBadge status={prData.state} label={prData.state} />
                  : <span className="text-text-muted">—</span>
                }
              </DetailRow>
              {prData?.head_sha && (
                <DetailRow label="Commit">
                  <span className="font-mono text-xs bg-white/5 border border-white/[0.07] px-2 py-0.5 rounded">
                    {prData.head_sha.substring(0, 7)}
                  </span>
                </DetailRow>
              )}
              {existingDecision && (
                <DetailRow label="Decision">
                  <StatusBadge
                    status={existingDecision.action === 'approve' ? 'approved' : 'rejected'}
                    label={existingDecision.action === 'approve' ? 'Approved' : 'Rejected'}
                  />
                </DetailRow>
              )}
            </div>
          </div>

          {/* Run info */}
          {runData && (
            <div className="bg-surface border border-white/[0.07] rounded-xl p-4">
              <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-3">Review Run</h3>
              <div className="space-y-2.5">
                <DetailRow label="Status">
                  <StatusBadge status={currentStatus} label={currentStatus || '—'} />
                </DetailRow>
                {runData.run_number != null && (
                  <DetailRow label="Run #">
                    <span className="font-mono text-xs text-text-secondary">#{runData.run_number}</span>
                  </DetailRow>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Approval Modal */}
      <ApprovalModal
        isOpen={approvalModal.isOpen}
        action={approvalModal.action}
        onClose={() => setApprovalModal({ isOpen: false, action: null })}
        onSubmit={submitDecision}
        isLoading={isSubmittingDecision}
      />
    </div>
  );
}
