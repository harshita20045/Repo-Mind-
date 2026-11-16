import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import TestIntelligenceDashboard from '../src/components/Testing/TestIntelligenceDashboard';

// Mock testing API
vi.mock('../src/lib/api', () => ({
  testingApi: {
    getTestDashboard: vi.fn(),
    generateTestCase: vi.fn(),
    executeGeneratedTest: vi.fn(),
    triggerTestAnalysis: vi.fn(),
  },
}));

import { testingApi } from '../src/lib/api';

const mockDashboardData = {
  repository_id: 1,
  pull_request_id: 10,
  review_run_id: null,
  total_scenarios_count: 8,
  coverage_gaps_count: 6,
  generated_tests_count: 1,
  passed_tests_count: 1,
  failed_tests_count: 0,
  pending_tests_count: 0,
  category_counts: {
    positive: 1,
    negative: 1,
    boundary: 1,
    validation: 1,
    authentication: 1,
    authorization: 1,
    integration: 1,
    regression: 1,
  },
  scenarios: [
    {
      id: 101,
      repository_id: 1,
      pull_request_id: 10,
      target_file: 'backend/app/auth/service.py',
      target_symbol: 'authenticate_user',
      category: 'positive',
      title: "Verify happy-path execution of 'authenticate_user'",
      description: "Validate authenticate_user executes successfully with nominal inputs.",
      edge_case_notes: 'Ensure valid credentials return user payload.',
      suggested_assertions: ['User is not None', 'Status is active'],
      existing_test_file: 'backend/tests/test_auth.py',
      coverage_gap: false,
      impacted_endpoints: ['backend/app/auth/routes.py:login_route'],
      impacted_services: ['backend/app/auth/tokens.py'],
      priority: 'high',
      created_at: '2026-11-16T10:00:00Z',
      generated_tests: [
        {
          id: 501,
          test_scenario_id: 101,
          language: 'python',
          framework: 'pytest',
          test_file_path: 'backend/tests/test_auth.py',
          test_code: 'def test_auth_nominal(): assert True',
          execution_status: 'passed',
          execution_result: {
            returncode: 0,
            duration_ms: 12.5,
            assertions_passed: 1,
            assertions_failed: 0,
          },
          security_reviewed: true,
          executed_at: '2026-11-16T10:05:00Z',
          created_at: '2026-11-16T10:04:00Z',
        },
      ],
    },
    {
      id: 102,
      repository_id: 1,
      pull_request_id: 10,
      target_file: 'backend/app/payments/processor.py',
      target_symbol: 'charge_card',
      category: 'negative',
      title: "Verify error handling for invalid inputs in 'charge_card'",
      description: "Ensure charge_card safely catches declined cards without crashing.",
      edge_case_notes: 'Pass expired card number.',
      suggested_assertions: ['Raises PaymentDeclinedError'],
      existing_test_file: null,
      coverage_gap: true,
      impacted_endpoints: [],
      impacted_services: [],
      priority: 'high',
      created_at: '2026-11-16T10:00:00Z',
      generated_tests: [],
    },
  ],
  existing_tests: [
    {
      test_file: 'backend/tests/test_auth.py',
      test_framework: 'pytest',
      test_count: 2,
      tested_symbols: ['auth', 'user'],
    },
  ],
  regression_test_files: ['backend/tests/test_auth.py'],
};

function renderDashboard() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <TestIntelligenceDashboard repositoryId={1} pullRequestId={10} />
    </QueryClientProvider>
  );
}

describe('TestIntelligenceDashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    testingApi.getTestDashboard.mockResolvedValue(mockDashboardData);
  });

  it('1. Renders overview KPIs and header metrics', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText(/RepoMind AI Test Intelligence/i)).toBeInTheDocument();
      expect(screen.getByText('Recommended Scenarios')).toBeInTheDocument();
      expect(screen.getByText('8')).toBeInTheDocument(); // total_scenarios_count
      expect(screen.getByText('6')).toBeInTheDocument(); // coverage_gaps_count
      expect(screen.getByText('Missing Coverage Gaps')).toBeInTheDocument();
    });
  });

  it('2. Switches category filter and filters scenario list', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText("Verify happy-path execution of 'authenticate_user'")).toBeInTheDocument();
      expect(screen.getByText("Verify error handling for invalid inputs in 'charge_card'")).toBeInTheDocument();
    });

    // Click 'Negative' category filter
    const negativeBtn = screen.getByRole('button', { name: /Negative/i });
    fireEvent.click(negativeBtn);

    // Only negative scenario should remain visible
    expect(screen.getByText("Verify error handling for invalid inputs in 'charge_card'")).toBeInTheDocument();
    expect(screen.queryByText("Verify happy-path execution of 'authenticate_user'")).not.toBeInTheDocument();
  });

  it('3. Filters by Missing Coverage Gaps Only', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText("Verify happy-path execution of 'authenticate_user'")).toBeInTheDocument();
    });

    const checkbox = screen.getByRole('checkbox', { name: /Missing Coverage Gaps Only/i });
    fireEvent.click(checkbox);

    // authenticate_user has coverage_gap: false, so it should disappear
    expect(screen.queryByText("Verify happy-path execution of 'authenticate_user'")).not.toBeInTheDocument();
    // charge_card has coverage_gap: true, so it should stay
    expect(screen.getByText("Verify error handling for invalid inputs in 'charge_card'")).toBeInTheDocument();
  });

  it('4. Switches to Existing Tests tab and renders discovered test files', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('Existing Tests (1)')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Existing Tests (1)'));

    expect(screen.getByText('backend/tests/test_auth.py')).toBeInTheDocument();
    expect(screen.getByText(/pytest/i)).toBeInTheDocument();
  });

  it('5. Switches to Regression Suites tab and renders recommended test commands', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('Regression Suites (1)')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Regression Suites (1)'));

    expect(screen.getByText(/Regression Test Requirements/i)).toBeInTheDocument();
    expect(screen.getByText('pytest backend/tests/test_auth.py')).toBeInTheDocument();
  });

  it('6. Triggers Generate Test Code and displays sandbox execution button', async () => {
    testingApi.generateTestCase.mockResolvedValue({
      id: 502,
      test_scenario_id: 102,
      language: 'python',
      framework: 'pytest',
      test_file_path: 'backend/tests/test_processor_negative.py',
      test_code: 'def test_charge_fail(): pass',
      execution_status: 'pending',
    });

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText("Verify error handling for invalid inputs in 'charge_card'")).toBeInTheDocument();
    });

    const generateBtn = screen.getByRole('button', { name: /Generate Test Code/i });
    fireEvent.click(generateBtn);

    await waitFor(() => {
      expect(testingApi.generateTestCase).toHaveBeenCalledWith(102);
    });
  });
});
