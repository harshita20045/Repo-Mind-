import React, { useState, useEffect } from 'react';
import { Link, useOutletContext } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { orgApi } from '../lib/api';
import { usePermissions, Permissions } from '../hooks/usePermissions';
import Modal from '../components/ui/Modal';
import { Button } from '../components/ui/Button';
import { StatusBadge } from '../components/ui/Badge';
import EmptyState from '../components/ui/EmptyState';
import { TableRowSkeleton } from '../components/ui/LoadingSkeleton';

// ─── Form Field ────────────────────────────────────────────────────────────────
function Field({ label, hint, error, children }) {
  return (
    <div>
      <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
        {label}
      </label>
      {children}
      {hint && !error && <p className="text-xs text-text-muted mt-1">{hint}</p>}
      {error && <p className="text-xs text-danger mt-1" role="alert">{error}</p>}
    </div>
  );
}

function TextInput({ value, onChange, placeholder, type = 'text', className = '', ...rest }) {
  return (
    <input
      type={type}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      className={`w-full bg-surfaceHighlight/40 border border-white/[0.09] text-text-primary text-sm rounded-lg px-3.5 py-2.5 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary/40 placeholder-text-muted transition-all ${className}`}
      {...rest}
    />
  );
}

// ─── Status badge for index status ────────────────────────────────────────────
function IndexStatusBadge({ status }) {
  const label = {
    indexed:   'Indexed',
    indexing:  'Indexing',
    failed:    'Failed',
    unindexed: 'Unindexed',
    pending:   'Pending',
  }[status?.toLowerCase()] || status || 'Unknown';

  return <StatusBadge status={status?.toLowerCase()} label={label} />;
}

