import React, { useEffect, useState } from 'react';
import { usePermissions, Permissions } from '../hooks/usePermissions';
import { apiRequest } from '../lib/api';
import ConfirmDialog from './ui/ConfirmDialog';
import { Button } from './ui/Button';
import { StatusBadge } from './ui/Badge';
import EmptyState from './ui/EmptyState';

const ROLES = ['developer', 'reviewer', 'tech_lead', 'org_admin'];
const ROLE_LABELS = { developer: 'Developer', reviewer: 'Reviewer', tech_lead: 'Lead', org_admin: 'Org Admin' };

export default function MemberManagement({ organizationId, memberships }) {
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('developer');
  const [inviteLoading, setInviteLoading] = useState(false);
  const [error, setError] = useState(null);
  const [removeTarget, setRemoveTarget] = useState(null); // { id, email }
  const [removeLoading, setRemoveLoading] = useState(false);

  const { can } = usePermissions(memberships, organizationId);
  const isAdmin = can(Permissions.MEMBERS_UPDATE);

  useEffect(() => { fetchMembers(); }, [organizationId]);

  async function fetchMembers() {
    if (!organizationId) return;
    setLoading(true);
    try {
      const data = await apiRequest(`/organizations/${organizationId}/members`);
      setMembers(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function handleInvite(e) {
    e.preventDefault();
    setError(null);
    if (!organizationId) return;
    setInviteLoading(true);
    try {
      await apiRequest(`/organizations/${organizationId}/members`, {
        method: 'POST',
        body: JSON.stringify({ email: inviteEmail, role: inviteRole }),
      });
      setInviteEmail('');
      fetchMembers();
    } catch (e) {
      setError(e.message || 'Failed to add member.');
    } finally {
      setInviteLoading(false);
    }
  }

  async function handleUpdateRole(userId, newRole) {
    if (!organizationId) return;
    try {
      await apiRequest(`/organizations/${organizationId}/members/${userId}/role`, {
        method: 'PUT',
        body: JSON.stringify({ role: newRole }),
      });
      fetchMembers();
    } catch (e) {
      setError(e.message || 'Failed to update role.');
    }
  }

  async function handleRemoveConfirmed() {
    if (!removeTarget) return;
    setRemoveLoading(true);
    try {
      await apiRequest(`/organizations/${organizationId}/members/${removeTarget.id}`, {
        method: 'DELETE',
      });
      fetchMembers();
    } catch (e) {
      setError(e.message || 'Failed to remove member.');
    } finally {
      setRemoveLoading(false);
      setRemoveTarget(null);
    }
  }

  // ─── Read-only view (non-admin) ─────────────────────────────────────────────
  if (!isAdmin) {
    return (
      <div className="p-6">
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-text-primary">Organization Members</h3>
          <p className="text-xs text-text-muted mt-0.5">Your team's membership in this organization.</p>
        </div>
        {loading ? (
          <div className="space-y-2">
            {[0,1,2].map(i => (
              <div key={i} className="flex items-center justify-between p-3 bg-surfaceHighlight/30 border border-white/[0.07] rounded-lg">
                <div className="skeleton h-4 w-40 rounded" />
                <div className="skeleton h-5 w-16 rounded-full" />
              </div>
            ))}
          </div>
        ) : members.length === 0 ? (
          <EmptyState title="No members yet" description="No members found in this organization." className="py-8" />
        ) : (
          <div className="space-y-1.5">
            {members.map(m => (
              <div key={m.id} className="flex items-center justify-between p-3 bg-surfaceHighlight/20 border border-white/[0.07] rounded-lg hover:bg-surfaceHighlight/30 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="w-7 h-7 rounded-full bg-gradient-to-br from-primary/30 to-accent/30 border border-white/10 flex items-center justify-center text-xs font-bold text-white">
                    {m.email?.charAt(0).toUpperCase()}
                  </div>
                  <span className="text-sm text-text-secondary">{m.email}</span>
                </div>
                <StatusBadge status={m.role} label={ROLE_LABELS[m.role] || m.role} />
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // ─── Admin view ────────────────────────────────────────────────────────────
  return (
    <>
      <div className="p-6">
        {/* Header */}
        <div className="mb-5">
          <h3 className="text-sm font-semibold text-text-primary">Manage Team Members</h3>
          <p className="text-xs text-text-muted mt-0.5">Invite new members and manage existing roles.</p>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 flex items-center gap-2.5 p-3 bg-danger/8 border border-danger/20 text-danger text-sm rounded-lg" role="alert">
            <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {error}
            <button onClick={() => setError(null)} className="ml-auto text-danger/60 hover:text-danger">×</button>
          </div>
        )}

        {/* Invite form */}
        <form onSubmit={handleInvite} className="flex gap-2 mb-6 flex-wrap">
          <input
            type="email"
            value={inviteEmail}
            onChange={e => setInviteEmail(e.target.value)}
            placeholder="member@company.com"
            required
            className="flex-1 min-w-[180px] bg-surfaceHighlight/40 border border-white/[0.09] text-text-primary text-sm rounded-lg px-3.5 py-2 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary/40 placeholder-text-muted transition-all"
          />
          <select
            value={inviteRole}
            onChange={e => setInviteRole(e.target.value)}
            className="bg-surfaceHighlight/40 border border-white/[0.09] text-text-primary text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all"
          >
            {ROLES.map(r => (
              <option key={r} value={r}>{ROLE_LABELS[r]}</option>
            ))}
          </select>
          <Button type="submit" variant="primary" size="sm" loading={inviteLoading} disabled={!inviteEmail.trim()}>
            Add Member
          </Button>
        </form>

        {/* Members list */}
        {loading ? (
          <div className="space-y-1.5">
            {[0,1,2,3].map(i => (
              <div key={i} className="flex items-center justify-between p-3 bg-surfaceHighlight/30 border border-white/[0.07] rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="skeleton w-7 h-7 rounded-full" />
                  <div className="skeleton h-4 w-40 rounded" />
                </div>
                <div className="flex gap-2">
                  <div className="skeleton h-8 w-28 rounded-lg" />
                  <div className="skeleton h-8 w-16 rounded-lg" />
                </div>
              </div>
            ))}
          </div>
        ) : members.length === 0 ? (
          <EmptyState title="No members yet" description="Add members to your organization above." icon="default" className="py-10" />
        ) : (
          <div className="space-y-1.5">
            {members.map(m => (
              <div key={m.id} className="flex items-center justify-between p-3 bg-surfaceHighlight/20 border border-white/[0.07] rounded-lg hover:bg-surfaceHighlight/30 transition-colors gap-3">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-7 h-7 rounded-full bg-gradient-to-br from-primary/30 to-accent/30 border border-white/10 flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
                    {m.email?.charAt(0).toUpperCase()}
                  </div>
                  <span className="text-sm text-text-secondary truncate">{m.email}</span>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <select
                    value={m.role}
                    onChange={e => handleUpdateRole(m.user_id, e.target.value)}
                    className="bg-surfaceHighlight/60 border border-white/[0.09] text-text-secondary text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all"
                  >
                    {ROLES.map(r => (
                      <option key={r} value={r}>{ROLE_LABELS[r]}</option>
                    ))}
                  </select>
                  <Button
                    variant="danger"
                    size="xs"
                    onClick={() => setRemoveTarget({ id: m.user_id, email: m.email })}
                    aria-label={`Remove ${m.email}`}
                  >
                    Remove
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Confirm remove dialog */}
      <ConfirmDialog
        isOpen={!!removeTarget}
        onClose={() => setRemoveTarget(null)}
        onConfirm={handleRemoveConfirmed}
        isLoading={removeLoading}
        title="Remove Member"
        description={`Are you sure you want to remove ${removeTarget?.email} from the organization? This action cannot be undone.`}
        confirmLabel="Remove Member"
        cancelLabel="Cancel"
        variant="danger"
      />
    </>
  );
}
