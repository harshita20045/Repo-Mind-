import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

// Mock the API module
vi.mock('../src/lib/api', () => ({
  intelligenceApi: {
    getSummary: vi.fn(),
    getGraph: vi.fn(),
    getArchitectureDiagram: vi.fn(),
    getDependencies: vi.fn(),
    getSymbols: vi.fn(),
    triggerIndex: vi.fn(),
  },
  architectureApi: {
    getLatestAnalysis: vi.fn().mockResolvedValue({
      id: 1,
      health_score: 95,
      inferred_pattern: 'layered_mvc',
      pattern_confidence: 0.95,
      total_violations: 0,
      critical_violations: 0,
      circular_dependency_count: 0,
      layer_summary: {},
      violations: [],
      mermaid_diagram: 'flowchart TD\n    API --> Service',
    }),
    triggerAnalysis: vi.fn().mockResolvedValue({}),
    getRules: vi.fn().mockResolvedValue([]),
    createRule: vi.fn().mockResolvedValue({}),
    updateRule: vi.fn().mockResolvedValue({}),
    deleteRule: vi.fn().mockResolvedValue({}),
    resetRules: vi.fn().mockResolvedValue([]),
    getCircularDependencies: vi.fn().mockResolvedValue([]),
    getFlows: vi.fn().mockResolvedValue([]),
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
      return Promise.resolve({ svg: '<svg data-testid="mock-mermaid-svg"></svg>' });
    }),
  },
}));

import { intelligenceApi, orgApi } from '../src/lib/api';
import RepositoryTopologyPage from '../src/pages/RepositoryTopologyPage';

const mockRepo = {
  id: 1,
  github_owner: 'repomind-org',
  github_name: 'repomind-core',
  default_branch: 'main',
  index_status: 'indexed',
};

const mockSummary = {
  repository_id: 1,
  primary_language: 'Python',
  frameworks: ['FastAPI', 'React', 'SQLAlchemy'],
  entry_points: ['backend/main.py', 'frontend/src/main.jsx'],
  stats: {
    nodes_count: 42,
    edges_count: 85,
    dependencies_count: 12,
  },
  architecture_summary: 'Modular Monolith with FastAPI and React.',
  mermaid_diagram: 'flowchart TD\n    API --> DB',
  scanned_commit_sha: 'commit_sha_123',
};

const mockDependencies = [
  { ecosystem: 'pypi', package_name: 'fastapi', version_spec: '>=0.115.0', is_dev: false, file_path: 'requirements.txt' },
  { ecosystem: 'npm', package_name: 'react', version_spec: '^18.2.0', is_dev: false, file_path: 'package.json' },
];

const mockSymbols = [
  { name: 'User', symbol_type: 'db_model', file_path: 'backend/models.py', start_line: 10, end_line: 25, signature: 'class User(Base)', docstring: 'User model' },
  { name: 'login_user', symbol_type: 'api_endpoint', file_path: 'backend/routes.py', start_line: 30, end_line: 45, signature: 'def login_user()' },
];

const mockGraph = {
  nodes: [
    { id: 1, node_key: 'file:backend/main.py', node_type: 'file', name: 'main.py', file_path: 'backend/main.py' },
    { id: 2, node_key: 'api:GET:/health', node_type: 'api_endpoint', name: '/health', file_path: 'backend/main.py' },
  ],
  edges: [
    { id: 1, source_node_id: 1, target_node_id: 2, relation_type: 'exposes' },
  ],
  total_nodes: 2,
  total_edges: 1,
};

function renderTopologyPage(repoId = '1') {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/repositories/${repoId}/topology`]}>
        <Routes>
          <Route path="/repositories/:rid/topology" element={<RepositoryTopologyPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('RepositoryTopologyPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    orgApi.getRepository.mockResolvedValue(mockRepo);
    intelligenceApi.getSummary.mockResolvedValue(mockSummary);
    intelligenceApi.getDependencies.mockResolvedValue(mockDependencies);
    intelligenceApi.getSymbols.mockResolvedValue(mockSymbols);
    intelligenceApi.getGraph.mockResolvedValue(mockGraph);
  });

  it('1. Renders repository overview, primary language, and frameworks', async () => {
    renderTopologyPage('1');

    await waitFor(() => {
      expect(screen.getByText('repomind-core')).toBeInTheDocument();
      expect(screen.getByText('Python')).toBeInTheDocument();
      expect(screen.getAllByText('FastAPI').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('React').length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('42')).toBeInTheDocument(); // Symbols count
    });
  });

  it('2. Switches to Symbols tab and displays indexed symbols', async () => {
    renderTopologyPage('1');

    await waitFor(() => {
      expect(screen.getByText('Symbols & Methods')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Symbols & Methods'));

    await waitFor(() => {
      expect(screen.getByText('User')).toBeInTheDocument();
      expect(screen.getByText('db_model')).toBeInTheDocument();
      expect(screen.getByText('login_user')).toBeInTheDocument();
    });
  });

  it('3. Switches to Package Dependencies tab and renders package catalog', async () => {
    renderTopologyPage('1');

    await waitFor(() => {
      expect(screen.getByText(/Package Dependencies/)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText(/Package Dependencies/));

    await waitFor(() => {
      expect(screen.getByText('fastapi')).toBeInTheDocument();
      expect(screen.getByText('>=0.115.0')).toBeInTheDocument();
    });
  });
});
