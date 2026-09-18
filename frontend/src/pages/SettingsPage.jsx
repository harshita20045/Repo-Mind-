import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import MemberManagement from '../components/MemberManagement';

export default function SettingsPage() {
  const { user, memberships } = useOutletContext();
  const [activeTab, setActiveTab] = useState('profile');

  const tabs = [
    { id: 'profile', label: 'My Profile' },
    { id: 'organization', label: 'Organization' },
    { id: 'members', label: 'Team Members' },
    { id: 'integrations', label: 'Integrations' },
    { id: 'billing', label: 'Billing & Plans' }
  ];

  return (
    <div className="space-y-6 animate-slide-up">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Settings</h1>
        <p className="text-gray-400 text-sm">Manage your personal preferences, organization details, and integrations.</p>
      </div>

      <div className="flex flex-col md:flex-row gap-8">
        
        {/* Settings Navigation */}
        <div className="w-full md:w-64 flex-shrink-0 space-y-1">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full text-left px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                activeTab === tab.id 
                  ? 'bg-primary/10 text-primary border border-primary/20'
                  : 'text-gray-400 hover:bg-white/5 hover:text-gray-200 border border-transparent'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Settings Content Area */}
        <div className="flex-1 space-y-6">
          
          {activeTab === 'profile' && (
            <div className="bg-surface/50 backdrop-blur-md border border-white/5 rounded-2xl p-6">
              <h2 className="text-xl font-bold text-white mb-6">Profile Settings</h2>
              
              <div className="flex items-center gap-6 mb-8">
                <div className="w-20 h-20 rounded-full bg-gradient-to-tr from-accent to-primary flex items-center justify-center text-2xl font-bold text-white shadow-lg">
                  {user?.email ? user.email.charAt(0).toUpperCase() : 'U'}
                </div>
                <div>
                  <button className="px-4 py-2 bg-surfaceHighlight hover:bg-surfaceHighlight/80 text-white rounded-lg text-sm font-medium transition-colors border border-white/10">
                    Upload Avatar
                  </button>
                  <p className="text-xs text-gray-500 mt-2">JPG, GIF or PNG. Max size of 800K</p>
                </div>
              </div>

              <div className="space-y-5 max-w-lg">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1.5">Email Address</label>
                  <input 
                    type="email" 
                    disabled 
                    value={user?.email || ''} 
                    className="w-full bg-surfaceHighlight/20 border border-white/10 text-gray-500 text-sm rounded-lg px-4 py-2 cursor-not-allowed"
                  />
                  <p className="text-xs text-gray-500 mt-1.5">Email cannot be changed directly.</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1.5">Full Name</label>
                  <input 
                    type="text" 
                    placeholder="e.g. Jane Doe" 
                    className="w-full bg-surfaceHighlight/30 border border-white/10 text-gray-200 text-sm rounded-lg px-4 py-2 focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all"
                  />
                </div>
                
                <div className="pt-4 border-t border-white/5">
                  <button className="px-5 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg font-medium transition-colors border border-white/10 shadow-lg shadow-primary/20">
                    Save Changes
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'organization' && (
            <div className="bg-surface/50 backdrop-blur-md border border-white/5 rounded-2xl p-6">
              <h2 className="text-xl font-bold text-white mb-6">Organization Settings</h2>
              <div className="space-y-5 max-w-lg">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1.5">Organization Name</label>
                  <input 
                    type="text" 
                    defaultValue={memberships?.[0]?.organization?.name || 'My Organization'}
                    className="w-full bg-surfaceHighlight/30 border border-white/10 text-gray-200 text-sm rounded-lg px-4 py-2 focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all"
                  />
                </div>
                <div className="pt-4 border-t border-white/5">
                  <button className="px-5 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg font-medium transition-colors border border-white/10 shadow-lg shadow-primary/20">
                    Update Organization
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'integrations' && (
            <div className="bg-surface/50 backdrop-blur-md border border-white/5 rounded-2xl p-6">
              <h2 className="text-xl font-bold text-white mb-6">GitHub Integration</h2>
              
              <div className="flex items-center justify-between p-4 border border-white/10 rounded-xl bg-surfaceHighlight/20 mb-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center">
                    <svg className="w-8 h-8 text-black" fill="currentColor" viewBox="0 0 24 24">
                      <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.161 22 16.418 22 12c0-5.523-4.477-10-10-10z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-white font-medium">GitHub Application</h3>
                    <p className="text-sm text-gray-400">Connected to 4 repositories</p>
                  </div>
                </div>
                <button className="px-4 py-2 border border-danger/30 text-danger hover:bg-danger/10 rounded-lg text-sm font-medium transition-colors">
                  Disconnect
                </button>
              </div>

              <div className="space-y-4 max-w-xl">
                <h3 className="text-sm font-bold text-gray-300 uppercase tracking-wider mb-2">Webhook Secrets</h3>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1.5">Webhook Payload URL</label>
                  <div className="flex">
                    <input 
                      type="text" 
                      readOnly 
                      value="https://api.repomind.com/webhooks/github" 
                      className="w-full bg-surfaceHighlight/20 border border-white/10 text-gray-300 text-sm rounded-l-lg px-4 py-2 font-mono"
                    />
                    <button className="px-4 bg-surfaceHighlight hover:bg-surfaceHighlight/80 border-y border-r border-white/10 text-gray-200 rounded-r-lg transition-colors">
                      Copy
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'members' && (
            <div className="bg-surface/50 backdrop-blur-md border border-white/5 rounded-2xl">
              <MemberManagement organizationId={memberships?.[0]?.organization_id} memberships={memberships || []} />
            </div>
          )}

          {activeTab === 'billing' && (
            <div className="bg-surface/50 backdrop-blur-md border border-white/5 rounded-2xl p-12 text-center">
              <svg className="w-12 h-12 text-gray-600 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              <h2 className="text-xl font-bold text-white mb-2 capitalize">{activeTab} Management</h2>
              <p className="text-gray-400">This section is part of the RepoMind Enterprise tier.</p>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
