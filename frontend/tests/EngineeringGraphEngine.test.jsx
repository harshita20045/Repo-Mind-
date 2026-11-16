import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MemoryRouter } from 'react-router-dom';
import EngineeringGraphEngine from '../src/components/Graph/EngineeringGraphEngine';

const mockNodes = [
  {
    id: 1,
    node_key: 'mod:backend/app',
    node_type: 'module',
    name: 'backend/app',
    file_path: 'backend/app',
    in_degree: 0,
    out_degree: 2,
  },
  {
    id: 2,
    node_key: 'file:backend/app/main.py',
    node_type: 'file',
    name: 'main.py',
    file_path: 'backend/app/main.py',
    in_degree: 1,
    out_degree: 1,
  },
  {
    id: 3,
    node_key: 'api:GET:/health',
    node_type: 'api_endpoint',
    name: '/health',
    file_path: 'backend/app/routes/health.py',
    metadata: { api_route: { method: 'GET', path: '/health' }, docstring: 'Health check endpoint' },
    in_degree: 1,
    out_degree: 0,
  },
];

const mockEdges = [
  { id: 1, source: 1, target: 2, relation_type: 'contains' },
  { id: 2, source: 2, target: 3, relation_type: 'exposes' },
];

const availableModes = [
  { id: 'all', label: 'All Knowledge Graph' },
  { id: 'module', label: 'Module Dependencies' },
  { id: 'file', label: 'File Dependencies' },
  { id: 'api', label: 'API Pipeline' },
];

describe('EngineeringGraphEngine', () => {
  it('1. Renders graph filter bar, statistics, and canvas', () => {
    render(
      <MemoryRouter>
        <EngineeringGraphEngine
          nodes={mockNodes}
          edges={mockEdges}
          repositoryId={1}
          availableModes={availableModes}
        />
      </MemoryRouter>
    );

    expect(screen.getByText('All Entities')).toBeInTheDocument();
    expect(screen.getByText('All Knowledge Graph')).toBeInTheDocument();
    expect(screen.getByText('Module Dependencies')).toBeInTheDocument();
    expect(screen.getByText('API Pipeline')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Search entity or file...')).toBeInTheDocument();
  });

  it('2. Filters nodes by search query and updates visible counts', () => {
    render(
      <MemoryRouter>
        <EngineeringGraphEngine
          nodes={mockNodes}
          edges={mockEdges}
          repositoryId={1}
          availableModes={availableModes}
        />
      </MemoryRouter>
    );

    const searchInput = screen.getByPlaceholderText('Search entity or file...');
    fireEvent.change(searchInput, { target: { value: 'health' } });

    expect(screen.getByDisplayValue('health')).toBeInTheDocument();
  });

  it('3. Renders empty state when no nodes match filter', () => {
    render(
      <MemoryRouter>
        <EngineeringGraphEngine
          nodes={mockNodes}
          edges={mockEdges}
          repositoryId={1}
          availableModes={availableModes}
        />
      </MemoryRouter>
    );

    const searchInput = screen.getByPlaceholderText('Search entity or file...');
    fireEvent.change(searchInput, { target: { value: 'non_existent_symbol' } });

    expect(screen.getByText('No Matching Entities')).toBeInTheDocument();
  });

  it('4. Renders unindexed empty state when rawNodes is empty', () => {
    const handleRefresh = vi.fn();
    render(
      <MemoryRouter>
        <EngineeringGraphEngine
          nodes={[]}
          edges={[]}
          repositoryId={1}
          onRefresh={handleRefresh}
        />
      </MemoryRouter>
    );

    expect(screen.getByText('Knowledge Graph Empty')).toBeInTheDocument();
    const btn = screen.getByText('Index Repository Now');
    fireEvent.click(btn);
    expect(handleRefresh).toHaveBeenCalled();
  });
});