// ─── Main Page ────────────────────────────────────────────────────────────────
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
  const [repoForm, setRepoForm] = useState({
    github_owner: '', github_name: '', default_branch: 'main', pat: '',
  });
  const [errorMsg, setErrorMsg] = useState(null);
  const [indexingRepoId, setIndexingRepoId] = useState(null);

  // Queries
  const { data: projects = [], isLoading: loadingProjects, error: projectError } = useQuery({
    queryKey: ['projects', orgId],
    queryFn: () => orgApi.getProjects(orgId),
    enabled: !!orgId,
  });

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
      queryClient.invalidateQueries({ queryKey: ['projects', orgId] });
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
      queryClient.invalidateQueries({ queryKey: ['repositories', selectedProjectId] });
      setIsConnectRepoOpen(false);
      setRepoForm({ github_owner: '', github_name: '', default_branch: 'main', pat: '' });
      setErrorMsg(null);
    },
    onError: (err) => setErrorMsg(err.message),
  });

  const triggerIndexMutation = useMutation({
    mutationFn: (repoId) => orgApi.triggerIndex(repoId),
    onMutate: (repoId) => setIndexingRepoId(repoId),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['repositories', selectedProjectId] });
      setIndexingRepoId(null);
    },
    onError: (err) => setErrorMsg(err.message),
  });

  const isLoading = loadingProjects || loadingRepos;
  const error = projectError || repoError;

  const canConnectRepo = can(Permissions.REPOS_CONNECT);
  const canIndex = can(Permissions.REPOS_INDEX);

  return (
    <div className="space-y-5 animate-slide-up">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">Repositories</h1>
          <p className="text-sm text-text-muted mt-1">Manage and monitor repositories connected to RepoMind.</p>
        </div>
        {canManageOrg && (
          <div className="flex gap-2 flex-shrink-0">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setIsAddProjectOpen(true)}
              leftIcon={
                <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                </svg>
              }
            >
              New Project
            </Button>
            {canConnectRepo && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => {
                  if (!selectedProjectId) {
                    setErrorMsg('Please create or select a project first.');
                    return;
                  }
                  setIsConnectRepoOpen(true);
                }}
                leftIcon={
                  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                }
              >
                Connect Repository
              </Button>
            )}
          </div>
        )}
      </div>

      {/* Error banner */}
      {(error || errorMsg) && (
        <div className="flex items-center gap-3 p-3.5 bg-danger/8 border border-danger/20 text-danger text-sm rounded-xl" role="alert">
          <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {errorMsg || error?.message}
          <button
            onClick={() => setErrorMsg(null)}
            className="ml-auto text-danger/60 hover:text-danger"
            aria-label="Dismiss error"
          >
            ×
          </button>
        </div>
      )}

      {/* Project selector */}
      {projects.length > 0 && (
        <div className="flex items-center gap-3 flex-wrap">
          <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">Project</span>
          <div className="flex gap-1.5 flex-wrap" role="tablist" aria-label="Project selector">
            {projects.map(p => (
              <button
                key={p.id}
                role="tab"
                aria-selected={selectedProjectId === p.id}
                onClick={() => setSelectedProjectId(p.id)}
                className={`px-3.5 py-1.5 rounded-lg text-sm font-medium border transition-all duration-150 ${
                  selectedProjectId === p.id
                    ? 'bg-primary/10 text-primary border-primary/25'
                    : 'bg-transparent text-text-muted border-white/[0.08] hover:text-text-primary hover:border-white/15 hover:bg-white/[0.04]'
                }`}
              >
                {p.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Repository table */}
      <div className="bg-surface border border-white/[0.07] rounded-xl overflow-hidden">
        {loadingProjects && projects.length === 0 ? (
          <div className="p-6">
            <div className="space-y-1">
              {/* Header skeleton */}
              <div className="flex gap-4 px-4 py-3 border-b border-white/[0.06]">
                {['w-32', 'w-24', 'w-20', 'w-24', 'w-16'].map((w, i) => (
                  <div key={i} className={`h-3 ${w} skeleton rounded`} />
                ))}
              </div>
              {[0,1,2].map(i => (
                <table key={i} className="w-full"><tbody><TableRowSkeleton cols={5} /></tbody></table>
              ))}
            </div>
          </div>
        ) : isLoading && repositories.length === 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/[0.06] bg-white/[0.02]">
                  {['Repository', 'Owner', 'Branch', 'Status', 'Actions'].map(h => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[0,1,2].map(i => <TableRowSkeleton key={i} cols={5} />)}
              </tbody>
            </table>
          </div>
        ) : repositories.length === 0 ? (
          <EmptyState
            icon="repo"
            title={projects.length === 0 ? 'No projects yet' : 'No repositories in this project'}
            description={
              projects.length === 0
                ? 'Create a project first, then connect your GitHub repositories to start reviewing pull requests.'
                : 'Connect a GitHub repository to this project to start AI-powered PR reviews.'
            }
            action={
              canManageOrg && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => projects.length === 0 ? setIsAddProjectOpen(true) : setIsConnectRepoOpen(true)}
                >
                  {projects.length === 0 ? 'Create Project' : 'Connect Repository'}
                </Button>
              )
            }
            className="py-20"
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full" role="table" aria-label="Repository list">
              <thead>
                <tr className="border-b border-white/[0.06] bg-white/[0.02]">
                  <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">Repository</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">Owner</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">Branch</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">Index Status</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {repositories.map(repo => (
                  <tr key={repo.id} className="hover:bg-white/[0.02] transition-colors group">
                    <td className="px-4 py-3.5">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-surfaceHighlight/60 border border-white/[0.07] flex items-center justify-center text-text-muted group-hover:text-primary transition-colors flex-shrink-0">
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                          </svg>
                        </div>
                        <Link
                          to={`/repositories/${repo.id}/pull-requests`}
                          className="text-sm font-semibold text-text-primary hover:text-primary transition-colors"
                        >
                          {repo.github_name}
                        </Link>
                      </div>
                    </td>
                    <td className="px-4 py-3.5">
                      <span className="text-sm text-text-muted">{repo.github_owner}</span>
                    </td>
                    <td className="px-4 py-3.5">
                      <span className="font-mono text-xs text-text-muted bg-white/5 border border-white/[0.07] px-2 py-0.5 rounded">
                        {repo.default_branch}
                      </span>
                    </td>
                    <td className="px-4 py-3.5">
                      <IndexStatusBadge status={repo.index_status} />
                    </td>
                    <td className="px-4 py-3.5">
                      {canIndex && (repo.index_status === 'indexed' || repo.index_status === 'failed' || repo.index_status === 'unindexed') && (
                        <Button
                          variant="ghost"
                          size="xs"
                          onClick={() => triggerIndexMutation.mutate(repo.id)}
                          loading={indexingRepoId === repo.id}
                          disabled={indexingRepoId === repo.id}
                        >
                          {repo.index_status === 'unindexed' ? 'Index' : 'Re-index'}
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create Project Modal */}
      <Modal
        isOpen={isAddProjectOpen}
        onClose={() => { setIsAddProjectOpen(false); setErrorMsg(null); setNewProjectName(''); }}
        title="Create New Project"
        subtitle="Projects group related repositories and team members together."
        size="sm"
      >
        {errorMsg && (
          <div className="mb-4 p-3 bg-danger/8 border border-danger/20 text-danger text-sm rounded-lg" role="alert">
            {errorMsg}
          </div>
        )}
        <Field label="Project Name">
          <TextInput
            value={newProjectName}
            onChange={(e) => setNewProjectName(e.target.value)}
            placeholder="e.g. Frontend Team"
            autoFocus
          />
        </Field>
        <div className="flex justify-end gap-3 mt-6">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => { setIsAddProjectOpen(false); setErrorMsg(null); }}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => createProjectMutation.mutate(newProjectName)}
            loading={createProjectMutation.isPending}
            disabled={!newProjectName.trim()}
          >
            Create Project
          </Button>
        </div>
      </Modal>

      {/* Connect Repository Modal */}
      <Modal
        isOpen={isConnectRepoOpen}
        onClose={() => { setIsConnectRepoOpen(false); setErrorMsg(null); }}
        title="Connect GitHub Repository"
        subtitle={`Connecting to project: ${projects.find(p => p.id === selectedProjectId)?.name || '—'}`}
        size="md"
      >
        {errorMsg && (
          <div className="mb-4 p-3 bg-danger/8 border border-danger/20 text-danger text-sm rounded-lg" role="alert">
            {errorMsg}
          </div>
        )}
        <div className="space-y-4">
          <Field label="GitHub Owner" hint="The GitHub user or organization that owns the repository">
            <TextInput
              value={repoForm.github_owner}
              onChange={(e) => setRepoForm({ ...repoForm, github_owner: e.target.value })}
              placeholder="e.g. google"
              autoComplete="off"
            />
          </Field>
          <Field label="Repository Name">
            <TextInput
              value={repoForm.github_name}
              onChange={(e) => setRepoForm({ ...repoForm, github_name: e.target.value })}
              placeholder="e.g. react"
              autoComplete="off"
            />
          </Field>
          <Field label="Default Branch">
            <TextInput
              value={repoForm.default_branch}
              onChange={(e) => setRepoForm({ ...repoForm, default_branch: e.target.value })}
              placeholder="main"
            />
          </Field>
          <Field
            label="Personal Access Token (PAT)"
            hint="Requires 'repo' scope. Encrypted immediately — never stored in plaintext."
          >
            <TextInput
              type="password"
              value={repoForm.pat}
              onChange={(e) => setRepoForm({ ...repoForm, pat: e.target.value })}
              placeholder="ghp_xxxxxxxxxxxx"
              autoComplete="new-password"
            />
          </Field>
        </div>
        <div className="flex justify-end gap-3 mt-6">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => { setIsConnectRepoOpen(false); setErrorMsg(null); }}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => connectRepoMutation.mutate({ ...repoForm, project_id: selectedProjectId })}
            loading={connectRepoMutation.isPending}
            disabled={!repoForm.github_owner || !repoForm.github_name || !repoForm.pat}
          >
            Connect Repository
          </Button>
        </div>
      </Modal>
    </div>
  );
}
