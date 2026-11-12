import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link, useOutletContext } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { onboardingApi, orgApi } from '../lib/api';
import { usePermissions, Permissions } from '../hooks/usePermissions';
import { Button } from '../components/ui/Button';
import MermaidViewer from '../components/Onboarding/MermaidViewer';

export default function CodebaseGuidePage() {
  const { rid } = useParams();
  const repoId = parseInt(rid, 10);
  const { memberships = [], currentOrgId = null } = useOutletContext() || {};
  const queryClient = useQueryClient();

  // Selected track state (defaults to 'backend', synced with user progress)
  const [selectedTrack, setSelectedTrack] = useState('backend');
  const [personalNotes, setPersonalNotes] = useState('');
  const [notesDirty, setNotesDirty] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const saveTimeoutRef = useRef(null);

  // Repository metadata query
  const { data: repoData } = useQuery({
    queryKey: ['repository', repoId],
    queryFn: () => orgApi.getRepository(repoId),
    enabled: !!repoId,
  });

  const orgId = currentOrgId || repoData?.project?.organization_id;
  const { can, isTeamLead, isLead, isOrgAdmin } = usePermissions(memberships, orgId);
  const canRefresh = (isOrgAdmin || isTeamLead || isLead) && can(Permissions.REPOS_INDEX);

  // 1. Blueprint Query
  const {
    data: blueprint,
    isLoading: blueprintLoading,
    error: blueprintError,
    refetch: refetchBlueprint,
  } = useQuery({
    queryKey: ['blueprint', repoId],
    queryFn: () => onboardingApi.getBlueprint(repoId),
    enabled: !!repoId,
    retry: (failureCount, error) => {
      // Don't retry on 400 (unindexed) or 403 (unauthorized)
      if (error?.status === 400 || error?.status === 403 || error?.status === 404) return false;
      return failureCount < 2;
    },
    refetchInterval: (query) => {
      // Poll every 4 seconds if generation is currently in-flight
      return query.state.data?.status === 'pending' ? 4000 : false;
    },
  });

  // 2. User Progress Query
  const {
    data: progress,
    isLoading: progressLoading,
    refetch: refetchProgress,
  } = useQuery({
    queryKey: ['onboarding-progress', repoId],
    queryFn: () => onboardingApi.getProgress(repoId),
    enabled: !!repoId,
  });

  // Sync initial user progress values
  useEffect(() => {
    if (progress) {
      if (progress.active_track && ['backend', 'frontend', 'fullstack'].includes(progress.active_track)) {
        setSelectedTrack(progress.active_track);
      }
      if (!notesDirty && progress.notes !== undefined) {
        setPersonalNotes(progress.notes || '');
      }
    }
  }, [progress, notesDirty]);

  // Clean up debounce timer on unmount
  useEffect(() => {
    return () => {
      if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
    };
  }, []);

  // 3. Progress Mutation
  const updateProgressMutation = useMutation({
    mutationFn: (payload) => onboardingApi.updateProgress(repoId, payload),
    onSuccess: (data) => {
      setNotesDirty(false);
      setSaveError(null);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2500);
      queryClient.setQueryData(['onboarding-progress', repoId], data);
    },
    onError: (err) => {
      setSaveError(
        err.message
          ? `Failed to save progress: ${err.message}. Your edits have been preserved.`
          : 'Failed to save progress. Your edits have been preserved.'
      );
    },
  });

  // 4. Refresh Blueprint Mutation
  const refreshMutation = useMutation({
    mutationFn: () => onboardingApi.refreshBlueprint(repoId),
    onSuccess: (data) => {
      queryClient.setQueryData(['blueprint', repoId], data);
    },
    onError: (err) => {
      alert(`Refresh failed: ${err.message}`);
    },
  });

  // Handlers for milestones
  const handleToggleMilestone = (milestoneId) => {
    const currentCompleted = progress?.completed_milestones || [];
    const isCompleted = currentCompleted.includes(milestoneId);
    const updated = isCompleted
      ? currentCompleted.filter((id) => id !== milestoneId)
      : [...currentCompleted, milestoneId];

    updateProgressMutation.mutate({
      completed_milestones: updated,
      active_track: selectedTrack,
    });
  };

  const handleTrackChange = (trackName) => {
    setSelectedTrack(trackName);
    updateProgressMutation.mutate({
      active_track: trackName,
    });
  };

  const handleNotesChange = (e) => {
    const nextNotes = e.target.value;
    setPersonalNotes(nextNotes);
    setNotesDirty(true);
    setSaveError(null);

    // Debounced autosave after 800ms of idle typing
    if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
    saveTimeoutRef.current = setTimeout(() => {
      updateProgressMutation.mutate({
        notes: nextNotes,
        active_track: selectedTrack,
      });
    }, 800);
  };

  const handleNotesBlur = () => {
    if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
    if (notesDirty) {
      updateProgressMutation.mutate({
        notes: personalNotes,
        active_track: selectedTrack,
      });
    }
  };

  // ─── Loading / Error States ──────────────────────────────────────────────────
  if (blueprintLoading && !blueprint) {
    return (
      <div className="space-y-6 max-w-7xl mx-auto py-6 animate-pulse">
        <div className="h-10 bg-surfaceHighlight/40 rounded-lg w-1/3" />
        <div className="h-44 bg-surfaceHighlight/30 rounded-xl" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="h-64 bg-surfaceHighlight/20 rounded-xl" />
          <div className="h-64 bg-surfaceHighlight/20 rounded-xl" />
          <div className="h-64 bg-surfaceHighlight/20 rounded-xl" />
        </div>
      </div>
    );
  }

  if (blueprintError && blueprintError.status === 400) {
    return (
      <div className="max-w-3xl mx-auto my-12 p-8 rounded-2xl border border-warning/30 bg-warning/5 text-center">
        <div className="w-14 h-14 mx-auto mb-4 rounded-xl bg-warning/10 text-warning flex items-center justify-center">
          <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h2 className="text-xl font-bold text-text-primary mb-2">Repository Not Indexed</h2>
        <p className="text-sm text-text-muted mb-6 max-w-md mx-auto">
          RepoMind generates grounded onboarding blueprints from the repository's indexed codebase. Please trigger repository indexing in Settings or Repositories first.
        </p>
        <Link to="/repositories">
          <Button variant="primary">Return to Repositories</Button>
        </Link>
      </div>
    );
  }

  if (blueprintError) {
    return (
      <div className="max-w-2xl mx-auto my-12 p-8 rounded-2xl border border-danger/30 bg-danger/5 text-center">
        <h2 className="text-lg font-bold text-danger mb-2">Error Loading Codebase Guide</h2>
        <p className="text-sm text-text-muted mb-4">{blueprintError.message}</p>
        <Button variant="secondary" onClick={() => refetchBlueprint()}>Retry Loading</Button>
      </div>
    );
  }

  // Active track data
  const currentTrackData = blueprint?.tracks?.[selectedTrack] || { reading_order: [], milestones: [] };
  const readingList = currentTrackData.reading_order || [];
  const milestones = currentTrackData.milestones || [];
  const completedMilestones = progress?.completed_milestones || [];

  // Dynamic progress calculation
  const completedCount = milestones.filter((m) => completedMilestones.includes(m.id)).length;
  const progressPercent = milestones.length > 0 ? Math.round((completedCount / milestones.length) * 100) : 0;

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-16">
      {/* ─── Breadcrumbs & Header ────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10 pb-6">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">
            <Link to="/repositories" className="hover:text-primary transition-colors">Repositories</Link>
            <span>/</span>
            <span className="text-text-primary">{repoData?.github_name || `Repo #${repoId}`}</span>
            <span>/</span>
            <span className="text-primary font-bold">Codebase Guide</span>
          </div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-text-primary tracking-tight">
              Developer Onboarding & Ramp-Up Blueprint
            </h1>
            {blueprint?.architecture_pattern && (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary border border-primary/20">
                {blueprint.architecture_pattern}
              </span>
            )}
          </div>
        </div>

        {/* Freshness & Action Controls */}
        <div className="flex items-center gap-3">
          {blueprint?.status === 'pending' ? (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-primary/10 border border-primary/30 text-xs font-medium text-primary animate-pulse">
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Analyzing Codebase...
            </div>
          ) : blueprint?.is_outdated ? (
            <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-warning/10 border border-warning/30 text-xs text-warning" title="New commits exist on default branch since this analysis">
              <span className="w-2 h-2 rounded-full bg-warning animate-ping" />
              Blueprint Outdated
            </div>
          ) : (
            <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-success/10 border border-success/30 text-xs text-success font-medium">
              <span className="w-2 h-2 rounded-full bg-success" />
              Up to date ({blueprint?.analyzed_commit_sha?.substring(0, 7)})
            </div>
          )}

          {canRefresh && (
            <Button
              variant="secondary"
              size="sm"
              loading={refreshMutation.isPending}
              disabled={blueprint?.status === 'pending' || refreshMutation.isPending}
              onClick={() => refreshMutation.mutate()}
              leftIcon={
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              }
            >
              Re-analyze Codebase
            </Button>
          )}
        </div>
      </div>

      {/* ─── SECTION 1: COMMON REPOSITORY ARCHITECTURE OVERVIEW ─────────────── */}
      <section aria-labelledby="section-overview" className="space-y-6">
        <div className="flex items-center gap-2">
          <span className="w-2 h-5 rounded-full bg-primary" />
          <h2 id="section-overview" className="text-lg font-bold text-text-primary">
            1. Repository Architecture Overview
          </h2>
        </div>

        {/* Summary Card */}
        <div className="p-6 rounded-2xl border border-white/10 bg-surface/70 backdrop-blur-md shadow-lg space-y-4">
          <p className="text-sm text-text-secondary leading-relaxed">
            {blueprint?.summary || 'No architectural summary available.'}
          </p>

          {/* Subsystems Breakdown */}
          {blueprint?.subsystems && blueprint.subsystems.length > 0 && (
            <div className="pt-4 border-t border-white/5">
              <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-3">
                Identified Subsystems & Key Directories
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {blueprint.subsystems.map((sub, i) => (
                  <div key={i} className="p-3.5 rounded-xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.04] transition-colors space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-sm text-text-primary">{sub.name}</span>
                      <code className="text-[11px] px-2 py-0.5 rounded bg-black/40 text-primary font-mono">{sub.path}</code>
                    </div>
                    <p className="text-xs text-text-muted line-clamp-2">{sub.purpose}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Request-to-Database Execution Flow */}
        {blueprint?.request_flow && blueprint.request_flow.length > 0 && (
          <div className="p-6 rounded-2xl border border-white/10 bg-surface/70 backdrop-blur-md space-y-4">
            <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wider">
              Request-to-Database Execution Flow Trace
            </h3>
            <div className="relative border-l border-primary/30 ml-3 pl-6 space-y-6 py-2">
              {blueprint.request_flow.map((step, idx) => (
                <div key={idx} className="relative group">
                  <div className="absolute -left-[31px] top-0.5 w-4 h-4 rounded-full border-2 border-primary bg-background flex items-center justify-center">
                    <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                  </div>
                  <div className="flex flex-col sm:flex-row sm:items-baseline gap-2">
                    <span className="text-xs font-bold text-primary uppercase tracking-wider">{step.layer}</span>
                    <span className="text-xs font-mono text-text-muted bg-surfaceHighlight/40 px-2 py-0.5 rounded">
                      {step.file} {step.symbol ? `→ ${step.symbol}` : ''}
                    </span>
                  </div>
                  <p className="text-xs text-text-secondary mt-1">{step.description}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Architecture Mermaid Flowchart */}
        {blueprint?.mermaid_diagram && (
          <div className="space-y-2">
            <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wider">
              Architecture & Component Relationships
            </h3>
            <MermaidViewer chart={blueprint.mermaid_diagram} />
          </div>
        )}
      </section>

      {/* ─── SECTION 2: ROLE-BASED ONBOARDING TRACKS ────────────────────────── */}
      <section aria-labelledby="section-tracks" className="space-y-6 pt-6 border-t border-white/10">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="w-2 h-5 rounded-full bg-accent" />
            <h2 id="section-tracks" className="text-lg font-bold text-text-primary">
              2. Select Your Learning Track
            </h2>
          </div>

          {/* Track Selector Tabs */}
          <div className="flex p-1 bg-surfaceHighlight/30 rounded-xl border border-white/10 w-fit">
            {[
              { id: 'backend', label: 'Backend Track' },
              { id: 'frontend', label: 'Frontend Track' },
              { id: 'fullstack', label: 'Fullstack Track' },
            ].map((track) => (
              <button
                key={track.id}
                onClick={() => handleTrackChange(track.id)}
                className={`px-4 py-1.5 text-xs font-semibold rounded-lg transition-all duration-150 ${
                  selectedTrack === track.id
                    ? 'bg-primary text-white shadow-sm shadow-primary/20'
                    : 'text-text-muted hover:text-text-primary'
                }`}
              >
                {track.label}
              </button>
            ))}
          </div>
        </div>

        {/* ─── SECTION 3: CURATED READING ORDER (5-7 FILES) ─────────────────── */}
        <div className="space-y-4">
          <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wider">
            Prioritized Reading Order ({selectedTrack} Focus)
          </h3>

          {readingList.length === 0 ? (
            <div className="p-6 rounded-xl border border-white/5 bg-surfaceHighlight/20 text-center text-xs text-text-muted">
              No specific files indexed for this track in this repository snapshot.
            </div>
          ) : (
            <div className="space-y-3">
              {readingList.map((item, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl border border-white/10 bg-surface/60 hover:border-primary/40 transition-all backdrop-blur-md flex flex-col md:flex-row md:items-start justify-between gap-4"
                >
                  <div className="flex items-start gap-3.5">
                    <span className="w-6 h-6 rounded-lg bg-primary/10 text-primary border border-primary/20 text-xs font-bold flex items-center justify-center flex-shrink-0 mt-0.5">
                      {idx + 1}
                    </span>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <code className="text-xs font-mono font-semibold text-text-primary bg-black/40 px-2 py-0.5 rounded border border-white/5">
                          {item.file_path}
                        </code>
                        <span className="text-[11px] px-2 py-0.5 rounded bg-accent/10 text-accent border border-accent/20 font-medium">
                          {item.role}
                        </span>
                        {item.key_lines && (
                          <span className="text-[11px] text-text-muted font-mono">{item.key_lines}</span>
                        )}
                      </div>
                      <p className="text-xs text-text-secondary leading-relaxed pt-1">
                        {item.why_read}
                      </p>
                      {item.focus_symbols && item.focus_symbols.length > 0 && (
                        <div className="flex items-center gap-1.5 pt-1 flex-wrap">
                          <span className="text-[11px] text-text-muted font-medium">Focus symbols:</span>
                          {item.focus_symbols.map((sym, sIdx) => (
                            <code key={sIdx} className="text-[11px] text-primary bg-primary/5 px-1.5 py-0.5 rounded font-mono">
                              {sym}
                            </code>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ─── SECTION 4: PERSONAL ONBOARDING CHECKLIST & SCRATCHPAD ──────────── */}
        <div className="p-6 rounded-2xl border border-white/10 bg-surface/70 backdrop-blur-md space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-4">
            <div>
              <h3 className="text-sm font-bold text-text-primary">
                My Hands-On Ramp-Up Milestones
              </h3>
              <p className="text-xs text-text-muted mt-0.5">
                Check off verifiable setup exercises and code inspection tasks as you complete them.
              </p>
            </div>
            {/* Progress indicator */}
            <div className="flex items-center gap-3">
              <div className="w-28 h-2 rounded-full bg-white/10 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-primary to-accent transition-all duration-300"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
              <span className="text-xs font-bold text-text-primary min-w-[36px]">
                {progressPercent}%
              </span>
            </div>
          </div>

          {/* Privacy Notice Banner */}
          <div className="flex items-center gap-2.5 px-3 py-2 rounded-lg bg-white/[0.02] border border-white/5 text-[11px] text-text-muted">
            <svg className="w-4 h-4 text-primary flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            <span>
              <strong>Privacy Guaranteed:</strong> Your progress checklist and notes are private to you. They are never shared with managers or used for developer evaluation.
            </span>
          </div>

          {/* Milestones Checklist */}
          <div className="space-y-3">
            {milestones.length === 0 ? (
              <div className="p-4 text-xs text-text-muted text-center">
                No milestones defined for this track.
              </div>
            ) : (
              milestones.map((m) => {
                const isChecked = completedMilestones.includes(m.id);
                return (
                  <label
                    key={m.id}
                    className={`flex items-start gap-3.5 p-3.5 rounded-xl border transition-all cursor-pointer ${
                      isChecked
                        ? 'bg-success/[0.04] border-success/30 text-text-primary'
                        : 'bg-white/[0.02] border-white/5 hover:border-white/15'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => handleToggleMilestone(m.id)}
                      className="w-4 h-4 mt-0.5 rounded border-white/20 text-primary focus:ring-primary focus:ring-offset-background bg-surfaceHighlight/50 cursor-pointer"
                    />
                    <div className="space-y-1 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className={`text-xs font-semibold ${isChecked ? 'line-through text-text-muted' : 'text-text-primary'}`}>
                          {m.title}
                        </span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 text-text-muted uppercase tracking-wider font-mono">
                          {m.action_type.replace('_', ' ')}
                        </span>
                      </div>
                      <p className="text-xs text-text-secondary">{m.description}</p>
                      {m.action_hint && (
                        <div className="pt-1 flex items-center gap-2">
                          <code className="text-[11px] font-mono bg-black/40 px-2 py-0.5 rounded text-primary border border-white/5">
                            {m.action_hint}
                          </code>
                        </div>
                      )}
                    </div>
                  </label>
                );
              })
            )}
          </div>

          {/* Private Developer Scratchpad */}
          <div className="pt-4 border-t border-white/10 space-y-2">
            <div className="flex items-center justify-between">
              <label htmlFor="dev-scratchpad" className="text-xs font-bold text-text-primary uppercase tracking-wider">
                Personal Developer Scratchpad (Private)
              </label>
              <div className="text-[11px] text-text-muted flex items-center gap-1.5">
                {updateProgressMutation.isPending && (
                  <span className="text-primary animate-pulse">Saving...</span>
                )}
                {saveSuccess && (
                  <span className="text-success font-medium">✓ Saved</span>
                )}
                {saveError && (
                  <span className="text-danger font-medium">{saveError}</span>
                )}
              </div>
            </div>
            <textarea
              id="dev-scratchpad"
              rows={3}
              value={personalNotes}
              onChange={handleNotesChange}
              onBlur={handleNotesBlur}
              placeholder="Record local port mappings, test commands, or personal onboarding notes here..."
              className="w-full bg-black/30 border border-white/10 rounded-xl p-3 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-primary font-mono"
            />
          </div>
        </div>
      </section>

      {/* ─── SECTION 5: CAUTION ZONES & SAFE STARTER AREAS ───────────────────── */}
      <section aria-labelledby="section-compass" className="space-y-6 pt-6 border-t border-white/10">
        <div className="flex items-center gap-2">
          <span className="w-2 h-5 rounded-full bg-danger" />
          <h2 id="section-compass" className="text-lg font-bold text-text-primary">
            3. Blast Radius & Starter Compass
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Caution Zones */}
          <div className="p-6 rounded-2xl border border-danger/25 bg-danger/[0.03] backdrop-blur-md space-y-4">
            <div className="flex items-center gap-2 text-danger">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <h3 className="text-sm font-bold tracking-tight">Caution Zones (High Blast Radius)</h3>
            </div>
            <p className="text-xs text-text-muted">
              These areas govern security, migrations, or shared infrastructure. Always request senior team review.
            </p>

            <div className="space-y-2.5">
              {!blueprint?.caution_zones || blueprint.caution_zones.length === 0 ? (
                <p className="text-xs text-text-muted italic">No high-risk caution zones flagged.</p>
              ) : (
                blueprint.caution_zones.map((zone, i) => (
                  <div key={i} className="p-3 rounded-xl border border-danger/20 bg-black/20 space-y-1">
                    <div className="flex items-center justify-between">
                      <code className="text-xs font-mono font-bold text-danger">{zone.path}</code>
                      <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-danger/10 text-danger border border-danger/20">
                        {zone.risk_level}
                      </span>
                    </div>
                    <p className="text-xs text-text-secondary">{zone.reason}</p>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Safe Starter Areas */}
          <div className="p-6 rounded-2xl border border-success/25 bg-success/[0.03] backdrop-blur-md space-y-4">
            <div className="flex items-center gap-2 text-success">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="text-sm font-bold tracking-tight">Safe Starter Areas (Beginner Friendly)</h3>
            </div>
            <p className="text-xs text-text-muted">
              Isolated modules and test suites ideal for your first contribution or exploratory PR.
            </p>

            <div className="space-y-2.5">
              {!blueprint?.safe_starter_areas || blueprint.safe_starter_areas.length === 0 ? (
                <p className="text-xs text-text-muted italic">No specific starter areas flagged.</p>
              ) : (
                blueprint.safe_starter_areas.map((safe, i) => (
                  <div key={i} className="p-3 rounded-xl border border-success/20 bg-black/20 space-y-1.5">
                    <span className="text-xs font-bold text-success">{safe.area}</span>
                    <p className="text-xs text-text-secondary">{safe.description}</p>
                    {safe.starter_ideas && safe.starter_ideas.length > 0 && (
                      <ul className="list-disc list-inside text-[11px] text-text-muted pt-1 space-y-0.5">
                        {safe.starter_ideas.map((idea, idx) => (
                          <li key={idx}>{idea}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
