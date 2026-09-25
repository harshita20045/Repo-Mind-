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
      <path d="M9 13h6" />
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
      <path d="M12 20V10M18 20V4M6 20v-4" />
    </svg>
  ),
  chat: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
    </svg>
  ),
  settings: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
      <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
      <circle cx="12" cy="12" r="3" />
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
        `group flex items-center gap-3 px-3 py-1.5 rounded-md text-sm font-medium transition-all duration-150 ${
          isActive
            ? 'bg-primary/10 text-primary'
            : 'text-text-muted hover:text-text-primary hover:bg-surfaceHighlight'
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
    <div className="mb-4">
      <p className="px-3 mb-1 text-[11px] font-semibold uppercase tracking-wider text-text-muted/60">
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
    'Org Admin': 'text-primary bg-primary/10 border-primary/20',
    'Lead':      'text-info bg-info/10 border-info/20',
    'Reviewer':  'text-success bg-success/10 border-success/20',
    'Developer': 'text-text-muted bg-white/5 border-white/10',
    'Read Only': 'text-text-muted bg-white/5 border-white/10',
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
      className="w-[240px] flex-shrink-0 flex flex-col h-full bg-background border-r border-border overflow-hidden"
      role="navigation"
      aria-label="Main navigation"
    >
      {/* Logo */}
      <div className="h-14 px-4 flex items-center gap-2.5 border-b border-border flex-shrink-0">
        <div className="w-6 h-6 rounded border border-white/10 bg-surface flex items-center justify-center flex-shrink-0">
          <svg className="w-3.5 h-3.5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <div>
          <span className="text-sm font-semibold text-text-primary tracking-tight leading-none">RepoMind</span>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-3 py-4">
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
              <NavItem to="/security" icon="security" label="Security" />
            )}
          </NavSection>
        )}

        {/* AI */}
        {can(Permissions.CHAT_USE) && (
          <NavSection label="AI">
            <NavItem to="/chat" icon="chat" label="Assistant" />
          </NavSection>
        )}

        {/* Admin */}
        {can(Permissions.ORG_UPDATE) && (
          <NavSection label="Configuration">
            <NavItem to="/settings" icon="settings" label="Settings" />
          </NavSection>
        )}
      </nav>

      {/* User footer */}
      <div className="border-t border-border p-3 flex-shrink-0">
        <div className="flex items-center gap-2.5 px-2 py-2 rounded-md hover:bg-surfaceHighlight transition-colors cursor-pointer group">
          <div className="w-7 h-7 rounded bg-surface border border-white/10 flex items-center justify-center text-xs font-semibold text-text-secondary flex-shrink-0 group-hover:text-text-primary group-hover:border-white/20 transition-all">
            {userInitial}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-text-primary truncate leading-tight">{user?.email || 'User'}</p>
            <span className={`text-[10px] font-medium px-1 rounded border inline-block mt-0.5 ${roleColors[displayRole] || roleColors['Read Only']}`}>
              {displayRole}
            </span>
          </div>
        </div>
        <button
          onClick={handleLogout}
          disabled={isLoggingOut}
          className="mt-2 w-full flex items-center gap-2 px-3 py-1.5 rounded-md text-[13px] font-medium text-text-muted hover:text-text-primary hover:bg-surface transition-all duration-150 disabled:opacity-50"
          aria-label="Sign out"
        >
          <span className="w-3.5 h-3.5 flex-shrink-0">{Icons.logout}</span>
          {isLoggingOut ? 'Signing out…' : 'Sign out'}
        </button>
      </div>
    </aside>
  );
}
