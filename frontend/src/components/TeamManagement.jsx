import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { orgApi } from '../lib/api';
import { Button } from './ui/Button';

export default function TeamManagement({ orgId }) {
  const queryClient = useQueryClient();
  const [isCreating, setIsCreating] = useState(false);
  const [newTeamName, setNewTeamName] = useState('');
  const [newTeamDesc, setNewTeamDesc] = useState('');
  const [errorMsg, setErrorMsg] = useState(null);

  const { data: teams = [], isLoading } = useQuery({
    queryKey: ['teams', orgId],
    queryFn: () => orgApi.getTeams(orgId),
    enabled: !!orgId,
  });

  const createMutation = useMutation({
    mutationFn: () => orgApi.createTeam(orgId, newTeamName, newTeamDesc),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams', orgId] });
      setIsCreating(false);
      setNewTeamName('');
      setNewTeamDesc('');
      setErrorMsg(null);
    },
    onError: (err) => setErrorMsg(err.message),
  });

  const handleCreate = (e) => {
    e.preventDefault();
    createMutation.mutate();
  };

  return (
    <div className="bg-surface border border-border rounded-lg shadow-sm p-6 space-y-6 animate-slide-up">
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-base font-bold text-text-primary mb-0.5">Team Management</h2>
          <p className="text-xs text-text-muted">Organize members into functional teams (e.g. Backend, Frontend, Security).</p>
        </div>
        <Button size="sm" variant="primary" onClick={() => setIsCreating(!isCreating)}>
          {isCreating ? 'Cancel' : 'Create Team'}
        </Button>
      </div>

      {errorMsg && (
        <div className="p-3 bg-danger/10 border border-danger/20 text-danger text-sm rounded-lg">
          {errorMsg}
        </div>
      )}

      {isCreating && (
        <form onSubmit={handleCreate} className="bg-surfaceHighlight border border-border rounded-lg p-4 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">Team Name</label>
            <input
              type="text"
              value={newTeamName}
              onChange={(e) => setNewTeamName(e.target.value)}
              placeholder="e.g. Core Backend"
              className="w-full bg-surface border border-border text-[13px] rounded-md px-3 py-2 text-text-primary focus:border-primary focus:outline-none"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">Description</label>
            <input
              type="text"
              value={newTeamDesc}
              onChange={(e) => setNewTeamDesc(e.target.value)}
              placeholder="Optional description"
              className="w-full bg-surface border border-border text-[13px] rounded-md px-3 py-2 text-text-primary focus:border-primary focus:outline-none"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button size="sm" variant="primary" type="submit" loading={createMutation.isPending}>
              Save Team
            </Button>
          </div>
        </form>
      )}

      {isLoading ? (
        <div className="flex justify-center p-8">
          <svg className="animate-spin w-6 h-6 text-primary" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
            <path className="opacity-80" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
        </div>
      ) : teams.length === 0 ? (
        <div className="text-center py-8 text-text-muted text-sm border border-dashed border-border rounded-lg">
          No teams have been created yet.
        </div>
      ) : (
        <div className="space-y-3">
          {teams.map(team => (
            <div key={team.id} className="border border-border rounded-lg p-4 bg-surfaceHighlight/50 flex justify-between items-center group">
              <div>
                <h3 className="text-sm font-semibold text-text-primary">{team.name}</h3>
                {team.description && <p className="text-xs text-text-muted mt-0.5">{team.description}</p>}
              </div>
              <Button size="xs" variant="outline">
                Manage Members
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
