'use client';

import { useEffect, useRef, useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useDebouncedValue } from '@/hooks/useDebouncedValue';
import { useErrorHandler } from '@/hooks/useErrorHandler';
import { apiClient } from '@/lib/apiClient';
import type { CardListItem } from '@/types/api';

export const SEARCH_DEBOUNCE_MS = 300;

export function useCardSearch(
  term: string,
  boardId?: string,
): { results: CardListItem[]; isLoading: boolean } {
  const { token } = useAuth();
  const { handleError } = useErrorHandler();
  // useDebouncedValue starts at its first value; feed '' on the first render so an initial
  // term is also delayed by SEARCH_DEBOUNCE_MS.
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  const debounced = useDebouncedValue(mounted ? term : '', SEARCH_DEBOUNCE_MS);
  const trimmed = debounced.trim();
  const [loaded, setLoaded] = useState<{ key: string; items: CardListItem[] } | null>(null);
  const latestTerm = useRef(term.trim());
  const handleErrorRef = useRef(handleError);

  useEffect(() => {
    latestTerm.current = term.trim();
    handleErrorRef.current = handleError;
  });

  const key = `${boardId ?? ''}|${trimmed}`;

  useEffect(() => {
    if (!trimmed) return;
    let active = true;
    const params = new URLSearchParams({ q: trimmed });
    if (boardId) params.set('board_id', boardId);

    apiClient
      .get<CardListItem[]>(`/api/cards?${params.toString()}`, { token })
      .then((items) => {
        // Ignore a response for an older term when a newer one is pending (FE-29).
        if (active && latestTerm.current === trimmed) setLoaded({ key, items });
      })
      .catch((error: unknown) => {
        if (active) handleErrorRef.current(error);
      });

    return () => {
      active = false;
    };
  }, [trimmed, boardId, token, key]);

  const results = trimmed && loaded?.key === key ? loaded.items : [];
  const isLoading = trimmed !== '' && loaded?.key !== key;
  return { results, isLoading };
}
