import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reviewApi, githubApi, orgApi } from '../lib/api';
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
import { SectionCard } from '../components/ui/Card';

function Tab({ id, label, isActive, count, onClick }) {
  return (
    <button
      role="tab"
      aria-selected={isActive}
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-3 text-[13px] font-medium border-b-2 transition-all duration-150 ${
        isActive
          ? 'text-primary border-primary'
          : 'text-text-muted border-transparent hover:text-text-primary hover:border-white/20'
      }`}
    >
      {label}
      {count !== null && count !== undefined && (
        <span className={`text-[11px] font-bold px-1.5 py-0.5 rounded-full ${
          isActive ? 'bg-primary/10 text-primary' : 'bg-surfaceHighlight text-text-muted'
        }`}>
          {count}
        </span>
      )}
    </button>
  );
}

function DetailRow({ label, children }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-[11px] font-medium text-text-muted uppercase tracking-wider">{label}</span>
      <div className="text-[13px] text-text-primary">{children}</div>
    </div>
  );
}

function RiskGauge({ score, level }) {
  const isHigh = score > 70;
  const isMed = score > 40;
  const color = isHigh ? 'text-danger' : isMed ? 'text-warning' : score > 0 ? 'text-success' : 'text-text-muted';
  const trackColor = isHigh ? 'text-danger' : isMed ? 'text-warning' : score > 0 ? 'text-success' : 'text-text-muted';
  const r = 32;
  const circ = 2 * Math.PI * r;
  const filled = circ - (circ * (score || 0)) / 100;

  return (
    <div className="flex items-center gap-5">
      <div className="relative w-[72px] h-[72px] flex-shrink-0">
        <svg className="w-[72px] h-[72px] -rotate-90" viewBox="0 0 72 72" aria-hidden="true">
          <circle cx="36" cy="36" r={r} fill="none" stroke="currentColor" strokeWidth="6" className="text-surfaceHighlight" />
          <circle
            cx="36" cy="36" r={r}
            fill="none" stroke="currentColor" strokeWidth="6"
            strokeDasharray={circ}
            strokeDashoffset={filled}
            strokeLinecap="round"
            className={`${trackColor} transition-all duration-1000`}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-[20px] font-bold tabular-nums leading-none tracking-tight ${color}`}>{score ?? '—'}</span>
        </div>
      </div>
      <div>
        <div className={`text-sm font-semibold tracking-tight ${color}`}>
          {isHigh ? 'High Risk' : isMed ? 'Medium Risk' : score > 0 ? 'Low Risk' : 'Pending'}
        </div>
        {level && (
          <div className="text-[12px] text-text-secondary capitalize mt-0.5">{level}</div>
        )}
      </div>
    </div>
  );
}

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
      title={isApprove ? 'Approve Pull Request' : action === 'reject' ? 'Reject Pull Request' : 'Request Changes'}
      subtitle={isApprove
        ? 'Confirm AI risk findings reviewed and PR is safe to merge.'
        : action === 'reject' ? 'Permanently reject this PR. No further automated re-reviews will occur.' : 'Specify changes needed before this PR can be merged.'}
      size="sm"
    >
      <div className="space-y-4">
        <div className={`flex items-start gap-3 p-3 rounded-md border text-[13px] ${
          isApprove
            ? 'bg-success/10 border-success/20 text-success'
            : 'bg-danger/10 border-danger/20 text-danger'
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
          <span>{isApprove ? 'This will mark the PR as approved for merge.' : action === 'reject' ? 'This will reject the PR and stop the review cycle.' : 'This will request changes and block merging.'}</span>
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
            Note <span className="text-text-muted font-normal normal-case">(optional)</span>
          </label>
          <textarea
            value={note}
            onChange={e => setNote(e.target.value)}
            placeholder={isApprove ? 'LGTM — reviewed risk findings.' : 'Please address the security vulnerabilities before merging.'}
            rows={3}
            className="w-full bg-surfaceHighlight border border-border text-text-primary text-[13px] rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary placeholder-text-muted resize-none transition-all"
          />
        </div>

        <div className="flex gap-2 justify-end pt-2">
          <Button variant="ghost" size="sm" onClick={onClose} disabled={isLoading}>Cancel</Button>
          <Button
            variant={isApprove ? 'success-solid' : 'danger-solid'}
            size="sm"
            loading={isLoading}
            onClick={() => onSubmit({ action, note })}
          >
            {isApprove ? 'Approve PR' : action === 'reject' ? 'Reject PR' : 'Request Changes'}
          </Button>
        </div>
      </div>
    </Modal>
  );
}

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

  const { data: prData, isLoading: loadingPr } = useQuery({
    queryKey: ['pullRequest', prid],
    queryFn: () => githubApi.getPullRequest(prid),
    enabled: !!prid,
  });

  const { data: prEvents } = useQuery({
    queryKey: ['pullRequestEvents', prid],
    queryFn: () => githubApi.getPullRequestEvents(prid),
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
    onError: (err) => console.error('Decision failed:', err.message),
  });

  const { mutate: mergePr, isPending: isMerging } = useMutation({
    mutationFn: () => githubApi.mergePullRequest(prid),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pullRequest', prid] });
      alert('Merge requested successfully.');
    },
    onError: (err) => alert(`Merge failed: ${err.message}`),
  });

  React.useEffect(() => {
    if (!activeRunId) triggerReview();
  }, [prid]);

  const currentStatus = runData?.status || null;
  const isCompleted = currentStatus === 'completed';
  const error = triggerError || runError;
  const existingDecision = runData?.human_decisions?.length > 0
    ? runData.human_decisions[runData.human_decisions.length - 1]
    : null;

  const findings = runData?.findings || [];
  const conflicts = runData?.conflicts || [];
  const riskScore = runData?.risk_assessment?.risk_score;

  const tabs = [
    { id: 'findings', label: 'Findings', count: isCompleted ? findings.length : null },
    { id: 'risk', label: 'Risk Assessment', count: null },
    { id: 'conflicts', label: 'Conflicts', count: isCompleted ? conflicts.length : null },
    { id: 'chat', label: 'AI Assistant', count: null },
    { id: 'events', label: 'Activity Log', count: null },
  ];

  const riskLevel = riskScore > 70 ? 'high' : riskScore > 40 ? 'medium' : riskScore > 0 ? 'low' : null;

  return (
    <div className="space-y-6 animate-slide-up max-w-[1400px]">
      {/* PR Header */}
      <div className="bg-surface border border-border rounded-lg p-6 shadow-sm">
        <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-5">
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-[13px] text-text-muted mb-2 font-mono">
              <Link to={`/repositories/${rid}/pull-requests`} className="hover:text-primary transition-colors">
                {repoData?.github_name || `repo-${rid}`}
              </Link>
              <span className="text-border">/</span>
              <span className="text-text-secondary">PR #{prData?.github_number || prid}</span>
            </div>
            
            <h1 className="text-[22px] font-semibold text-text-primary tracking-tight leading-snug mb-3">
              {loadingPr ? (
                <span className="skeleton inline-block h-7 w-96 rounded" />
              ) : (
                prData?.title || 'Pull Request'
              )}
            </h1>
            
            {prData && (
              <div className="flex items-center gap-3">
                <StatusBadge status={prData.state} label={prData.state} />
                <div className="w-1 h-1 rounded-full bg-border" />
                <div className="flex items-center gap-1.5">
                  <div className="w-4 h-4 rounded bg-surfaceHighlight border border-border flex items-center justify-center text-[9px] font-bold text-text-secondary">
                    {prData.author?.charAt(0).toUpperCase() || 'U'}
                  </div>
                  <span className="text-[13px] font-medium text-text-secondary">{prData.author}</span>
                </div>
                {prData.head_sha && (
                  <>
                    <div className="w-1 h-1 rounded-full bg-border" />
                    <span className="font-mono text-[12px] text-text-muted bg-surfaceHighlight border border-border px-1.5 py-0.5 rounded">
                      {prData.head_sha.substring(0, 7)}
                    </span>
                  </>
                )}
              </div>
            )}
          </div>

          <div className="flex items-center gap-2.5 flex-shrink-0 flex-wrap">
            {existingDecision && (
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-[13px] font-medium border ${
                existingDecision.action === 'approve'
                  ? 'bg-success/10 text-success border-success/20'
                  : 'bg-danger/10 text-danger border-danger/20'
              }`}>
                {existingDecision.action === 'approve' ? 'Approved' : 'Changes Requested'}
              </div>
            )}

            {(canReview || canApprove) && (
              <>
                <Button
                  variant="danger"
                  size="sm"
                  disabled={!isCompleted || isSubmittingDecision}
                  onClick={() => setApprovalModal({ isOpen: true, action: 'request_changes' })}
                >
                  Request Changes
                </Button>
                {canApprove && (
                  <>
                    <Button
                      variant="success-solid"
                      size="sm"
                      disabled={!isCompleted || isSubmittingDecision}
                      onClick={() => setApprovalModal({ isOpen: true, action: 'approve' })}
                    >
                      Approve
                    </Button>
                    <Button
                      variant="primary"
                      size="sm"
                      loading={isMerging}
                      disabled={!isCompleted || prData?.state === 'merged'}
                      onClick={() => mergePr()}
                    >
                      Merge PR
                    </Button>
                  </>
                )}
              </>
            )}
          </div>
        </div>

        {isCompleted && riskLevel && (
          <div className="mt-5 pt-4 border-t border-border flex items-center gap-3">
            <span className="text-[12px] font-semibold text-text-muted uppercase tracking-wider">Analysis Result</span>
            <RiskBadge level={riskLevel} />
            {runData?.risk_assessment?.explanation && (
              <span className="text-[13px] text-text-secondary truncate hidden lg:block ml-2">
                {runData.risk_assessment.explanation.substring(0, 100)}…
              </span>
            )}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[1fr_300px] gap-6">
        {/* Main Content */}
        <div className="flex flex-col min-h-0 bg-surface border border-border rounded-lg shadow-sm overflow-hidden">
          <div className="flex gap-2 border-b border-border bg-surfaceHighlight/20 px-2 pt-2 overflow-x-auto">
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

          <div className="p-6 min-h-[500px]">
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
                {activeTab === 'events' && <ActivityLog events={prEvents} />}
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          <SectionCard title="Risk Profile">
            {isCompleted && runData?.risk_assessment ? (
              <div className="flex flex-col gap-4">
                <RiskGauge
                  score={runData.risk_assessment.risk_score}
                  level={runData.risk_assessment.security_risk_level}
                />
                {runData.risk_assessment.explanation && (
                  <p className="text-[13px] text-text-secondary leading-relaxed">
                    {runData.risk_assessment.explanation}
                  </p>
                )}
              </div>
            ) : (
              <div className="text-[13px] text-text-muted italic">
                {currentStatus === 'running' || currentStatus === 'pending' || isTriggering
                  ? 'Analyzing pull request...'
                  : 'Awaiting analysis'}
              </div>
            )}
          </SectionCard>

          <SectionCard title="PR Context">
            <div className="space-y-4">
              <DetailRow label="Author">
                <div className="flex items-center gap-2">
                  <div className="w-5 h-5 rounded border border-border bg-surfaceHighlight flex items-center justify-center text-[10px] font-semibold text-text-secondary">
                    {prData?.author?.charAt(0).toUpperCase() || 'U'}
                  </div>
                  {prData?.author || '—'}
                </div>
              </DetailRow>
              <DetailRow label="State">
                {prData?.state ? <StatusBadge status={prData.state} label={prData.state} /> : '—'}
              </DetailRow>
              {prData?.head_sha && (
                <DetailRow label="Commit">
                  <span className="font-mono text-[12px] bg-surfaceHighlight border border-border px-1.5 py-0.5 rounded">
                    {prData.head_sha.substring(0, 7)}
                  </span>
                </DetailRow>
              )}
            </div>
          </SectionCard>
        </div>
      </div>

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
