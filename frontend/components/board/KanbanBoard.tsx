'use client';

import { useState } from 'react';
import { useDragAndDrop } from '@/hooks/useDragAndDrop';
import BoardColumn from '@/components/board/BoardColumn';
import ColumnForm from '@/components/board/ColumnForm';
import BaseButton from '@/components/shared/BaseButton';
import type { BoardDetail, Card, Column, TeamMember } from '@/types/api';

interface Props {
  initialBoard: BoardDetail;
  isReadOnly: boolean;
  isAdmin: boolean;
  members: TeamMember[];
}

export default function KanbanBoard({ initialBoard, isReadOnly, isAdmin, members }: Props) {
  const {
    board,
    setBoard,
    draggingCardId,
    handleDragStart,
    handleDragEnd,
    handleDragOver,
    handleDrop,
  } = useDragAndDrop(initialBoard);
  const [showColumnForm, setShowColumnForm] = useState(false);
  const columns = board.columns;

  function updateColumns(change: (current: Column[]) => Column[]) {
    setBoard((current) => ({ ...current, columns: change(current.columns) }));
  }

  function handleColumnCreated(column: Column) {
    updateColumns((cols) => [...cols, { ...column, cards: column.cards ?? [] }]);
    setShowColumnForm(false);
  }

  function handleColumnRenamed(columnId: string, name: string) {
    updateColumns((cols) => cols.map((c) => (c.id === columnId ? { ...c, name } : c)));
  }

  function handleColumnDeleted(columnId: string) {
    updateColumns((cols) => cols.filter((c) => c.id !== columnId));
  }

  function handleCardUpdated(card: Card) {
    updateColumns((cols) =>
      cols.map((c) => ({
        ...c,
        cards: c.cards.map((existing) => (existing.id === card.id ? card : existing)),
      })),
    );
  }

  function handleCardDeleted(cardId: string, columnId: string) {
    updateColumns((cols) =>
      cols.map((c) =>
        c.id === columnId ? { ...c, cards: c.cards.filter((card) => card.id !== cardId) } : c,
      ),
    );
  }

  function handleCardCreated(card: Card) {
    updateColumns((cols) =>
      cols.map((c) => (c.id === card.column_id ? { ...c, cards: [...c.cards, card] } : c)),
    );
  }
  return (
    <div className="flex w-full gap-4 overflow-x-auto pb-4">
      {columns.map((column) => (
        <BoardColumn
          key={column.id}
          column={column}
          isReadOnly={isReadOnly}
          isAdmin={isAdmin}
          members={members}
          draggingCardId={draggingCardId}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onColumnRenamed={handleColumnRenamed}
          onColumnDeleted={handleColumnDeleted}
          onCardUpdated={handleCardUpdated}
          onCardDeleted={handleCardDeleted}
          onCardCreated={handleCardCreated}
        />
      ))}

      {!isReadOnly && isAdmin && (
        <div className="shrink-0">
          <BaseButton
            variant="secondary"
            onClick={() => setShowColumnForm(true)}
            className="whitespace-nowrap"
          >
            + Add Column
          </BaseButton>
          {showColumnForm && (
            <ColumnForm
              boardId={board.id}
              onClose={() => setShowColumnForm(false)}
              onCreated={handleColumnCreated}
            />
          )}
        </div>
      )}
    </div>
  );
}
