import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ArchitectureDashboard from '../src/components/Architecture/ArchitectureDashboard';

// Mock MermaidViewer
vi.mock('../src/components/Onboarding/MermaidViewer', () => ({
  default: ({ chart }) => <div data-testid="mock-mermaid">{chart}</div>,
}));

// Mock architecture API
vi.mock('../src/lib/api', () => ({
  architectureApi: {
    getLatestAnalysis: vi.fn(),
    triggerAnalysis: vi.fn(),
    getRules: vi.fn(),
    createRule: vi.fn(),
    updateRule: vi.fn(),
    deleteRule: vi.fn(),
    resetRules: vi.fn(),
    getCircularDependencies: vi.fn(),
    getFlows: vi.fn(),
  },
}));

import { architectureApi } from '../src/lib/api';

const mockAnalysis = {
  id: 10,
  repository_id: 1,
  health_score: 75,
  inferred_pattern: 'layered_mvc',
  pattern_confidence: 0.92,
  total_violations: 2,
  critical_violations: 1,
  circular_dependency_count: 1,
  layer_summary: {
    presentation: { file_count: 5 },
    business_logic: { file_count: 8 },
    data_access: { file_count: 4 },
  },
  mermaid_diagram: 'flowchart TD\n    Presentation --> BusinessLogic',
  violations: [
    {
      id: 101,
      rule_code: 'ARCH-001',
      rule_id: 1,
      violation_type: 'api_db_isolation',
      severity: 'critical',
      title: 'Controller Directly Accessing Database Model',
      explanation: "Route handler 'routes/orders.py' directly imports and queries 'Order' model.",
      suggested_correction: 'Delegate query to OrderService.',
      source_file: 'backend/app/api/orders.py',
      source_line: 25,
      target_file: 'backend/app/models/order.py',
      evidence: 'from backend.app.models.order import Order',
    },
    {
      id: 102,
      rule_code: 'ARCH-004',
      rule_id: 4,
      violation_type: 'forbidden_dependency',
      severity: 'high',
      title: 'Utility Importing Business Service',
      explanation: "Helper 'utils/exporter.py' imports 'PaymentService'.",
      suggested_correction: 'Pass data payload as parameter.',
      source_file: 'backend/app/utils/exporter.py',
      source_line: 12,
      target_file: 'backend/app/services/payment.py',
      evidence: 'from backend.app.services.payment import PaymentService',
    },
  ],
};

const mockRules = [
  {
    id: 1,
    repository_id: 1,
    rule_code: 'ARCH-001',
    name: 'Controllers Must Not Directly Access Database Models',
    description: 'API controllers must delegate through services.',
    rule_type: 'api_db_isolation',
    source_layer: 'presentation',
    target_layer: 'data_access',
    severity: 'critical',
    is_enabled: true,
    is_system_inferred: true,
  },
  {
    id: 2,
    repository_id: 1,
    rule_code: 'CUSTOM-001',
    name: 'Strict Domain Isolation',
    description: 'Domain layer must remain pure.',
    rule_type: 'layer_boundary',
    source_layer: 'domain',
    target_layer: 'infrastructure',
    severity: 'high',
    is_enabled: false,
    is_system_inferred: false,
  },
];

const mockCircular = [
  {
    cycle_path: ['backend/app/auth.py', 'backend/app/user.py', 'backend/app/auth.py'],
    length: 2,
    participating_files: ['backend/app/auth.py', 'backend/app/user.py'],
    severity: 'critical',
    title: 'Direct circular dependency: backend/app/auth.py <-> backend/app/user.py',
    explanation: 'Mutually recursive imports cause runtime initialization hazards.',
    decoupling_recommendation: 'Extract common credentials to a shared types module.',
  },
];

const mockFlows = [
  {
    endpoint_name: 'GET /orders',
    endpoint_path: '/orders',
    route_file: 'backend/app/api/orders.py',
    service_name: 'OrderService',
    service_file: 'backend/app/orders/service.py',
    model_name: 'Order',
    model_file: 'backend/app/models/order.py',
    is_leaky: false,
    evidence: 'Route -> OrderService -> Order',
  },
  {
    endpoint_name: 'POST /checkout',
    endpoint_path: '/checkout',
    route_file: 'backend/app/api/checkout.py',
    is_leaky: true,
    model_name: 'Order',
    evidence: 'Route directly queries Order table',
    suggested_fix: 'Move query into checkout service',
  },
];

