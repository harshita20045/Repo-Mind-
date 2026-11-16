import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import HistoricalIntelligencePage from '../src/pages/HistoricalIntelligencePage';
import HistoricalContextCard from '../src/components/Review/HistoricalContextCard';

// Mock historyApi and orgApi
vi.mock('../src/lib/api', () => ({
  historyApi: {
    getHistoricalPrs: vi.fn(),
    getPreviousChanges: vi.fn(),
    getRecurringIssues: vi.fn(),
    getAdrs: vi.fn(),
    getSimilarBugs: vi.fn(),
    compareChanges: vi.fn(),
    triggerIndex: vi.fn(),
  },
  orgApi: {
    getRepository: vi.fn(),
  },
}));

import { historyApi, orgApi } from '../src/lib/api';

const mockRepo = {
  id: 1,
  github_owner: 'repomind-org',
  github_name: 'core-service',
  default_branch: 'main',
};

const mockHistoricalPrs = [
  {
    id: 101,
    github_number: 101,
    title: 'Fix session token deadlock under high load',
    description: 'Added mutex lock to token renewal',
    state: 'merged',
    author: 'alice',
    merged_at: '2025-01-11T00:00:00Z',
    touched_files: ['backend/app/auth/service.py'],
  },
];

const mockHistoricalCommits = [
  {
    id: 1,
    commit_sha: 'c101a01',
    commit_message: 'fix(auth): prevent deadlock in token renewal',
    author_name: 'alice',
    committed_at: '2025-01-10T14:00:00Z',
    pull_request_number: 101,
    is_bugfix: true,
    touched_files: ['backend/app/auth/service.py'],
    original_decision: 'Guard token renewal with mutex lock',
    supporting_evidence: 'Bugfix commit c101a01; PR #101',
  },
];

const mockHotspots = [
  {
    id: 1,
    repository_id: 1,
    file_path: 'backend/app/auth/service.py',
    bugfix_count: 3,
    recurring_finding_count: 5,
    hotspot_score: 8.5,
    severity: 'critical',
    recommendation: 'Refactor session management into smaller modular units.',
    last_modified_at: '2025-02-01T00:00:00Z',
  },
];

const mockAdrs = [
  {
    id: 1,
    repository_id: 1,
    adr_number: 'ADR-004',
    title: 'Session Token Synchronization Strategy',
    status: 'Confirmed',
    decision: 'All session mutations must use centralized atomic redis or database row locks.',
    context: 'Distributed workers caused token renewal collisions.',
    reason: 'Prevents race conditions and token replay bugs.',
    consequences: 'Minor latency increase with linear consistency guarantees.',
    file_path: 'docs/02-architecture/architecture-decisions.md',
    affected_modules: ['backend/app/auth'],
  },
];

const mockComparison = {
  repository_id: 1,
  pull_request_id: 101,
  target_file: 'backend/app/auth/service.py',
  is_problematic_hotspot: true,
  hotspot_details: mockHotspots[0],
  relevant_adrs: mockAdrs,
  historical_commits: mockHistoricalCommits,
  similar_resolved_bugs: [
    {
      id: 1,
      title: 'Unsynchronized session token state update',
      file_path: 'backend/app/auth/service.py',
      category: 'security',
      resolution_notes: 'Resolved by wrapping refresh in mutex lock',
      commit_sha: 'c101a01',
      resolved_at: '2025-01-11T00:00:00Z',
    },
  ],
  change_evolution_summary: 'File backend/app/auth/service.py has 3 prior bugfixes and 1 governing ADR (ADR-004).',
};

function renderWithClient(ui, route = '/repositories/1/history') {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[route]}>
        <Routes>
          <Route path="/repositories/:rid/history" element={ui} />
          <Route path="*" element={ui} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('Historical Intelligence Module', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    orgApi.getRepository.mockResolvedValue(mockRepo);
    historyApi.getHistoricalPrs.mockResolvedValue(mockHistoricalPrs);
    historyApi.getPreviousChanges.mockResolvedValue(mockHistoricalCommits);
    historyApi.getRecurringIssues.mockResolvedValue(mockHotspots);
    historyApi.getAdrs.mockResolvedValue(mockAdrs);
    historyApi.compareChanges.mockResolvedValue(mockComparison);
    historyApi.triggerIndex.mockResolvedValue({ status: 'completed' });
  });

  describe('HistoricalIntelligencePage', () => {
    it('renders page header and tabs correctly', async () => {
      renderWithClient(<HistoricalIntelligencePage />);

      await waitFor(() => {
        expect(screen.getByText('Historical Code Intelligence')).toBeInTheDocument();
      });

      expect(screen.getByRole('tab', { name: /PR & Change Search/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /Recurring Issues & Hotspots/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /Architecture Decisions \(ADRs\)/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /Change Evolution & Decisions/i })).toBeInTheDocument();
    });

    it('displays historical PRs in the PR & Change Search tab', async () => {
      renderWithClient(<HistoricalIntelligencePage />);

      await waitFor(() => {
        expect(screen.getByText('Fix session token deadlock under high load')).toBeInTheDocument();
      });
      expect(screen.getByText('alice')).toBeInTheDocument();
      expect(screen.getByText('merged')).toBeInTheDocument();
    });

    it('switches to Recurring Hotspots tab and displays hotspot metrics', async () => {
      renderWithClient(<HistoricalIntelligencePage />);

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /Recurring Issues & Hotspots/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('tab', { name: /Recurring Issues & Hotspots/i }));

      await waitFor(() => {
        expect(screen.getByText('backend/app/auth/service.py')).toBeInTheDocument();
      });
      expect(screen.getByText('8.5')).toBeInTheDocument();
    });

    it('switches to Architecture Decisions (ADRs) tab and displays parsed ADRs', async () => {
      renderWithClient(<HistoricalIntelligencePage />);

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /Architecture Decisions \(ADRs\)/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('tab', { name: /Architecture Decisions \(ADRs\)/i }));

      await waitFor(() => {
        expect(screen.getByText('ADR-004')).toBeInTheDocument();
        expect(screen.getByText('Session Token Synchronization Strategy')).toBeInTheDocument();
      });
      expect(screen.getByText(/All session mutations must use centralized atomic redis/i)).toBeInTheDocument();
    });

    it('triggers sync when index button is clicked', async () => {
      renderWithClient(<HistoricalIntelligencePage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Re-index history/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /Re-index history/i }));
      await waitFor(() => {
        expect(historyApi.triggerIndex).toHaveBeenCalled();
      });
    });
  });

  describe('HistoricalContextCard (Review Integration)', () => {
    it('renders hotspot warning and governing ADRs for pull request changes', async () => {
      renderWithClient(<HistoricalContextCard repositoryId={1} pullRequestId={101} />);

      await waitFor(() => {
        expect(screen.getByText('Problematic Hotspot Detected')).toBeInTheDocument();
      });

      expect(screen.getByText(/Caution: Modified files have high historical churn or bug rates/i)).toBeInTheDocument();
      expect(screen.getByText('ADR-004')).toBeInTheDocument();
      expect(screen.getByText('Session Token Synchronization Strategy')).toBeInTheDocument();
      expect(screen.getByText(/Original Engineering Decision:/i)).toBeInTheDocument();
      expect(screen.getByText(/Guard token renewal with mutex lock/i)).toBeInTheDocument();
      expect(screen.getByText(/Supporting Evidence: Bugfix commit c101a01; PR #101/i)).toBeInTheDocument();
      expect(screen.getByText('Previously Resolved Similar Bugs (1)')).toBeInTheDocument();
    });
  });
});
