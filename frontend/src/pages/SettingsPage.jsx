import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import MemberManagement from '../components/MemberManagement';

// ─── Form helpers ─────────────────────────────────────────────────────────────
function SettingField({ label, hint, children }) {
  return (
    <div>
      <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">{label}</label>
      {children}
      {hint && <p className="text-xs text-text-muted mt-1">{hint}</p>}
    </div>
  );
}

function TextInput({ value, onChange, disabled, placeholder, type = 'text', readOnly, className = '' }) {
  return (
    <input
      type={type}
      value={value}
      onChange={onChange}
      disabled={disabled}
      placeholder={placeholder}
      readOnly={readOnly}
      className={`w-full bg-surfaceHighlight/40 border border-white/[0.09] text-sm rounded-lg px-3.5 py-2.5 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary/40 placeholder-text-muted transition-all
        ${disabled || readOnly ? 'text-text-muted cursor-not-allowed opacity-60' : 'text-text-primary'}
        ${className}`}
    />
  );
}

// ─── Settings tab nav ──────────────────────────────────────────────────────────
const TABS = [
  { id: 'profile', label: 'My Profile', icon: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
    </svg>
  )},
  { id: 'organization', label: 'Organization', icon: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
    </svg>
  )},
  { id: 'members', label: 'Team Members', icon: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
    </svg>
  )},
  { id: 'integrations', label: 'GitHub Integration', icon: (
    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
      <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.161 22 16.418 22 12c0-5.523-4.477-10-10-10z" />
    </svg>
  )},
  { id: 'billing', label: 'Billing & Plans', icon: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
    </svg>
  )},
];

