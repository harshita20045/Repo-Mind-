import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ChangeImpactDashboard from '../src/components/Impact/ChangeImpactDashboard';

// Mock MermaidViewer to avoid canvas/svg rendering dependencies in JSDOM
vi.mock('../src/components/Onboarding/MermaidViewer', () => ({
  default: ({ chart }) => <div data-testid="mermaid-viewer">{chart}</div>,
}));

describe('ChangeImpactDashboard Component Suite', () => {
  const mockImpactData = {
    id: 10,
    repository_id: 1,
    pull_request_id: 42,
    risk_level: 'high',
    directly_affected_count: 2,
    indirectly_affected_count: 3,
    breaking_changes_count: 1,
    summary: 'High blast radius: 5 total downstream dependents affected, 1 breaking change detected.',
    affected_components: [
      {
        component_name: 'process_payment',
        file_path: 'backend/app/payments/service.py',
        node_type: 'function',
        impact_tier: 'directly_affected',
        severity: 'critical',
        relationship: 'calls modified symbol checkout()',
        reason: 'Signature parameter added without default.',
        suggested_verification: 'Verify caller arguments in test_payments.py',
        evidence: 'checkout(user_id, cart, new_required_param)',
      },
      {
        component_name: 'generate_invoice',
        file_path: 'backend/app/billing/invoice.py',
        node_type: 'function',
        impact_tier: 'indirectly_affected',
        severity: 'high',
        relationship: 'transitive caller of process_payment',
        reason: 'Exposed to downstream payment schema change.',
        suggested_verification: 'Run billing integration tests.',
        evidence: 'Calls process_payment()',
      },
      {
        component_name: 'send_receipt_email',
        file_path: 'backend/app/notifications/mailer.py',
        node_type: 'service',
        impact_tier: 'potentially_affected',
        severity: 'medium',
        relationship: 'event listener on payment_success',
        reason: 'Event payload fields may vary.',
        suggested_verification: 'Check email templates.',
      },
    ],
    breaking_changes: [
      {
        component_name: 'checkout',
        file_path: 'backend/app/payments/checkout.py',
        line_number: 45,
        change_type: 'signature_mutation',
        severity: 'critical',
        description: "New parameter 'currency_code' added without default value.",
        evidence: '+def checkout(user_id, cart, currency_code):',
        suggested_fix: "Provide default value 'USD' or make optional with None.",
      },
    ],
    test_recommendations: [
      {
        target_component: 'process_payment',
        target_file: 'backend/app/payments/service.py',
        recommended_test_file: 'tests/test_payments.py',
        test_type: 'unit',
        priority: 'P0',
        reason: 'Direct dependent of modified signature.',
        command: 'pytest backend/tests/test_payments.py',
      },
    ],
    graph_visualization: {
      nodes: [
        { id: 'checkout', name: 'checkout', type: 'function', impact_tier: 'changed', file_path: 'backend/app/payments/checkout.py' },
        { id: 'process_payment', name: 'process_payment', type: 'function', impact_tier: 'directly_affected', file_path: 'backend/app/payments/service.py' },
      ],
      edges: [
        { source: 'process_payment', target: 'checkout', relationship: 'calls' },
      ],
      mermaid: 'flowchart LR\n    N0["checkout (function)"]:::changed\n    N1["process_payment (function)"]:::direct\n    N1 -->|calls| N0',
    },
  };

  test('renders empty state when no impact data is provided', () => {
    render(<ChangeImpactDashboard impactData={null} repositoryId={1} pullRequestId={42} />);
    expect(screen.getByText('No Change Impact Data')).toBeInTheDocument();
  });

  test('renders overview with risk level and metric counts', () => {
    render(<ChangeImpactDashboard impactData={mockImpactData} repositoryId={1} pullRequestId={42} />);
    expect(screen.getByText('Change Impact & Blast Radius Analysis')).toBeInTheDocument();
    expect(screen.getByRole('status', { name: /Risk level: high/i })).toBeInTheDocument();
    expect(screen.getByText('Directly Affected')).toBeInTheDocument();
    expect(screen.getByText('Indirectly Affected')).toBeInTheDocument();
    expect(screen.getAllByText('Breaking Changes').length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Recommended Tests/i).length).toBeGreaterThan(0);
  });

  test('renders breaking changes list with alert and suggested fix', () => {
    render(<ChangeImpactDashboard impactData={mockImpactData} repositoryId={1} pullRequestId={42} />);
    
    // Breaking changes are rendered in overview banner when present
    expect(screen.getByText(/New parameter 'currency_code' added without default value/i)).toBeInTheDocument();
    expect(screen.getByText(/Provide default value 'USD' or make optional with None/i)).toBeInTheDocument();
  });

  test('switches to affected components tab, filters by tier and searches', () => {
    render(<ChangeImpactDashboard impactData={mockImpactData} repositoryId={1} pullRequestId={42} />);

    // Click "Affected Components" sub-tab
    const affectedTab = screen.getByRole('button', { name: /Affected Components/i });
    fireEvent.click(affectedTab);

    // Initial state shows all 3 components
    expect(screen.getByText('process_payment')).toBeInTheDocument();
    expect(screen.getByText('generate_invoice')).toBeInTheDocument();
    expect(screen.getByText('send_receipt_email')).toBeInTheDocument();

    // Filter by "Direct" tier
    const directFilter = screen.getByRole('button', { name: /^Direct \(/i });
    fireEvent.click(directFilter);

    expect(screen.getByText('process_payment')).toBeInTheDocument();
    expect(screen.queryByText('generate_invoice')).not.toBeInTheDocument();
    expect(screen.queryByText('send_receipt_email')).not.toBeInTheDocument();

    // Reset to "All" and search by query
    const allFilter = screen.getByRole('button', { name: /^All \(/i });
    fireEvent.click(allFilter);

    const searchInput = screen.getByPlaceholderText(/Search component or file/i);
    fireEvent.change(searchInput, { target: { value: 'invoice' } });

    expect(screen.queryByText('process_payment')).not.toBeInTheDocument();
    expect(screen.getByText('generate_invoice')).toBeInTheDocument();
  });

  test('switches to recommended tests and shows CLI command', () => {
    // Mock navigator.clipboard
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(),
      },
    });

    render(<ChangeImpactDashboard impactData={mockImpactData} repositoryId={1} pullRequestId={42} />);

    const testsTab = screen.getByRole('button', { name: /Recommended Tests/i });
    fireEvent.click(testsTab);

    expect(screen.getByText('P0 - Critical Path')).toBeInTheDocument();
    expect(screen.getByText('pytest backend/tests/test_payments.py')).toBeInTheDocument();

    const copyBtn = screen.getByRole('button', { name: /Copy Command/i });
    fireEvent.click(copyBtn);

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('pytest backend/tests/test_payments.py');
  });

  test('switches to dependency graph and toggles nodes view', () => {
    render(<ChangeImpactDashboard impactData={mockImpactData} repositoryId={1} pullRequestId={42} />);

    const graphTab = screen.getByRole('button', { name: /Dependency Graph/i });
    fireEvent.click(graphTab);

    expect(screen.getByTestId('mermaid-viewer')).toBeInTheDocument();

    // Toggle to Nodes list view
    const nodesToggle = screen.getByRole('button', { name: /Nodes \(2\)/i });
    fireEvent.click(nodesToggle);

    expect(screen.getByText('backend/app/payments/checkout.py')).toBeInTheDocument();
    expect(screen.getByText('backend/app/payments/service.py')).toBeInTheDocument();
  });
});
