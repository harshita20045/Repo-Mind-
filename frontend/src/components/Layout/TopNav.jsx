import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import ThemeToggle from '../ThemeToggle';

const ROUTE_LABELS = {
  '/':            { label: 'Dashboard',            crumbs: [] },
  '/repositories':{ label: 'Repositories',         crumbs: [] },
  '/analytics':   { label: 'Engineering Intelligence', crumbs: [] },
  '/security':    { label: 'Security',             crumbs: [] },
  '/chat':        { label: 'Assistant',            crumbs: [] },
  '/settings':    { label: 'Settings',             crumbs: [] },
};

function getPageInfo(pathname) {
  if (ROUTE_LABELS[pathname]) return ROUTE_LABELS[pathname];

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

  if (/^\/repositories\/\d+\/pull-requests$/.test(pathname)) {
    return {
      label: 'Pull Requests',
      crumbs: [{ label: 'Repositories', to: '/repositories' }],
    };
  }

  return { label: 'RepoMind', crumbs: [] };
}

export default function TopNav({ user, memberships, currentOrgId, setCurrentOrgId }) {
  const { pathname } = useLocation();
  const { label, crumbs } = getPageInfo(pathname);

  const handleOrgChange = (e) => {
    const newOrgId = e.target.value;
    setCurrentOrgId(newOrgId);
    localStorage.setItem('repomind_current_org_id', newOrgId);
    // Force reload to ensure data resets (simplest way to prevent leaks)
    window.location.href = '/';
  };

  return (
    <header
      className="h-14 flex-shrink-0 flex items-center justify-between px-6 bg-background border-b border-border sticky top-0 z-20"
      role="banner"
    >
      {/* Left: breadcrumbs + page title */}
      <div className="flex items-center gap-1.5 min-w-0">
        <div className="w-1.5 h-1.5 rounded-full bg-primary/80 mr-2" />
        
        {/* Organization Switcher */}
        {memberships && memberships.length > 0 && (
          <div className="mr-3 border-r border-border pr-4">
            <select
              value={currentOrgId || ''}
              onChange={handleOrgChange}
              className="bg-transparent text-[13px] font-medium text-text-primary focus:outline-none focus:ring-0 cursor-pointer hover:text-primary transition-colors appearance-none"
              style={{ paddingRight: '16px', background: 'url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 20 20\' fill=\'currentColor\'%3E%3Cpath fill-rule=\'evenodd\' d=\'M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z\' clip-rule=\'evenodd\' /%3E%3C/svg%3E") no-repeat right center / 16px' }}
            >
              {memberships.map((m) => (
                <option key={m.organization.id} value={m.organization.id} className="bg-surface">
                  {m.organization.name}
                </option>
              ))}
            </select>
          </div>
        )}

        {crumbs.length > 0 && (
          <>
            {crumbs.map((crumb, i) => (
              <React.Fragment key={i}>
                <Link
                  to={crumb.to}
                  className="text-[13px] text-text-muted hover:text-text-primary transition-colors truncate"
                >
                  {crumb.label}
                </Link>
                <span className="text-text-muted/30 mx-1">/</span>
              </React.Fragment>
            ))}
          </>
        )}
        <h1 className="text-[13px] font-medium text-text-primary truncate">{label}</h1>
      </div>

      {/* Right: tools */}
      <div className="flex items-center gap-4 flex-shrink-0">
        <ThemeToggle />
        
        <div
          className="flex items-center gap-2 pl-3 border-l border-border"
          title="API connected"
          aria-label="System status: connected"
        >
          <div className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-success"></span>
          </div>
          <span className="text-[11px] font-medium text-text-muted uppercase tracking-wider">Connected</span>
        </div>
      </div>
    </header>
  );
}
