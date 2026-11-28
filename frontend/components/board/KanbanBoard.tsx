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
  const { board, draggingCardId, handleDragStart, handleDragEnd, handleDragOver, handleDrop } =
    useDragAndDrop(initialBoard);
  const [columns, setColumns] = useState<Column[]>(board.columns);
  const [showColumnForm, setShowColumnForm] = useState(false);

  // Sync columns when board refreshes
  if (board.columns !== columns && JSON.stringify(board.columns) !== JSON.stringify(columns)) {
    setColumns(board.columns);
  }

  function handleColumnRenamed(columnId: string, name: string) {
    setColumns((cols) => cols.map((c) => (c.id === columnId ? { ...c, name } : c)));
  }

  function handleColumnDeleted(columnId: string) {
    setColumns((cols) => cols.filter((c) => c.id !== columnId));
  }

  function handleCardUpdated(card: Card) {
    setColumns((cols) =>
      cols.map((c) => ({
        ...c,
        cards: c.cards.map((existing) => (existing.id === card.id ? card : existing)),
      })),
    );
  }

  function handleCardDeleted(cardId: string, columnId: string) {
    setColumns((cols) =>
      cols.map((c) => (c.id === columnId ? { ...c, cards: c.cards.filter((card) => card.id !== cardId) } : c)),
    );
  }

  function handleCardCreated(card: Card) {
    setColumns((cols) =>
      cols.map((c) => (c.id === card.column_id ? { ...c, cards: [...c.cards, card] } : c)),
    );
  }

  return (
    <div className="flex gap-4 overflow-x-auto pb-4">
      {columns.map((column) => (
        <BoardColumn
          key={column.id}
          column={{ ...column, cards: board.columns.find((c) => c.id === column.id)?.cards ?? column.cards }}
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
          <BaseButton variant="secondary" onClick={() => setShowColumnForm(true)} className="whitespace-nowrap">
            + Add Column
          </BaseButton>
          {showColumnForm && (
            <ColumnForm
              boardId={board.id}
              onClose={() => setShowColumnForm(false)}
              onCreated={(col) => { setColumns((cs) => [...cs, col]); setShowColumnForm(false); }}
            />
          )}
        </div>
      )}
    </div>
  );
}