function renderDashboard(repoId = 1) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <ArchitectureDashboard repositoryId={repoId} />
    </QueryClientProvider>
  );
}

describe('ArchitectureDashboard Component Suite', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    architectureApi.getLatestAnalysis.mockResolvedValue(mockAnalysis);
    architectureApi.getRules.mockResolvedValue(mockRules);
    architectureApi.getCircularDependencies.mockResolvedValue(mockCircular);
    architectureApi.getFlows.mockResolvedValue(mockFlows);
  });

  it('1. Renders health score gauge, inferred pattern, and metric counts', async () => {
    renderDashboard(1);

    await waitFor(() => {
      expect(screen.getByText('75')).toBeInTheDocument();
      expect(screen.getByText('layered mvc')).toBeInTheDocument();
      expect(screen.getByText('92% Confidence')).toBeInTheDocument();
      expect(screen.getByText('Total Violations')).toBeInTheDocument();
      expect(screen.getByText('Critical Violations')).toBeInTheDocument();
      expect(screen.getAllByText('Circular Dependencies').length).toBeGreaterThanOrEqual(1);
    });
  });

  it('2. Switches to Rule Violations tab and filters by severity', async () => {
    renderDashboard(1);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Rule Violations/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Rule Violations/i }));

    await waitFor(() => {
      expect(screen.getByText('ARCH-001')).toBeInTheDocument();
      expect(screen.getByText('Controller Directly Accessing Database Model')).toBeInTheDocument();
      expect(screen.getByText('ARCH-004')).toBeInTheDocument();
    });

    // Filter by critical
    const critBtn = screen.getByRole('button', { name: /^Critical \(/i });
    fireEvent.click(critBtn);

    expect(screen.getByText('ARCH-001')).toBeInTheDocument();
    expect(screen.queryByText('ARCH-004')).not.toBeInTheDocument();
  });

  it('3. Switches to Circular Dependencies tab and displays cycle loop', async () => {
    renderDashboard(1);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Circular Dependencies/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Circular Dependencies/i }));

    await waitFor(() => {
      expect(screen.getByText(/Direct circular dependency/i)).toBeInTheDocument();
      expect(screen.getByText('Extract common credentials to a shared types module.')).toBeInTheDocument();
      expect(screen.getAllByText('backend/app/auth.py').length).toBeGreaterThanOrEqual(1);
    });
  });

  it('4. Switches to Execution Flows tab and highlights leaky bypass', async () => {
    renderDashboard(1);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Execution Flows/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Execution Flows/i }));

    await waitFor(() => {
      expect(screen.getByText('GET /orders')).toBeInTheDocument();
      expect(screen.getByText('Clean Flow')).toBeInTheDocument();
      expect(screen.getAllByText('POST /checkout').length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('Direct DB Access')).toBeInTheDocument();
    });
  });

  it('5. Switches to Rule Governance tab, opens modal, and adds custom rule', async () => {
    architectureApi.createRule.mockResolvedValueOnce({
      id: 3,
      repository_id: 1,
      rule_code: 'NEW-001',
      name: 'Frontend Secret Shield',
      rule_type: 'forbidden_dependency',
      severity: 'critical',
      is_enabled: true,
      is_system_inferred: false,
    });

    renderDashboard(1);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Rule Governance/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Rule Governance/i }));

    await waitFor(() => {
      expect(screen.getByText('Controllers Must Not Directly Access Database Models')).toBeInTheDocument();
      expect(screen.getByText('Strict Domain Isolation')).toBeInTheDocument();
    });

    // Click "+ Add Custom Rule"
    const addBtn = screen.getByRole('button', { name: /\+ Add Custom Rule/i });
    fireEvent.click(addBtn);

    expect(screen.getByText('Create Custom Architecture Rule')).toBeInTheDocument();

    const codeInput = screen.getByLabelText(/Rule Code/i);
    const nameInput = screen.getByLabelText(/Rule Name/i);

    fireEvent.change(codeInput, { target: { value: 'NEW-001' } });
    fireEvent.change(nameInput, { target: { value: 'Frontend Secret Shield' } });

    const saveBtn = screen.getByRole('button', { name: /Save Rule/i });
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(architectureApi.createRule).toHaveBeenCalledWith(
        1,
        expect.objectContaining({
          rule_code: 'NEW-001',
          name: 'Frontend Secret Shield',
        })
      );
    });
  });
});
