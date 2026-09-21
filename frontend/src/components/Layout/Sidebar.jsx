import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { authApi } from '../../lib/api';
import { usePermissions, Permissions } from '../../hooks/usePermissions';

// ─── Nav item icon map ─────────────────────────────────────────────────────────
const Icons = {
  dashboard: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </svg>
  ),
  repositories: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
    </svg>
  ),
  pullRequests: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
      <circle cx="6" cy="6" r="3" />
      <circle cx="6" cy="18" r="3" />
      <path d="M6 9v6M13 6h3a2 2 0 012 2v7a2 2 0 01-2 2h-3" />
      <circle cx="18" cy="6" r="3" />
    </svg>
  ),
  security: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  ),
  analytics: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 19V9m4 10V5m4 14v-7" />
      <rect x="3" y="3" width="18" height="18" rx="2" />
    </svg>
  ),
  chat: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
    </svg>
  ),
  settings: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />
    </svg>
  ),
  logout: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" />
    </svg>
  ),
};

// ─── Sidebar Nav Item ──────────────────────────────────────────────────────────
function NavItem({ to, icon, label, end = false }) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        `group flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
          isActive
            ? 'bg-primary/10 text-primary'
            : 'text-text-muted hover:text-text-primary hover:bg-white/[0.05]'
        }`
      }
    >
      {({ isActive }) => (
        <>
          <span className={`w-4 h-4 flex-shrink-0 transition-colors ${isActive ? 'text-primary' : 'text-text-muted group-hover:text-text-secondary'}`}>
            {Icons[icon]}
          </span>
          <span className="truncate">{label}</span>
        </>
      )}
    </NavLink>
  );
}

// ─── Sidebar Section ───────────────────────────────────────────────────────────
function NavSection({ label, children }) {
  return (
    <div className="mb-1">
      <p className="px-3 mb-1 text-2xs font-semibold uppercase tracking-widest text-text-muted/60">
        {label}
      </p>
      <div className="space-y-0.5">{children}</div>
    </div>
  );
}

// ─── Main Sidebar ──────────────────────────────────────────────────────────────
export default function Sidebar({ user, memberships, onLogout }) {
  const { can, isOrgAdmin, isLead, isReviewer, isDeveloper } = usePermissions(memberships);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  let displayRole = 'Read Only';
  if (isOrgAdmin) displayRole = 'Org Admin';
  else if (isLead) displayRole = 'Lead';
  else if (isReviewer) displayRole = 'Reviewer';
  else if (isDeveloper) displayRole = 'Developer';

  const roleColors = {
    'Org Admin': 'text-accent bg-accent/10',
    'Lead':      'text-primary bg-primary/10',
    'Reviewer':  'text-info bg-info/10',
    'Developer': 'text-text-muted bg-white/5',
    'Read Only': 'text-text-muted bg-white/5',
  };

  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
      await authApi.logout();
    } catch (e) {
      console.error('Logout API failed', e);
    } finally {
      if (onLogout) onLogout();
      setIsLoggingOut(false);
    }
  };

  const userInitial = user?.email?.charAt(0).toUpperCase() || 'U';

  return (
    <aside
      className="w-60 flex-shrink-0 flex flex-col h-full bg-surface border-r border-white/[0.07] overflow-hidden"
      role="navigation"
      aria-label="Main navigation"
    >
      {/* Logo */}
      <div className="px-5 py-5 flex items-center gap-3 border-b border-white/[0.07]">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center flex-shrink-0 shadow-glow-primary">
          <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <div>
          <span className="text-sm font-bold text-text-primary tracking-tight">RepoMind</span>
          <p className="text-2xs text-text-muted leading-none mt-0.5">Engineering Intelligence</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-5">
        {/* Workspace */}
        <NavSection label="Workspace">
          <NavItem to="/" icon="dashboard" label="Dashboard" end />
          {can(Permissions.REPOS_READ) && (
            <NavItem to="/repositories" icon="repositories" label="Repositories" />
          )}
        </NavSection>

        {/* Intelligence */}
        {can(Permissions.ANALYTICS_READ) && (
          <NavSection label="Intelligence">
            <NavItem to="/analytics" icon="analytics" label="Engineering Intel" />
            {can(Permissions.SECURITY_READ) && (
              <NavItem to="/security" icon="security" label="Security Browser" />
            )}
          </NavSection>
        )}

        {/* AI */}
        {can(Permissions.CHAT_USE) && (
          <NavSection label="AI">
            <NavItem to="/chat" icon="chat" label="Developer Assistant" />
          </NavSection>
        )}

        {/* Admin */}
        {can(Permissions.ORG_UPDATE) && (
          <NavSection label="Administration">
            <NavItem to="/settings" icon="settings" label="Settings" />
          </NavSection>
        )}
      </nav>

      {/* User footer */}
      <div className="border-t border-white/[0.07] p-3">
        <div className="flex items-center gap-3 px-2 py-2.5 rounded-lg">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary/40 to-accent/40 border border-white/10 flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
            {userInitial}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-text-primary truncate">{user?.email || 'User'}</p>
            <span className={`text-2xs font-semibold px-1.5 py-0.5 rounded ${roleColors[displayRole] || roleColors['Read Only']}`}>
              {displayRole}
            </span>
          </div>
        </div>
        <button
          onClick={handleLogout}
          disabled={isLoggingOut}
          className="mt-1 w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-text-muted hover:text-danger hover:bg-danger/5 transition-all duration-150 disabled:opacity-50"
          aria-label="Sign out"
        >
          <span className="w-4 h-4 flex-shrink-0">{Icons.logout}</span>
          {isLoggingOut ? 'Signing out…' : 'Sign Out'}
        </button>
      </div>
    </aside>
  );
}
