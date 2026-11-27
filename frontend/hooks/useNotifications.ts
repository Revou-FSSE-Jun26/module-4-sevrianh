'use client';

import { useEffect, useRef, useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useErrorHandler } from '@/hooks/useErrorHandler';
import { apiClient } from '@/lib/apiClient';
import { ApiError } from '@/lib/errors';
import type { NotificationPage } from '@/types/api';

export const NOTIFICATION_POLL_MS = 30_000;

export function useNotifications(): {
  page: NotificationPage | null;
  unreadCount: number;
} {
  const { token, isAuthenticated } = useAuth();
  const { handleError } = useErrorHandler();
  const [page, setPage] = useState<NotificationPage | null>(null);
  const handleErrorRef = useRef(handleError);

  useEffect(() => {
    handleErrorRef.current = handleError;
  }, [handleError]);

  useEffect(() => {
    if (!isAuthenticated) return;
    let active = true;

    const poll = async (): Promise<void> => {
      try {
        const next = await apiClient.get<NotificationPage>('/api/notifications', { token });
        if (active) setPage(next);
      } catch (error) {
        // Keep the previous page; only a 401 is reported (FE-28, FE-24).
        if (active && error instanceof ApiError && error.statusCode === 401) {
          handleErrorRef.current(error);
        }
      }
    };

    const id = setInterval(() => {
      void poll();
    }, NOTIFICATION_POLL_MS);

    return () => {
      active = false;
      clearInterval(id);
    };
  }, [isAuthenticated, token]);

  return { page, unreadCount: page?.unread_count ?? 0 };
}
