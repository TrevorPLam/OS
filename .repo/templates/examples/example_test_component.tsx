/**
 * Example: React Component Test Pattern
 * File: frontend/tests/components/ClientList.test.tsx
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ClientList } from '../../src/components/ClientList';
import * as apiClient from '../../src/api/clients';

// Mock API client
vi.mock('../../src/api/clients', () => ({
  fetchClients: vi.fn(),
}));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('ClientList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state', () => {
    vi.mocked(apiClient.fetchClients).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<ClientList />, { wrapper });
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('renders client list', async () => {
    const mockClients = [
      { id: 1, name: 'Client 1' },
      { id: 2, name: 'Client 2' },
    ];

    vi.mocked(apiClient.fetchClients).mockResolvedValue(mockClients);

    render(<ClientList />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Client 1')).toBeInTheDocument();
      expect(screen.getByText('Client 2')).toBeInTheDocument();
    });
  });

  it('handles error state', async () => {
    vi.mocked(apiClient.fetchClients).mockRejectedValue(
      new Error('Failed to fetch')
    );

    render(<ClientList />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });

  it('handles user interaction', async () => {
    const user = userEvent.setup();
    const mockClients = [{ id: 1, name: 'Client 1' }];
    vi.mocked(apiClient.fetchClients).mockResolvedValue(mockClients);

    render(<ClientList />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Client 1')).toBeInTheDocument();
    });

    const button = screen.getByRole('button', { name: /delete/i });
    await user.click(button);

    await waitFor(() => {
      expect(screen.queryByText('Client 1')).not.toBeInTheDocument();
    });
  });

  it('handles empty state', async () => {
    vi.mocked(apiClient.fetchClients).mockResolvedValue([]);

    render(<ClientList />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText(/no clients/i)).toBeInTheDocument();
    });
  });
});
