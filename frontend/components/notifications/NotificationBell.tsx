'use client';

import { useState } from 'react';
import Link from 'next/link';
import BaseButton from '@/components/shared/BaseButton';
import { useAuth } from '@/context/AuthContext';
import { useErrorHandler } from '@/hooks/useErrorHandler';
import { useNotifications } from '@/hooks/useNotifications';
import { apiClient } from '@/lib/apiClient';

export default function NotificationBell() {
  const { token } = useAuth();
  const { handleError } = useErrorHandler();
  const { page, unreadCount } = useNotifications();
  const [isOpen, setIsOpen] = useState(false);
  const [readIds, setReadIds] = useState<string[]>([]);
  const items = page?.items ?? [];

  const handleToggle = (): void => setIsOpen((open) => !open);

  const handleItemClick = async (id: string): Promise<void> => {
    setIsOpen(false);
    try {
      await apiClient.patch(`/api/notifications/${id}/read`, undefined, { token });
      setReadIds((ids) => [...ids, id]);
    } catch (error) {
      handleError(error);
    }
  };

  return (
    <div className="relative">
      <BaseButton variant="secondary" aria-label="Notifications" onClick={handleToggle}>
        <span aria-hidden="true">🔔</span>
        {unreadCount > 0 && (
          <span
            data-testid="notification-badge"
            className="rounded-full bg-danger px-2 text-xs font-semibold text-white"
          >
            {unreadCount}
          </span>
        )}
      </BaseButton>
      {isOpen && (
        <ul className="absolute right-0 z-10 mt-2 w-72 rounded-lg border border-line bg-surface p-2 shadow-lg">
          {items.length === 0 && <li className="p-2 text-sm text-ink-muted">No notifications</li>}
          {items.map((item) => (
            <li key={item.id}>
              <Link
                href={`/boards/${item.board_id}?card=${item.card_id}`}
                onClick={() => void handleItemClick(item.id)}
                className={`block min-h-11 rounded-lg p-2 text-sm text-ink hover:bg-secondary ${
                  item.is_read || readIds.includes(item.id) ? '' : 'font-semibold'
                }`}
              >
                {item.message}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
