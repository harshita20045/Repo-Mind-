import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

// Mock the API module
vi.mock('../src/lib/api', () => ({
  reviewApi: {
    triggerReview: vi.fn(),
    getReviewRun: vi.fn(),
  }
}));

import { reviewApi } from '../src/lib/api';
import ReviewPage from '../src/pages/ReviewPage';

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

const renderWithProviders = (ui) => {
  const testQueryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={testQueryClient}>
      <MemoryRouter initialEntries={['/repositories/1/pull-requests/42']}>
        <Routes>
          <Route path="/repositories/:rid/pull-requests/:prid" element={ui} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('ReviewUI Lifecycle', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('renders initial state and triggers review', async () => {
    reviewApi.triggerReview.mockResolvedValueOnce({ job_id: 100, status: 'pending' });
    reviewApi.getReviewRun.mockResolvedValueOnce({ id: 100, status: 'pending' });

    renderWithProviders(<ReviewPage user={{ email: 'test@example.com' }} onLogout={() => {}} />);
    
    // Initial state
    expect(screen.getByText('No active review')).toBeInTheDocument();
    
    // Trigger
    const triggerBtn = screen.getByRole('button', { name: /Run Review/i });
    fireEvent.click(triggerBtn);
    
    await waitFor(() => {
      expect(reviewApi.triggerReview).toHaveBeenCalledWith('42');
    });
    
    // Wait for pending state
    await waitFor(() => {
      expect(screen.getByText('Review Queued')).toBeInTheDocument();
    });
  });

  test('displays findings when review completes', async () => {
    reviewApi.triggerReview.mockResolvedValueOnce({ job_id: 101, status: 'pending' });
    reviewApi.getReviewRun
      .mockResolvedValueOnce({ id: 101, status: 'running' })
      .mockResolvedValueOnce({ 
        id: 101, 
        status: 'completed', 
        findings: [
          {
            id: 1,
            title: 'Hardcoded secret',
            severity: 'critical',
            type: 'security',
            explanation: 'Found a dummy PAT',
            file: 'src/config.js',
            line: 12
          }
        ]
      });

    renderWithProviders(<ReviewPage user={{ email: 'test@example.com' }} onLogout={() => {}} />);
    
    fireEvent.click(screen.getByRole('button', { name: /Run Review/i }));
    
    // Wait for completed state to show findings
    await waitFor(() => {
      expect(screen.getByText('Findings')).toBeInTheDocument();
    }, { timeout: 3000 });
    
    expect(screen.getByText('Hardcoded secret')).toBeInTheDocument();
    expect(screen.getByText('critical')).toBeInTheDocument();
    expect(screen.getByText('security')).toBeInTheDocument();
    expect(screen.getByText('src/config.js :12')).toBeInTheDocument();
  });

  test('displays error state on failure', async () => {
    reviewApi.triggerReview.mockResolvedValueOnce({ job_id: 102, status: 'pending' });
    reviewApi.getReviewRun.mockResolvedValueOnce({ id: 102, status: 'failed' });

    renderWithProviders(<ReviewPage user={{ email: 'test@example.com' }} onLogout={() => {}} />);
    
    fireEvent.click(screen.getByRole('button', { name: /Run Review/i }));
    
    await waitFor(() => {
      expect(screen.getByText('Review Failed')).toBeInTheDocument();
    });
  });
});