// ─── Settings Page ────────────────────────────────────────────────────────────
export default function SettingsPage() {
  const { user, memberships } = useOutletContext();
  const [activeTab, setActiveTab] = useState('profile');

  const orgId = memberships?.[0]?.organization_id;
  const orgName = memberships?.[0]?.organization?.name || 'My Organization';

  return (
    <div className="space-y-5 animate-slide-up">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary tracking-tight">Settings</h1>
        <p className="text-sm text-text-muted mt-1">Manage your profile, organization, and integrations.</p>
      </div>

      {/* Two-col layout */}
      <div className="flex flex-col lg:flex-row gap-5">

        {/* Sidebar tabs */}
        <div className="lg:w-56 flex-shrink-0">
          <nav className="bg-surface border border-white/[0.07] rounded-xl p-2 space-y-0.5" role="navigation" aria-label="Settings sections">
            {TABS.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                role="tab"
                aria-selected={activeTab === tab.id}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                  activeTab === tab.id
                    ? 'bg-primary/10 text-primary'
                    : 'text-text-muted hover:text-text-primary hover:bg-white/[0.05]'
                }`}
              >
                <span className={`flex-shrink-0 ${activeTab === tab.id ? 'text-primary' : 'text-text-muted'}`}>
                  {tab.icon}
                </span>
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">

          {/* Profile */}
          {activeTab === 'profile' && (
            <div className="bg-surface border border-white/[0.07] rounded-xl p-6 space-y-6">
              <div>
                <h2 className="text-base font-bold text-text-primary mb-0.5">Profile Settings</h2>
                <p className="text-xs text-text-muted">Manage your personal account details.</p>
              </div>

              <div className="flex items-center gap-5 pb-5 border-b border-white/[0.06]">
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary/40 to-accent/40 border border-white/10 flex items-center justify-center text-2xl font-bold text-white flex-shrink-0">
                  {user?.email?.charAt(0).toUpperCase() || 'U'}
                </div>
                <div>
                  <p className="text-sm font-semibold text-text-primary">{user?.email}</p>
                  <p className="text-xs text-text-muted mt-0.5">
                    Member since account creation
                  </p>
                </div>
              </div>

              <div className="space-y-4 max-w-md">
                <SettingField label="Email Address" hint="Email cannot be changed. Contact support if needed.">
                  <TextInput value={user?.email || ''} disabled />
                </SettingField>
                <SettingField label="Full Name">
                  <TextInput placeholder="e.g. Jane Doe" />
                </SettingField>
                <div className="pt-2">
                  <button className="px-5 py-2 bg-primary hover:bg-primary-hover text-white text-sm font-semibold rounded-lg transition-all shadow-sm shadow-primary/20 border border-white/10">
                    Save Changes
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Organization */}
          {activeTab === 'organization' && (
            <div className="bg-surface border border-white/[0.07] rounded-xl p-6 space-y-6">
              <div>
                <h2 className="text-base font-bold text-text-primary mb-0.5">Organization Settings</h2>
                <p className="text-xs text-text-muted">Details about your engineering organization.</p>
              </div>
              <div className="space-y-4 max-w-md">
                <SettingField label="Organization Name">
                  <TextInput defaultValue={orgName} />
                </SettingField>
                <SettingField label="Organization ID" hint="Read-only identifier used for API access.">
                  <TextInput value={String(orgId || '—')} readOnly />
                </SettingField>
                <div className="pt-2">
                  <button className="px-5 py-2 bg-primary hover:bg-primary-hover text-white text-sm font-semibold rounded-lg transition-all shadow-sm shadow-primary/20 border border-white/10">
                    Update Organization
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Members */}
          {activeTab === 'members' && (
            <div className="bg-surface border border-white/[0.07] rounded-xl overflow-hidden">
              <MemberManagement organizationId={orgId} memberships={memberships || []} />
            </div>
          )}

          {/* Integrations */}
          {activeTab === 'integrations' && (
            <div className="bg-surface border border-white/[0.07] rounded-xl p-6 space-y-6">
              <div>
                <h2 className="text-base font-bold text-text-primary mb-0.5">GitHub Integration</h2>
                <p className="text-xs text-text-muted">RepoMind uses Personal Access Tokens per repository for a secure, zero-OAuth setup.</p>
              </div>

              {/* Connection status */}
              <div className="flex items-center justify-between p-4 bg-surfaceHighlight/30 border border-white/[0.08] rounded-xl">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center flex-shrink-0">
                    <svg className="w-6 h-6 text-black" fill="currentColor" viewBox="0 0 24 24">
                      <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.161 22 16.418 22 12c0-5.523-4.477-10-10-10z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-text-primary">GitHub (PAT-based)</p>
                    <p className="text-xs text-text-muted mt-0.5">Repositories connected via per-repo Personal Access Tokens</p>
                  </div>
                </div>
                <span className="text-xs font-bold text-success bg-success/10 border border-success/20 px-2.5 py-1 rounded-full">Active</span>
              </div>

              {/* Webhook info */}
              <div>
                <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">Webhook Configuration</h3>
                <div className="space-y-3 max-w-lg">
                  <SettingField label="Payload URL" hint="Add this URL to your GitHub repository webhooks.">
                    <div className="flex">
                      <input
                        type="text"
                        readOnly
                        value={`${window.location.protocol}//${window.location.host.replace('5173','8000').replace('3000','8000')}/api/webhooks/github`}
                        className="flex-1 bg-surfaceHighlight/30 border border-white/[0.09] text-text-muted text-xs font-mono rounded-l-lg px-3.5 py-2.5 focus:outline-none"
                      />
                      <button
                        onClick={() => navigator.clipboard.writeText(`${window.location.protocol}//${window.location.host}/api/webhooks/github`)}
                        className="px-3.5 bg-surfaceHighlight/60 hover:bg-surfaceElevated border-y border-r border-white/[0.09] text-text-secondary rounded-r-lg text-xs font-medium transition-colors"
                      >
                        Copy
                      </button>
                    </div>
                  </SettingField>
                  <SettingField label="Content Type" hint="Must match your webhook configuration.">
                    <TextInput value="application/json" readOnly />
                  </SettingField>
                </div>
              </div>
            </div>
          )}

          {/* Billing */}
          {activeTab === 'billing' && (
            <div className="bg-surface border border-white/[0.07] rounded-xl p-12 text-center">
              <div className="w-14 h-14 rounded-2xl bg-surfaceHighlight/60 border border-white/[0.08] flex items-center justify-center text-text-muted mx-auto mb-5">
                <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                </svg>
              </div>
              <h2 className="text-base font-bold text-text-primary mb-2">Enterprise Billing</h2>
              <p className="text-sm text-text-muted max-w-xs mx-auto">
                Billing management is available on the RepoMind Enterprise tier. Contact your account manager to get started.
              </p>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
