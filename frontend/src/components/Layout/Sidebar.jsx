import React from 'react';
import { NavLink } from 'react-router-dom';

const Sidebar = ({ user }) => {
  
  // Basic RBAC navigation items
  const navItems = [
    { name: 'Dashboard', path: '/', roles: ['org_owner', 'org_admin', 'eng_manager', 'tech_lead', 'security_reviewer', 'reviewer', 'developer', 'read_only'] },
    { name: 'Repositories', path: '/repositories', roles: ['org_owner', 'org_admin', 'eng_manager', 'tech_lead'] },
    { name: 'My PRs', path: '/prs', roles: ['developer', 'reviewer', 'tech_lead'] },
    { name: 'Security', path: '/security', roles: ['org_owner', 'security_reviewer'] },
    { name: 'Analytics', path: '/analytics', roles: ['org_owner', 'org_admin', 'eng_manager'] },
    { name: 'Settings', path: '/settings', roles: ['org_owner', 'org_admin'] },
  ];
  
  // Fake user role for UI preview if auth not fully loaded
  const role = user?.role || 'org_owner'; 
  
  const filteredNav = navItems.filter(item => item.roles.includes(role));

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
                  ? 'bg-primary/10 text-primary shadow-sm ring-1 ring-primary/20' 
                  : 'text-gray-400 hover:bg-white/5 hover:text-white'
              }`
            }
          >
            <span className="font-medium text-sm">{item.name}</span>
          </NavLink>
        ))}
      </nav>
      
      <div className="p-4 border-t border-white/5">
        <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-surfaceHighlight/50 border border-white/5">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-700 to-gray-900 flex items-center justify-center border border-white/10">
            <span className="text-xs font-medium text-white">{user?.email?.charAt(0).toUpperCase() || 'U'}</span>
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-medium text-white truncate max-w-[120px]">{user?.email || 'User'}</span>
            <span className="text-xs text-primary/80 capitalize">{role.replace('_', ' ')}</span>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
