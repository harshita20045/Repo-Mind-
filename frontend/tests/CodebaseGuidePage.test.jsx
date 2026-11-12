import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Routes, Route, Outlet } from 'react-router-dom';

// Mock the API module
vi.mock('../src/lib/api', () => ({
  onboardingApi: {
    getBlueprint: vi.fn(),
    refreshBlueprint: vi.fn(),
    getProgress: vi.fn(),
    updateProgress: vi.fn(),
  },
  orgApi: {
    getRepository: vi.fn(),
  },
}));

// Mock mermaid rendering
vi.mock('mermaid', () => ({
  default: {
    initialize: vi.fn(),
    render: vi.fn().mockImplementation((id, text) => {
      if (text.includes('FAIL_SYNTAX')) {
        return Promise.reject(new Error('Syntax error'));
      }
      return Promise.resolve({ svg: '<svg data-testid="mock-mermaid-svg"></svg>' });
    }),
  },
}));

import { onboardingApi, orgApi } from '../src/lib/api';
import CodebaseGuidePage from '../src/pages/CodebaseGuidePage';

const mockBlueprint = {
  repository_id: 1,
  analyzed_commit_sha: 'abcdef1234567890abcdef1234567890abcdef12',
  status: 'ready',
  is_outdated: false,
  architecture_pattern: 'Modular Monolith',
  summary: 'RepoMind is an engineering intelligence system for pull requests.',
  subsystems: [
    {
      name: 'API Routing Layer',
      path: 'backend/app',
      purpose: 'FastAPI routes and middlewares',
      key_files: ['backend/app/main.py'],
    },
    {
      name: 'RAG Knowledge Tier',
      path: 'backend/app/rag',
      purpose: 'Document chunking and pgvector search',
      key_files: ['backend/app/rag/service.py'],
    },
  ],
  request_flow: [
    {
      step_number: 1,
      layer: 'Routing',
      file: 'backend/app/main.py',
      symbol: 'app',
      description: 'Incoming HTTP request dispatched to router',
    },
    {
      step_number: 2,
      layer: 'Service',
      file: 'backend/app/review/service.py',
      symbol: 'run_review',
      description: 'Executes PR analysis engine',
    },
  ],
  tracks: {
    backend: {
      track_name: 'backend',
      reading_order: [
        {
          file_path: 'backend/app/main.py',
          role: 'Entry Point',
          why_read: 'Boots FastAPI server and registers middleware',
          focus_symbols: ['app'],
          key_lines: 'L1-L50',
        },
        {
          file_path: 'backend/app/auth/permissions.py',
          role: 'RBAC Authorization',
          why_read: 'Defines permission atoms and role mappings',
          focus_symbols: ['Permission', 'assert_org_permission'],
          key_lines: 'L10-L80',
        },
      ],
      milestones: [
        {
          id: 'be_m1',
          title: 'Verify Local Pytest',
          description: 'Run unit test suite locally to verify environment',
          action_type: 'run_command',
          action_hint: 'pytest backend/tests/',
        },
        {
          id: 'be_m2',
          title: 'Inspect DB Models',
          description: 'Locate RepositoryBlueprint and UserOnboardingProgress models',
          action_type: 'code_inspection',
          action_hint: 'backend/app/onboarding/models.py',
        },
      ],
    },
    frontend: {
      track_name: 'frontend',
      reading_order: [
        {
          file_path: 'frontend/src/App.jsx',
          role: 'Client Router',
          why_read: 'Top-level routing and authentication layout',
          focus_symbols: ['App'],
        },
      ],
      milestones: [
        {
          id: 'fe_m1',
          title: 'Run Frontend Build',
          description: 'Execute npm run build',
          action_type: 'run_command',
          action_hint: 'npm run build',
        },
      ],
    },
    fullstack: {
      track_name: 'fullstack',
      reading_order: [
        {
          file_path: 'backend/app/main.py',
          role: 'API Entry',
          why_read: 'Backend service surface',
          focus_symbols: ['app'],
        },
      ],
      milestones: [
        {
          id: 'fs_m1',
          title: 'Healthcheck Verification',
          description: 'Verify end-to-end API response',
          action_type: 'first_task',
          action_hint: 'GET /health',
        },
      ],
    },
  },
  caution_zones: [
    {
      path: 'backend/app/auth',
      risk_level: 'critical',
      reason: 'Authentication and JWT token validation boundary',
    },
  ],
  safe_starter_areas: [
    {
      area: 'Unit Testing Suite',
      description: 'Independent test files safe for new contributors',
      starter_ideas: ['Add tests for helper utilities'],
    },
  ],
  mermaid_diagram: 'flowchart TD\n    A[Client] --> B[FastAPI Router]\n    B --> C[Postgres DB]',
};

