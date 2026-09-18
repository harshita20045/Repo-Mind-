import React, { useState, useEffect } from 'react';
import { Link, useOutletContext } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { orgApi } from '../lib/api';
import { usePermissions, Permissions } from '../hooks/usePermissions';

export default function RepositoriesPage() {
  const { memberships } = useOutletContext();
  const orgId = memberships?.[0]?.organization_id;
  const queryClient = useQueryClient();
  const { can, isOrgAdmin } = usePermissions(memberships, orgId);
  const canManageOrg = isOrgAdmin || can(Permissions.PROJECTS_CREATE);

  const [selectedProjectId, setSelectedProjectId] = useState(null);
  const [isAddProjectOpen, setIsAddProjectOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  
  const [isConnectRepoOpen, setIsConnectRepoOpen] = useState(false);
  const [repoForm, setRepoForm] = useState({ github_owner: '', github_name: '', default_branch: 'main', pat: '' });
  
  const [errorMsg, setErrorMsg] = useState(null);

  // Queries
  const { data: projects = [], isLoading: loadingProjects, error: projectError } = useQuery({
    queryKey: ['projects', orgId],
    queryFn: () => orgApi.getProjects(orgId),
    enabled: !!orgId,
  });

  // Auto-select first project if none selected
  useEffect(() => {
    if (projects.length > 0 && !selectedProjectId) {
      setSelectedProjectId(projects[0].id);
    }
  }, [projects, selectedProjectId]);

  const { data: repositories = [], isLoading: loadingRepos, error: repoError } = useQuery({
    queryKey: ['repositories', selectedProjectId],
    queryFn: () => orgApi.getRepositories(selectedProjectId),
    enabled: !!selectedProjectId,
  });

  // Mutations
  const createProjectMutation = useMutation({
    mutationFn: (name) => orgApi.createProject(orgId, name),
    onSuccess: (newProject) => {
      queryClient.invalidateQueries(['projects', orgId]);
      setSelectedProjectId(newProject.id);
      setIsAddProjectOpen(false);
      setNewProjectName('');
      setErrorMsg(null);
    },
    onError: (err) => setErrorMsg(err.message),
  });

  const connectRepoMutation = useMutation({
    mutationFn: (payload) => orgApi.connectRepository(orgId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries(['repositories', selectedProjectId]);
      setIsConnectRepoOpen(false);
      setRepoForm({ github_owner: '', github_name: '', default_branch: 'main', pat: '' });
      setErrorMsg(null);
    },
    onError: (err) => setErrorMsg(err.message),
  });

  const triggerIndexMutation = useMutation({
    mutationFn: (repoId) => orgApi.triggerIndex(repoId),
    onSuccess: () => {
      queryClient.invalidateQueries(['repositories', selectedProjectId]);
    },
    onError: (err) => alert(err.message),
  });

  const isLoading = loadingProjects || loadingRepos;
  const error = projectError || repoError;

  return (
    <div className="space-y-6 animate-slide-up relative">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Repositories</h1>
          <p className="text-gray-400 text-sm">Manage and monitor source code repositories onboarded to RepoMind.</p>
        </div>
        
        {canManageOrg && (
          <div className="flex gap-3">
             <button 
                onClick={() => setIsAddProjectOpen(true)}
                className="px-4 py-2 bg-surfaceHighlight hover:bg-white/10 text-white rounded-lg font-medium transition-colors border border-white/10 flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                New Project
              </button>
            <button 
              onClick={() => {
                if (!selectedProjectId) {
                  alert("Please create or select a project first.");
                  return;
                }
                setIsConnectRepoOpen(true);
              }}
              className="px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg font-medium transition-colors border border-white/10 shadow-lg shadow-primary/20 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
              Connect Repository
            </button>
          </div>
        )}
      </div>

      {/* Project Selector */}
      {projects.length > 0 && (
        <div className="flex items-center gap-4">
          <label className="text-sm text-gray-400 font-medium">Project Context:</label>
          <select 
            value={selectedProjectId || ''} 
            onChange={(e) => setSelectedProjectId(Number(e.target.value))}
            className="bg-surfaceHighlight border border-white/10 text-white text-sm rounded-lg focus:ring-primary focus:border-primary block p-2.5 outline-none"
          >
            {projects.map(p => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        </div>
      )}

      {/* Error Displays */}
      {error && (
        <div className="p-4 bg-danger/10 border border-danger/20 text-danger rounded-xl">
          {error.message}
        </div>
      )}

      <div className="bg-surface/50 backdrop-blur-md border border-white/5 rounded-2xl overflow-hidden min-h-[400px]">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-400">
            <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mb-4"></div>
            Loading repositories...
          </div>
        ) : repositories.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-400">
            <svg className="w-12 h-12 mb-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            <p>No repositories found in this project.</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-surfaceHighlight/20 border-b border-white/5 text-xs uppercase tracking-wider text-gray-500 font-semibold">
                    <th className="px-6 py-4">Repository Name</th>
                    <th className="px-6 py-4">Owner</th>
                    <th className="px-6 py-4">Default Branch</th>
                    <th className="px-6 py-4">Index Status</th>
                    <th className="px-6 py-4">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {repositories.map(repo => (
                    <tr key={repo.id} className="hover:bg-white/[0.02] transition-colors group">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-surfaceHighlight flex items-center justify-center text-gray-400 group-hover:text-primary transition-colors border border-white/5">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                            </svg>
                          </div>
                          <div>
                            <Link to={`/repositories/${repo.id}/pull-requests`} className="font-medium text-gray-200 hover:text-white transition-colors">
                              {repo.github_name}
                            </Link>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                        {repo.github_owner}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400 font-mono">
                        {repo.default_branch}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${
                          repo.index_status === 'indexed' ? 'bg-success/10 text-success border-success/20' :
                          repo.index_status === 'failed' ? 'bg-danger/10 text-danger border-danger/20' :
                          repo.index_status === 'indexing' ? 'bg-warning/10 text-warning border-warning/20' :
                          'bg-gray-500/10 text-gray-400 border-gray-500/20'
                        }`}>
                          {repo.index_status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {canManageOrg && (repo.index_status === 'indexed' || repo.index_status === 'failed') && (
                          <button
                            onClick={() => triggerIndexMutation.mutate(repo.id)}
                            disabled={triggerIndexMutation.isLoading}
                            className="text-primary hover:text-primary-hover font-medium transition-colors disabled:opacity-50"
                          >
                            Re-index
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>

      {/* Add Project Modal */}
      {isAddProjectOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
          <div className="bg-surface border border-white/10 rounded-2xl p-6 w-full max-w-md shadow-2xl animate-scale-in">
            <h2 className="text-xl font-bold text-white mb-4">Create New Project</h2>
            {errorMsg && <p className="text-danger text-sm mb-4">{errorMsg}</p>}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-300 mb-2">Project Name</label>
              <input 
                type="text" 
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                className="w-full bg-surfaceHighlight/30 border border-white/10 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-1 focus:ring-primary/50"
                placeholder="e.g. Frontend Team"
              />
            </div>
            <div className="flex justify-end gap-3">
              <button 
                onClick={() => { setIsAddProjectOpen(false); setErrorMsg(null); }}
                className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button 
                onClick={() => createProjectMutation.mutate(newProjectName)}
                disabled={!newProjectName.trim() || createProjectMutation.isLoading}
                className="px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg font-medium transition-colors disabled:opacity-50"
              >
                {createProjectMutation.isLoading ? 'Creating...' : 'Create Project'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Connect Repository Modal */}
      {isConnectRepoOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
          <div className="bg-surface border border-white/10 rounded-2xl p-6 w-full max-w-lg shadow-2xl animate-scale-in">
            <h2 className="text-xl font-bold text-white mb-4">Connect GitHub Repository</h2>
            <p className="text-sm text-gray-400 mb-6">Repository will be added to the currently selected project.</p>
            {errorMsg && <div className="text-danger text-sm mb-4 p-3 bg-danger/10 border border-danger/20 rounded-lg">{errorMsg}</div>}
            
            <div className="space-y-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">GitHub Owner (User/Org)</label>
                <input 
                  type="text" 
                  value={repoForm.github_owner}
                  onChange={(e) => setRepoForm({...repoForm, github_owner: e.target.value})}
                  className="w-full bg-surfaceHighlight/30 border border-white/10 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-1 focus:ring-primary/50"
                  placeholder="e.g. google"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Repository Name</label>
                <input 
                  type="text" 
                  value={repoForm.github_name}
                  onChange={(e) => setRepoForm({...repoForm, github_name: e.target.value})}
                  className="w-full bg-surfaceHighlight/30 border border-white/10 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-1 focus:ring-primary/50"
                  placeholder="e.g. react"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Default Branch</label>
                <input 
                  type="text" 
                  value={repoForm.default_branch}
                  onChange={(e) => setRepoForm({...repoForm, default_branch: e.target.value})}
                  className="w-full bg-surfaceHighlight/30 border border-white/10 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-1 focus:ring-primary/50"
                  placeholder="e.g. main"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Personal Access Token (PAT)</label>
                <input 
                  type="password" 
                  value={repoForm.pat}
                  onChange={(e) => setRepoForm({...repoForm, pat: e.target.value})}
                  className="w-full bg-surfaceHighlight/30 border border-white/10 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-1 focus:ring-primary/50"
                  placeholder="ghp_xxxxxxxxxxxx"
                />
                <p className="text-xs text-gray-500 mt-1">Requires 'repo' scope. Token is encrypted immediately and not stored in plaintext.</p>
              </div>
            </div>

            <div className="flex justify-end gap-3">
              <button 
                onClick={() => { setIsConnectRepoOpen(false); setErrorMsg(null); }}
                className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button 
                onClick={() => connectRepoMutation.mutate({ ...repoForm, project_id: selectedProjectId })}
                disabled={!repoForm.github_owner || !repoForm.github_name || !repoForm.pat || connectRepoMutation.isLoading}
                className="px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg font-medium transition-colors disabled:opacity-50"
              >
                {connectRepoMutation.isLoading ? 'Connecting...' : 'Connect Repository'}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
