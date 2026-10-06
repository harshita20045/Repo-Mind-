import React, { useState, useEffect } from 'react';
import Modal from '../../components/ui/Modal';
import { Button } from '../../components/ui/Button';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { githubApi } from '../../lib/api';

export default function MergePolicyModal({ isOpen, onClose, repoId, repoName }) {
  const queryClient = useQueryClient();
  const [errorMsg, setErrorMsg] = useState(null);

  const { data: policy, isLoading } = useQuery({
    queryKey: ['mergePolicy', repoId],
    queryFn: () => githubApi.getMergePolicy(repoId),
    enabled: !!repoId && isOpen,
  });

  const [formData, setFormData] = useState({
    require_human_approval: 1,
    required_approvals: 1,
    require_ai_analysis: 1,
    require_ci_success: 1,
    auto_merge_enabled: 0,
    approval_validity: 'LATEST_COMMIT_ONLY',
    require_latest_commit_review: 1,
  });

  useEffect(() => {
    if (policy) {
      setFormData(policy);
    }
  }, [policy]);

  const updateMutation = useMutation({
    mutationFn: (data) => githubApi.updateMergePolicy(repoId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mergePolicy', repoId] });
      onClose();
    },
    onError: (err) => setErrorMsg(err.message),
  });

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleToggle = (field) => {
    setFormData(prev => ({ ...prev, [field]: prev[field] === 1 ? 0 : 1 }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    updateMutation.mutate(formData);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Merge Policies for ${repoName || 'Repository'}`}
      subtitle="Configure strict gating rules before a Pull Request can be merged."
      size="md"
    >
      {isLoading ? (
        <div className="flex justify-center p-8">
          <svg className="animate-spin w-6 h-6 text-primary" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
            <path className="opacity-80" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-5">
          {errorMsg && (
            <div className="p-3 bg-danger/10 border border-danger/20 text-danger text-sm rounded-lg">
              {errorMsg}
            </div>
          )}

          <div className="space-y-4">
            <label className="flex items-start gap-3 cursor-pointer group">
              <div className="mt-0.5 relative flex items-center justify-center">
                <input
                  type="checkbox"
                  className="peer appearance-none w-4 h-4 rounded border border-border bg-surfaceHighlight checked:bg-primary checked:border-primary transition-colors cursor-pointer"
                  checked={formData.require_human_approval === 1}
                  onChange={() => handleToggle('require_human_approval')}
                />
                <svg className="absolute w-3 h-3 text-white opacity-0 peer-checked:opacity-100 pointer-events-none" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </div>
              <div className="flex-1">
                <div className="text-[13px] font-semibold text-text-primary group-hover:text-primary transition-colors">Require Human Approval</div>
                <div className="text-[12px] text-text-muted mt-0.5">At least one approved review from an organization member is required before merging.</div>
              </div>
            </label>

            <label className="flex items-start gap-3 cursor-pointer group">
              <div className="mt-0.5 relative flex items-center justify-center">
                <input
                  type="checkbox"
                  className="peer appearance-none w-4 h-4 rounded border border-border bg-surfaceHighlight checked:bg-primary checked:border-primary transition-colors cursor-pointer"
                  checked={formData.require_ai_analysis === 1}
                  onChange={() => handleToggle('require_ai_analysis')}
                />
                <svg className="absolute w-3 h-3 text-white opacity-0 peer-checked:opacity-100 pointer-events-none" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </div>
              <div className="flex-1">
                <div className="text-[13px] font-semibold text-text-primary group-hover:text-primary transition-colors">Require AI Review</div>
                <div className="text-[12px] text-text-muted mt-0.5">RepoMind must complete its analysis and find no unaddressed Critical/High risk findings.</div>
              </div>
            </label>

            <label className="flex items-start gap-3 cursor-pointer group">
              <div className="mt-0.5 relative flex items-center justify-center">
                <input
                  type="checkbox"
                  className="peer appearance-none w-4 h-4 rounded border border-border bg-surfaceHighlight checked:bg-primary checked:border-primary transition-colors cursor-pointer"
                  checked={formData.require_ci_success === 1}
                  onChange={() => handleToggle('require_ci_success')}
                />
                <svg className="absolute w-3 h-3 text-white opacity-0 peer-checked:opacity-100 pointer-events-none" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </div>
              <div className="flex-1">
                <div className="text-[13px] font-semibold text-text-primary group-hover:text-primary transition-colors">Require CI Success</div>
                <div className="text-[12px] text-text-muted mt-0.5">All GitHub Check Runs must pass successfully before merging.</div>
              </div>
            </label>

            <label className="flex items-start gap-3 cursor-pointer group">
              <div className="mt-0.5 relative flex items-center justify-center">
                <input
                  type="checkbox"
                  className="peer appearance-none w-4 h-4 rounded border border-border bg-surfaceHighlight checked:bg-primary checked:border-primary transition-colors cursor-pointer"
                  checked={formData.require_latest_commit_review === 1}
                  onChange={() => handleToggle('require_latest_commit_review')}
                />
                <svg className="absolute w-3 h-3 text-white opacity-0 peer-checked:opacity-100 pointer-events-none" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </div>
              <div className="flex-1">
                <div className="text-[13px] font-semibold text-text-primary group-hover:text-primary transition-colors">Stale Reviews Enforcement</div>
                <div className="text-[12px] text-text-muted mt-0.5">New commits invalidate previous approvals, requiring a fresh review on the latest code.</div>
              </div>
            </label>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-border">
            <Button variant="ghost" type="button" onClick={onClose} disabled={updateMutation.isPending}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" loading={updateMutation.isPending}>
              Save Policies
            </Button>
          </div>
        </form>
      )}
    </Modal>
  );
}
