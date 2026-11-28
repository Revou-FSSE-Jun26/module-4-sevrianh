'use client';

import { useCallback, useState } from 'react';
import type { Dispatch, DragEvent, SetStateAction } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { useErrorHandler } from '@/hooks/useErrorHandler';
import { apiClient } from '@/lib/apiClient';
import { computeOrder } from '@/lib/ordering';
import type { BoardDetail, Card, MoveCardResult } from '@/types/api';

/** Remove the Card from every Column and put `card` into `columnId`, sorted by `order`. */
function placeCard(board: BoardDetail, card: Card, columnId: string): BoardDetail {
  return {
    ...board,
    columns: board.columns.map((column) => {
      const others = column.cards.filter((c) => c.id !== card.id);
      if (column.id !== columnId) return { ...column, cards: others };
      return { ...column, cards: [...others, card].sort((a, b) => a.order - b.order) };
    }),
  };
}

function findCard(board: BoardDetail, cardId: string): Card | null {
  for (const column of board.columns) {
    const card = column.cards.find((c) => c.id === cardId);
    if (card) return card;
  }
  return null;
}

/** Order for a drop at `index` among the other Cards of the target Column (FE-27). */
function orderAt(board: BoardDetail, cardId: string, columnId: string, index?: number): number {
  const column = board.columns.find((c) => c.id === columnId);
  const others = (column?.cards ?? []).filter((c) => c.id !== cardId);
  const at = index === undefined ? others.length : Math.max(0, Math.min(index, others.length));
  return computeOrder(others[at - 1]?.order ?? null, others[at]?.order ?? null);
}

export interface UseDragAndDrop {
  board: BoardDetail;
  /** Replace the local board copy, for example after a Column or Card is created. */
  setBoard: Dispatch<SetStateAction<BoardDetail>>;
  draggingCardId: string | null;
  handleDragStart: (event: DragEvent, cardId: string) => void;
  handleDragEnd: () => void;
  handleDragOver: (event: DragEvent) => void;
  /** Drop the dragged Card into `columnId`, at `index` among its other Cards (default: end). */
  handleDrop: (event: DragEvent, columnId: string, index?: number) => Promise<void>;
}

export function useDragAndDrop(initialBoard: BoardDetail): UseDragAndDrop {
  const router = useRouter();
  const { token } = useAuth();
  const { handleError } = useErrorHandler();
  const [board, setBoard] = useState<BoardDetail>(initialBoard);
  const [seenInitial, setSeenInitial] = useState<BoardDetail>(initialBoard);
  const [draggingCardId, setDraggingCardId] = useState<string | null>(null);

  // A new `initialBoard` (after router.refresh()) replaces the local copy (FE-26).
  if (seenInitial !== initialBoard) {
    setSeenInitial(initialBoard);
    setBoard(initialBoard);
  }

  const handleDragStart = useCallback((event: DragEvent, cardId: string): void => {
    event.dataTransfer?.setData('text/plain', cardId);
    setDraggingCardId(cardId);
  }, []);

  const handleDragEnd = useCallback((): void => setDraggingCardId(null), []);

  const handleDragOver = useCallback((event: DragEvent): void => {
    event.preventDefault();
  }, []);

  const handleDrop = useCallback(
    async (event: DragEvent, columnId: string, index?: number): Promise<void> => {
      event.preventDefault();
      const cardId = draggingCardId ?? event.dataTransfer?.getData('text/plain') ?? null;
      setDraggingCardId(null);
      const original = cardId ? findCard(board, cardId) : null;
      if (!cardId || !original) return;

      const order = orderAt(board, cardId, columnId, index);
      setBoard(placeCard(board, { ...original, column_id: columnId, order }, columnId));
      try {
        const result = await apiClient.patch<MoveCardResult>(
          `/api/cards/${cardId}/position`,
          { column_id: columnId, order },
          { token },
        );
        setBoard((current) => placeCard(current, result.card, result.card.column_id));
        if (result.rebalanced) router.refresh();
      } catch (error) {
        setBoard((current) => placeCard(current, original, original.column_id));
        handleError(error);
      }
    },
    [board, draggingCardId, token, router, handleError],
  );

  return {
    board,
    setBoard,
    draggingCardId,
    handleDragStart,
    handleDragEnd,
    handleDragOver,
    handleDrop,
  };
}
