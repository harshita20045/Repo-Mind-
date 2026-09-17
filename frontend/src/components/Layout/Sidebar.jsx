import React from 'react';
import { NavLink } from 'react-router-dom';

import { authApi } from '../../lib/api';

const Sidebar = ({ user, memberships, onLogout }) => {
  
  // Basic RBAC navigation items
  const navItems = [
    { name: 'Dashboard', path: '/', roles: ['org_owner', 'org_admin', 'eng_manager', 'tech_lead', 'security_reviewer', 'reviewer', 'developer', 'read_only'] },
    { name: 'Repositories', path: '/repositories', roles: ['org_owner', 'org_admin', 'eng_manager', 'tech_lead', 'developer', 'reviewer'] },
    { name: 'Security', path: '/security', roles: ['org_owner', 'security_reviewer'] },
    { name: 'Analytics', path: '/analytics', roles: ['org_owner', 'org_admin', 'eng_manager'] },
    { name: 'Chat', path: '/chat', roles: ['org_owner', 'org_admin', 'eng_manager', 'tech_lead', 'security_reviewer', 'reviewer', 'developer'] },
    { name: 'Settings', path: '/settings', roles: ['org_owner', 'org_admin'] },
  ];
  
  // Real user role from memberships, default to least privilege
  const role = memberships?.[0]?.role || 'read_only';
  
  const filteredNav = navItems.filter(item => item.roles.includes(role));

  const handleLogoutClick = async () => {
    try {
      await authApi.logout();
    } catch (e) {
      console.error('Logout API failed', e);
    } finally {
      if (onLogout) onLogout();
    }
  };

  return (
    <aside className="w-64 bg-surface/50 backdrop-blur-xl border-r border-white/5 flex flex-col h-full transition-all duration-300">
      <div className="p-6 flex items-center gap-3">
        <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-primary to-accent flex items-center justify-center shadow-lg shadow-primary/20">
          <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-white/70">
          RepoMind
        </h1>
      </div>
      
      <nav className="flex-1 px-4 space-y-1 overflow-y-auto mt-4">
        {filteredNav.map((item) => (
          <NavLink
            key={item.name}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group ${
                isActive
                  ? 'bg-[var(--color-primary-teal)]/10 text-[var(--color-primary-teal)] shadow-sm ring-1 ring-[var(--color-primary-teal)]/20'
                  : 'text-gray-400 hover:bg-white/5 hover:text-white'
              }`
            }
          >
            <span className="font-medium text-sm">{item.name}</span>
          </NavLink>
        ))}
      </nav>
      
      <div className="p-4 border-t border-white/5 space-y-3">
        <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-surfaceHighlight/50 border border-white/5">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-700 to-gray-900 flex items-center justify-center border border-white/10">
            <span className="text-xs font-medium text-white">{user?.email?.charAt(0).toUpperCase() || 'U'}</span>
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-medium text-white truncate max-w-[120px]">{user?.email || 'User'}</span>
            <span className="text-xs text-primary/80 capitalize">{role.replace('_', ' ')}</span>
          </div>
        </div>
        
        <button 
          onClick={handleLogoutClick}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm text-gray-400 hover:text-danger hover:bg-danger/10 rounded-lg transition-colors border border-transparent hover:border-danger/20"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          Logout
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
