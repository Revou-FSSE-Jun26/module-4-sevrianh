import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import AnalyticsPanel from '@/components/board/AnalyticsPanel';
import { apiClient } from '@/lib/apiClient';
import type { AnalyticsData } from '@/types/api';

jest.mock('@/context/AuthContext', () => ({ useAuth: () => ({ token: 'tok' }) }));
jest.mock('@/hooks/useErrorHandler', () => ({ useErrorHandler: () => ({ handleError: jest.fn() }) }));
jest.mock('@/lib/apiClient', () => ({
  apiClient: { get: jest.fn() },
}));

const mockData: AnalyticsData = {
  cards_per_column: [
    { column_id: 'c1', column_name: 'Todo', count: 3 },
    { column_id: 'c2', column_name: 'Done', count: 7 },
  ],
  completed_this_week: 5,
  member_activity: [
    { user_id: 'u1', name: 'Alice', username: 'alice', event_count: 12 },
  ],
  activity_per_day: [
    { date: '2024-01-01', count: 4 },
  ],
  start_date: '2024-01-01',
  end_date: '2024-01-07',
};

describe('AnalyticsPanel', () => {
  it('shows loading state initially', () => {
    jest.mocked(apiClient.get).mockReturnValue(new Promise(() => {}));
    render(<AnalyticsPanel boardId="b1" />);
    expect(screen.getByText(/loading analytics/i)).toBeInTheDocument();
  });

  it('renders analytics data after load', async () => {
    jest.mocked(apiClient.get).mockResolvedValue(mockData);
    render(<AnalyticsPanel boardId="b1" />);
    await waitFor(() => expect(screen.getByText('Todo')).toBeInTheDocument());
    expect(screen.getByText('Done')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('12 events')).toBeInTheDocument();
    expect(screen.getByText('2024-01-01')).toBeInTheDocument();
  });

  it('calls correct analytics endpoint', async () => {
    jest.mocked(apiClient.get).mockResolvedValue(mockData);
    render(<AnalyticsPanel boardId="b42" />);
    await waitFor(() => expect(apiClient.get).toHaveBeenCalledWith('/api/boards/b42/analytics', { token: 'tok' }));
  });
});
