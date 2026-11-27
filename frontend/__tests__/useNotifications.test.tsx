import { act, renderHook } from '@testing-library/react';
import { NOTIFICATION_POLL_MS, useNotifications } from '@/hooks/useNotifications';
import { apiClient } from '@/lib/apiClient';
import { ApiError } from '@/lib/errors';
import type { NotificationPage } from '@/types/api';

const handleError = jest.fn();
let authenticated = true;

jest.mock('@/context/AuthContext', () => ({
  useAuth: () => ({ token: authenticated ? 'tok' : null, isAuthenticated: authenticated }),
}));
jest.mock('@/hooks/useErrorHandler', () => ({ useErrorHandler: () => ({ handleError }) }));
jest.mock('@/lib/apiClient', () => ({ apiClient: { get: jest.fn() } }));

const get = apiClient.get as jest.Mock;

function pageWith(unread: number, items = 0): NotificationPage {
  return {
    items: Array.from({ length: items }, (_, i) => ({
      id: `n${i}`,
      type: 'mention' as const,
      message: 'm',
      is_read: false,
      created_at: '2025-01-01T00:00:00Z',
      comment_id: 'c',
      card_id: 'k',
      board_id: 'b',
    })),
    page: 1,
    per_page: 20,
    total: unread,
    total_pages: 1,
    unread_count: unread,
  };
}

describe('useNotifications', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.clearAllMocks();
    authenticated = true;
  });
  afterEach(() => jest.useRealTimers());

  it('makes 0 calls at 29 999 ms and 1 call at 30 000 ms', async () => {
    get.mockResolvedValue(pageWith(3));
    renderHook(() => useNotifications());
    await act(async () => {
      jest.advanceTimersByTime(NOTIFICATION_POLL_MS - 1);
    });
    expect(get).toHaveBeenCalledTimes(0);
    await act(async () => {
      jest.advanceTimersByTime(1);
    });
    expect(get).toHaveBeenCalledTimes(1);
    expect(get).toHaveBeenCalledWith('/api/notifications', { token: 'tok' });
  });

  it('takes unreadCount from unread_count, not from items length', async () => {
    get.mockResolvedValue(pageWith(7, 2));
    const { result } = renderHook(() => useNotifications());
    expect(result.current.unreadCount).toBe(0);
    await act(async () => {
      jest.advanceTimersByTime(NOTIFICATION_POLL_MS);
    });
    expect(result.current.unreadCount).toBe(7);
    expect(result.current.page?.items).toHaveLength(2);
  });

  it('does not poll after unmount', async () => {
    get.mockResolvedValue(pageWith(1));
    const { unmount } = renderHook(() => useNotifications());
    unmount();
    await act(async () => {
      jest.advanceTimersByTime(NOTIFICATION_POLL_MS * 3);
    });
    expect(get).not.toHaveBeenCalled();
  });

  it('does not poll when not authenticated', async () => {
    authenticated = false;
    renderHook(() => useNotifications());
    await act(async () => {
      jest.advanceTimersByTime(NOTIFICATION_POLL_MS * 3);
    });
    expect(get).not.toHaveBeenCalled();
  });

  it('keeps the previous page and shows no toast on a non-401 failure', async () => {
    get.mockResolvedValueOnce(pageWith(4)).mockRejectedValueOnce(new ApiError(500, 'boom'));
    const { result } = renderHook(() => useNotifications());
    await act(async () => {
      jest.advanceTimersByTime(NOTIFICATION_POLL_MS);
    });
    await act(async () => {
      jest.advanceTimersByTime(NOTIFICATION_POLL_MS);
    });
    expect(get).toHaveBeenCalledTimes(2);
    expect(result.current.unreadCount).toBe(4);
    expect(handleError).not.toHaveBeenCalled();
  });

  it('routes a 401 failure to the error handler', async () => {
    const error = new ApiError(401, 'Unauthorized');
    get.mockRejectedValue(error);
    renderHook(() => useNotifications());
    await act(async () => {
      jest.advanceTimersByTime(NOTIFICATION_POLL_MS);
    });
    expect(handleError).toHaveBeenCalledWith(error);
  });
});
