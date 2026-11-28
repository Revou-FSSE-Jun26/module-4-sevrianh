'use client';

import { useState } from 'react';
import type { DragEvent } from 'react';
import BaseButton from '@/components/shared/BaseButton';
import BaseModal from '@/components/shared/BaseModal';
import BaseBadge from '@/components/shared/BaseBadge';
import CardDragHandle from '@/components/board/CardDragHandle';
import CardDetailModal from '@/components/card/CardDetailModal';
import CardForm from '@/components/card/CardForm';
import type { Card, TeamMember } from '@/types/api';

interface Props {
  card: Card;
  isReadOnly: boolean;
  isAdmin: boolean;
  members: TeamMember[];
  columnId: string;
  draggingCardId: string | null;
  onDragStart: (e: DragEvent, cardId: string) => void;
  onDragEnd: () => void;
  onUpdated: (card: Card) => void;
  onDeleted: (cardId: string) => void;
}

export default function CardItem({
  card,
  isReadOnly,
  isAdmin,
  members,
  columnId,
  draggingCardId,
  onDragStart,
  onDragEnd,
  onUpdated,
  onDeleted,
}: Props) {
  const [showDetail, setShowDetail] = useState(false);
  const [showEdit, setShowEdit] = useState(false);
  const isDragging = draggingCardId === card.id;

  return (
    <>
      <div
        className={`group relative mb-2 rounded-lg border bg-white p-3 shadow-sm transition-opacity ${isDragging ? 'opacity-40' : 'opacity-100'}`}
      >
        <div className="flex items-start gap-2">
          {!isReadOnly && (
            <CardDragHandle cardId={card.id} onDragStart={onDragStart} onDragEnd={onDragEnd} />
          )}
          <div className="min-w-0 flex-1">
            <BaseButton
              variant="secondary"
              className="w-full justify-start bg-transparent px-0 py-0 text-left font-medium text-gray-800 hover:bg-transparent hover:underline"
              onClick={() => setShowDetail(true)}
            >
              {card.title}
            </BaseButton>
            {card.assignee && (
              <div className="mt-1">
                <BaseBadge>{card.assignee.username}</BaseBadge>
              </div>
            )}
          </div>
          {!isReadOnly && (
            <div className="hidden gap-1 group-hover:flex">
              <BaseButton
                variant="secondary"
                onClick={() => setShowEdit(true)}
                aria-label={`Edit card ${card.title}`}
              >
                ✏️
              </BaseButton>
            </div>
          )}
        </div>
      </div>

      {showDetail && (
        <CardDetailModal
          card={card}
          isReadOnly={isReadOnly}
          isAdmin={isAdmin}
          onClose={() => setShowDetail(false)}
          onUpdated={(c) => { onUpdated(c); setShowDetail(false); }}
          onDeleted={() => { onDeleted(card.id); setShowDetail(false); }}
          members={members}
          columnId={columnId}
        />
      )}

      {showEdit && (
        <BaseModal isOpen={showEdit} title="Edit Card" onClose={() => setShowEdit(false)}>
          <CardForm
            columnId={columnId}
            members={members}
            card={card}
            onClose={() => setShowEdit(false)}
            onSaved={(c) => { onUpdated(c); setShowEdit(false); }}
          />
        </BaseModal>
      )}
    </>
  );
}
