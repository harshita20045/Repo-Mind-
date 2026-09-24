import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import ThemeToggle from '../ThemeToggle';

// Map route patterns to readable labels
const ROUTE_LABELS = {
  '/':            { label: 'Dashboard',            crumbs: [] },
  '/repositories':{ label: 'Repositories',         crumbs: [] },
  '/analytics':   { label: 'Engineering Intelligence', crumbs: [] },
  '/security':    { label: 'Security Browser',     crumbs: [] },
  '/chat':        { label: 'Developer Assistant',  crumbs: [] },
  '/settings':    { label: 'Settings',             crumbs: [] },
};

function getPageInfo(pathname) {
  // Exact match first
  if (ROUTE_LABELS[pathname]) return ROUTE_LABELS[pathname];

  // Pull-requests detail: /repositories/:rid/pull-requests/:prid
  if (/^\/repositories\/\d+\/pull-requests\/\d+$/.test(pathname)) {
    const parts = pathname.split('/');
    return {
      label: `PR #${parts[4]}`,
      crumbs: [
        { label: 'Repositories', to: '/repositories' },
        { label: 'Pull Requests', to: `/repositories/${parts[2]}/pull-requests` },
      ],
    };
  }

  // Pull-requests list: /repositories/:rid/pull-requests
  if (/^\/repositories\/\d+\/pull-requests$/.test(pathname)) {
    return {
      label: 'Pull Requests',
      crumbs: [{ label: 'Repositories', to: '/repositories' }],
    };
  }

  return { label: 'RepoMind', crumbs: [] };
}

export default function TopNav({ user }) {
  const { pathname } = useLocation();
  const { label, crumbs } = getPageInfo(pathname);

  return (
    <header
      className="h-14 flex-shrink-0 flex items-center justify-between px-6 bg-background/80 backdrop-blur-md border-b border-white/[0.07] sticky top-0 z-20"
      role="banner"
    >
      {/* Left: breadcrumbs + page title */}
      <div className="flex items-center gap-2 min-w-0">
        {crumbs.length > 0 && (
          <>
            {crumbs.map((crumb, i) => (
              <React.Fragment key={i}>
                <Link
                  to={crumb.to}
                  className="text-sm text-text-muted hover:text-text-secondary transition-colors truncate"
                >
                  {crumb.label}
                </Link>
                <svg className="w-3.5 h-3.5 text-text-muted/40 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </React.Fragment>
            ))}
          </>
        )}
        <h1 className="text-sm font-semibold text-text-primary truncate">{label}</h1>
      </div>

      {/* Right: user info */}
      <div className="flex items-center gap-3 flex-shrink-0">
        <ThemeToggle />
        {/* Status dot */}
        <div
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-success/10 border border-success/20"
          title="API connected"
          aria-label="System status: connected"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" aria-hidden="true" />
          <span className="text-2xs font-semibold text-success">Live</span>
        </div>

        {/* User avatar */}
        {user && (
          <div
            className="w-7 h-7 rounded-full bg-gradient-to-br from-primary/40 to-accent/40 border border-white/10 flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
            aria-label={`Signed in as ${user.email}`}
            title={user.email}
          >
            {user.email?.charAt(0).toUpperCase() || 'U'}
          </div>
        )}
      </div>
    </header>
  );
}
