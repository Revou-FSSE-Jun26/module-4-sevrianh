'use client';

import type { DragEvent } from 'react';
import { useState } from 'react';
import ColumnHeader from '@/components/board/ColumnHeader';
import CardItem from '@/components/card/CardItem';
import BaseButton from '@/components/shared/BaseButton';
import BaseModal from '@/components/shared/BaseModal';
import CardForm from '@/components/card/CardForm';
import type { Card, Column, TeamMember } from '@/types/api';

interface Props {
  column: Column;
  isReadOnly: boolean;
  isAdmin: boolean;
  members: TeamMember[];
  draggingCardId: string | null;
  onDragStart: (e: DragEvent, cardId: string) => void;
  onDragEnd: () => void;
  onDragOver: (e: DragEvent) => void;
  onDrop: (e: DragEvent, columnId: string, index?: number) => Promise<void>;
  onColumnRenamed: (columnId: string, name: string) => void;
  onColumnDeleted: (columnId: string) => void;
  onCardUpdated: (card: Card) => void;
  onCardDeleted: (cardId: string, columnId: string) => void;
  onCardCreated: (card: Card) => void;
}

/** The only component with onDragOver / onDrop handlers (FE-28). */
export default function BoardColumn({
  column,
  isReadOnly,
  isAdmin,
  members,
  draggingCardId,
  onDragStart,
  onDragEnd,
  onDragOver,
  onDrop,
  onColumnRenamed,
  onColumnDeleted,
  onCardUpdated,
  onCardDeleted,
  onCardCreated,
}: Props) {
  const [showCardForm, setShowCardForm] = useState(false);

  return (
    <div
      className="flex h-fit min-h-32 w-72 shrink-0 flex-col rounded-xl border border-gray-200 bg-gray-50 p-3"
      onDragOver={onDragOver}
      onDrop={(e) => { void onDrop(e, column.id); }}
    >
      <ColumnHeader
        columnId={column.id}
        name={column.name}
        cardCount={column.cards.length}
        isAdmin={isAdmin}
        onRenamed={(name) => onColumnRenamed(column.id, name)}
        onDeleted={() => onColumnDeleted(column.id)}
      />

      <div className="flex-1">
        {column.cards.map((card) => (
          <CardItem
            key={card.id}
            card={card}
            isReadOnly={isReadOnly}
            isAdmin={isAdmin}
            members={members}
            columnId={column.id}
            draggingCardId={draggingCardId}
            onDragStart={onDragStart}
            onDragEnd={onDragEnd}
            onUpdated={onCardUpdated}
            onDeleted={(cardId) => onCardDeleted(cardId, column.id)}
          />
        ))}
      </div>

      {!isReadOnly && (
        <BaseButton variant="secondary" className="mt-2 w-full" onClick={() => setShowCardForm(true)}>
          + Add Card
        </BaseButton>
      )}

      {showCardForm && (
        <BaseModal isOpen={showCardForm} title="New Card" onClose={() => setShowCardForm(false)}>
          <CardForm
            columnId={column.id}
            members={members}
            onClose={() => setShowCardForm(false)}
            onSaved={(card) => { onCardCreated(card); setShowCardForm(false); }}
          />
        </BaseModal>
      )}
    </div>
  );
}
