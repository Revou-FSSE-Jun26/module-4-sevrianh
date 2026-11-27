import { act, fireEvent, render, screen } from '@testing-library/react';
import Header from '@/components/layout/Header';
import NotificationBell from '@/components/notifications/NotificationBell';
import { apiClient } from '@/lib/apiClient';
import type { NotificationPage } from '@/types/api';

let page: NotificationPage | null = null;
let unreadCount = 0;
let pathname = '/';
let search = '';
const logout = jest.fn();

jest.mock('@/hooks/useNotifications', () => ({
  useNotifications: () => ({ page, unreadCount }),
}));
jest.mock('@/hooks/useErrorHandler', () => ({
  useErrorHandler: () => ({ handleError: jest.fn() }),
}));
jest.mock('@/context/AuthContext', () => ({
  useAuth: () => ({ token: 'tok', isAuthenticated: true, logout }),
}));
jest.mock('next/navigation', () => ({
  usePathname: () => pathname,
  useSearchParams: () => new URLSearchParams(search),
}));
jest.mock('@/lib/apiClient', () => ({ apiClient: { patch: jest.fn() } }));

function makePage(unread: number, count: number): NotificationPage {
  return {
    items: Array.from({ length: count }, (_, i) => ({
      id: `n${i}`,
      type: 'mention' as const,
      message: `Mention ${i}`,
      is_read: false,
      created_at: '2025-01-01T00:00:00Z',
      comment_id: 'c1',
      card_id: 'card-1',
      board_id: 'board-1',
    })),
    page: 1,
    per_page: 20,
    total: unread,
    total_pages: 1,
    unread_count: unread,
  };
}

beforeEach(() => {
  jest.clearAllMocks();
  pathname = '/';
  search = '';
});

describe('NotificationBell', () => {
  it('shows unread_count, not items.length', () => {
    page = makePage(12, 2);
    unreadCount = 12;
    render(<NotificationBell />);
    expect(screen.getByTestId('notification-badge')).toHaveTextContent('12');
  });

  it('hides the badge at 0', () => {
    page = makePage(0, 0);
    unreadCount = 0;
    render(<NotificationBell />);
    expect(screen.queryByTestId('notification-badge')).not.toBeInTheDocument();
  });

  it('links an item to /boards/<board_id>?card=<card_id> and marks it read', async () => {
    page = makePage(1, 1);
    unreadCount = 1;
    render(<NotificationBell />);
    fireEvent.click(screen.getByRole('button', { name: 'Notifications' }));
    const link = screen.getByRole('link', { name: 'Mention 0' });
    expect(link).toHaveAttribute('href', '/boards/board-1?card=card-1');
    await act(async () => {
      fireEvent.click(link);
    });
    expect(apiClient.patch).toHaveBeenCalledWith('/api/notifications/n0/read', undefined, {
      token: 'tok',
    });
  });
});

describe('Header', () => {
  it('shows links, bell and logout on an authenticated page', () => {
    page = makePage(0, 0);
    unreadCount = 0;
    render(<Header />);
    expect(screen.getByRole('link', { name: 'My Tasks' })).toHaveAttribute('href', '/my-tasks');
    expect(screen.getByRole('link', { name: 'Profile' })).toHaveAttribute('href', '/profile');
    expect(screen.getByRole('button', { name: 'Notifications' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Log out' }));
    expect(logout).toHaveBeenCalled();
  });

  it('shows only the brand in Guest mode', () => {
    pathname = '/boards/b1';
    search = 'invite=abc';
    render(<Header />);
    expect(screen.getByRole('link', { name: 'Sevy' })).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'My Tasks' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});
