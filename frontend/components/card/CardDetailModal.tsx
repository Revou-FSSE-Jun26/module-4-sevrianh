'use client';

import { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useErrorHandler } from '@/hooks/useErrorHandler';
import { apiClient } from '@/lib/apiClient';
import BaseModal from '@/components/shared/BaseModal';
import BaseButton from '@/components/shared/BaseButton';
import BaseBadge from '@/components/shared/BaseBadge';
import CommentList from '@/components/comments/CommentList';
import CardForm from '@/components/card/CardForm';
import type { Card, TeamMember } from '@/types/api';

interface Props {
  card: Card;
  isReadOnly: boolean;
  isAdmin: boolean;
  members: TeamMember[];
  columnId: string;
  inviteToken?: string;
  onClose: () => void;
  onUpdated: (card: Card) => void;
  onDeleted: () => void;
}

export default function CardDetailModal({
  card,
  isReadOnly,
  isAdmin,
  members,
  columnId,
  inviteToken,
  onClose,
  onUpdated,
  onDeleted,
}: Props) {
  const { token } = useAuth();
  const { handleError } = useErrorHandler();
  const [editing, setEditing] = useState(false);
  const [deleting, setDeleting] = useState(false);

  async function handleDelete() {
    if (!confirm(`Delete card "${card.title}"?`)) return;
    setDeleting(true);
    try {
      await apiClient.delete(`/api/cards/${card.id}`, { token });
      onDeleted();
    } catch (err) {
      handleError(err);
    } finally {
      setDeleting(false);
    }
  }

  return (
    <BaseModal isOpen={true} title={card.title} onClose={onClose}>
      {editing ? (
        <CardForm
          columnId={columnId}
          members={members}
          card={card}
          onClose={() => setEditing(false)}
          onSaved={(c) => { onUpdated(c); setEditing(false); }}
        />
      ) : (
        <div>
          {card.description && (
            <p className="mb-3 whitespace-pre-wrap text-sm text-gray-700">{card.description}</p>
          )}
          {card.assignee ? (
            <div className="mb-3">
              <span className="text-xs text-gray-500">Assignee: </span>
              <BaseBadge>{card.assignee.username}</BaseBadge>
            </div>
          ) : (
            <p className="mb-3 text-xs text-gray-400">No assignee</p>
          )}
          {card.completed_at && (
            <p className="mb-3 text-xs text-green-600">
              ✓ Completed {new Date(card.completed_at).toLocaleDateString()}
            </p>
          )}
          {!isReadOnly && (
            <div className="mb-4 flex gap-2">
              <BaseButton variant="secondary" onClick={() => setEditing(true)}>Edit</BaseButton>
              {isAdmin && (
                <BaseButton variant="destructive" onClick={handleDelete} disabled={deleting}>
                  {deleting ? 'Deleting…' : 'Delete'}
                </BaseButton>
              )}
            </div>
          )}
        </div>
      )}
      <hr className="my-4" />
      <CommentList cardId={card.id} isReadOnly={isReadOnly} inviteToken={inviteToken} />
    </BaseModal>
  );
}