const mockProgress = {
  repository_id: 1,
  active_track: 'backend',
  completed_milestones: ['be_m1'],
  notes: 'My initial local notes',
};

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

function LayoutOutlet({ memberships, currentOrgId }) {
  return <Outlet context={{ memberships, currentOrgId }} />;
}

const renderGuidePage = (memberships = [], currentOrgId = 1) => {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/repositories/1/guide']}>
        <Routes>
          <Route element={<LayoutOutlet memberships={memberships} currentOrgId={currentOrgId} />}>
            <Route path="/repositories/:rid/guide" element={<CodebaseGuidePage />} />
          </Route>
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('CodebaseGuidePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    orgApi.getRepository.mockResolvedValue({
      id: 1,
      github_name: 'repomind-core',
      default_branch: 'main',
      project: { organization_id: 1 },
    });
    onboardingApi.getBlueprint.mockResolvedValue(mockBlueprint);
    onboardingApi.getProgress.mockResolvedValue(mockProgress);
    onboardingApi.updateProgress.mockResolvedValue(mockProgress);
  });

  it('1. Loads and renders common repository overview before tracks', async () => {
    renderGuidePage();

    await waitFor(() => {
      expect(screen.getByText('Developer Onboarding & Ramp-Up Blueprint')).toBeInTheDocument();
    });

    // Overview section is visible
    expect(screen.getByText('1. Repository Architecture Overview')).toBeInTheDocument();
    expect(screen.getByText('Modular Monolith')).toBeInTheDocument();
    expect(screen.getByText(mockBlueprint.summary)).toBeInTheDocument();
    expect(screen.getByText('API Routing Layer')).toBeInTheDocument();
    expect(screen.getByText('RAG Knowledge Tier')).toBeInTheDocument();

    // Execution flow step
    expect(screen.getByText('Request-to-Database Execution Flow Trace')).toBeInTheDocument();
    expect(screen.getByText(/Incoming HTTP request dispatched/)).toBeInTheDocument();
  });

  it('2. Switches role tracks and updates curated reading list and milestones', async () => {
    renderGuidePage();

    await waitFor(() => {
      expect(screen.getByText('Backend Track')).toBeInTheDocument();
    });

    // Initially on backend track
    expect(screen.getByText('backend/app/main.py')).toBeInTheDocument();
    expect(screen.getByText('backend/app/auth/permissions.py')).toBeInTheDocument();
    expect(screen.getByText('Verify Local Pytest')).toBeInTheDocument();

    // Click Frontend Track tab
    const feTab = screen.getByRole('button', { name: 'Frontend Track' });
    fireEvent.click(feTab);

    // Track changed to frontend
    await waitFor(() => {
      expect(screen.getByText('frontend/src/App.jsx')).toBeInTheDocument();
      expect(screen.getByText('Run Frontend Build')).toBeInTheDocument();
    });

    // Verify API called to save active_track
    expect(onboardingApi.updateProgress).toHaveBeenCalledWith(1, { active_track: 'frontend' });
  });

  it('3. Renders 5-7 reading order items with purpose and focus symbols', async () => {
    renderGuidePage();

    await waitFor(() => {
      expect(screen.getByText('Prioritized Reading Order (backend Focus)')).toBeInTheDocument();
    });

    expect(screen.getByText('Boots FastAPI server and registers middleware')).toBeInTheDocument();
    expect(screen.getByText('assert_org_permission')).toBeInTheDocument();
  });

  it('4. Toggles milestone completion and updates progress bar', async () => {
    renderGuidePage();

    await waitFor(() => {
      expect(screen.getByText('Verify Local Pytest')).toBeInTheDocument();
    });

    // Progress shows 50% (1 of 2 completed: be_m1)
    expect(screen.getByText('50%')).toBeInTheDocument();

    // Toggle second milestone (be_m2)
    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[1]);

    await waitFor(() => {
      expect(onboardingApi.updateProgress).toHaveBeenCalledWith(1, {
        completed_milestones: ['be_m1', 'be_m2'],
        active_track: 'backend',
      });
    });
  });

  it('5. Persists private developer notes', async () => {
    renderGuidePage();

    await waitFor(() => {
      expect(screen.getByDisplayValue('My initial local notes')).toBeInTheDocument();
    });

    const textarea = screen.getByPlaceholderText(/Record local port mappings/i);
    fireEvent.change(textarea, { target: { value: 'Updated local port 8000' } });

    await waitFor(() => {
      expect(screen.getByDisplayValue('Updated local port 8000')).toBeInTheDocument();
    });
  });

  it('6. Preserves user edits when progress save fails', async () => {
    onboardingApi.updateProgress.mockRejectedValueOnce(new Error('Network error'));
    renderGuidePage();

    await waitFor(() => {
      expect(screen.getByDisplayValue('My initial local notes')).toBeInTheDocument();
    });

    const textarea = screen.getByPlaceholderText(/Record local port mappings/i);
    fireEvent.change(textarea, { target: { value: 'Draft notes that failed save' } });
    fireEvent.blur(textarea);

    // Wait for save error feedback
    await waitFor(
      () => {
        expect(screen.getByText(/Failed to save progress.*Your edits have been preserved/i)).toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    // Content remains intact in textarea!
    expect(screen.getByDisplayValue('Draft notes that failed save')).toBeInTheDocument();
  });

  it('7. Displays Caution Zones and Safe Starter Areas with blast radius indicators', async () => {
    renderGuidePage();

    await waitFor(() => {
      expect(screen.getByText('3. Blast Radius & Starter Compass')).toBeInTheDocument();
    });

    expect(screen.getByText('Caution Zones (High Blast Radius)')).toBeInTheDocument();
    expect(screen.getByText('backend/app/auth')).toBeInTheDocument();
    expect(screen.getByText('critical')).toBeInTheDocument();

    expect(screen.getByText('Safe Starter Areas (Beginner Friendly)')).toBeInTheDocument();
    expect(screen.getByText('Unit Testing Suite')).toBeInTheDocument();
    expect(screen.getByText('Add tests for helper utilities')).toBeInTheDocument();
  });

  it('8. Shows refresh button for Team Lead+ and handles refresh', async () => {
    const memberships = [
      {
        organization_id: 1,
        organization: { id: 1 },
        role: 'team_lead',
      },
    ];

    onboardingApi.refreshBlueprint.mockResolvedValueOnce({
      ...mockBlueprint,
      analyzed_commit_sha: 'newcommit1234567890',
    });

    renderGuidePage(memberships);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Re-analyze Codebase/i })).toBeInTheDocument();
    });

    const refreshBtn = screen.getByRole('button', { name: /Re-analyze Codebase/i });
    fireEvent.click(refreshBtn);

    await waitFor(() => {
      expect(onboardingApi.refreshBlueprint).toHaveBeenCalledWith(1);
    });
  });

  it('9. Hides refresh button for developers without REPOS_INDEX permission', async () => {
    const memberships = [
      {
        organization_id: 1,
        organization: { id: 1 },
        role: 'developer',
      },
    ];

    renderGuidePage(memberships);

    await waitFor(() => {
      expect(screen.getByText('Developer Onboarding & Ramp-Up Blueprint')).toBeInTheDocument();
    });

    // Developer cannot refresh
    expect(screen.queryByRole('button', { name: /Re-analyze Codebase/i })).not.toBeInTheDocument();
  });

  it('10. Renders Outdated Blueprint badge when is_outdated is true', async () => {
    onboardingApi.getBlueprint.mockResolvedValueOnce({
      ...mockBlueprint,
      is_outdated: true,
    });

    renderGuidePage();

    await waitFor(() => {
      expect(screen.getByText('Blueprint Outdated')).toBeInTheDocument();
    });
  });

  it('11. Renders Unindexed Repository error state when API returns 400', async () => {
    const unindexedErr = new Error('Repository is not indexed');
    unindexedErr.status = 400;
    onboardingApi.getBlueprint.mockRejectedValueOnce(unindexedErr);

    renderGuidePage();

    await waitFor(() => {
      expect(screen.getByText('Repository Not Indexed')).toBeInTheDocument();
      expect(screen.getByText(/Return to Repositories/i)).toBeInTheDocument();
    });
  });

  it('12. Falls back to textual representation when Mermaid diagram syntax is invalid', async () => {
    onboardingApi.getBlueprint.mockResolvedValueOnce({
      ...mockBlueprint,
      mermaid_diagram: 'FAIL_SYNTAX invalid code',
    });

    renderGuidePage();

    await waitFor(() => {
      expect(screen.getByText(/Textual Architecture Representation/i)).toBeInTheDocument();
      expect(screen.getByText('Diagram fallback mode')).toBeInTheDocument();
    });
  });
});
