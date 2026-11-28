'use client';

import { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useErrorHandler } from '@/hooks/useErrorHandler';
import { apiClient } from '@/lib/apiClient';
import BaseButton from '@/components/shared/BaseButton';
import type { Comment } from '@/types/api';

interface Props {
  cardId: string;
  parentId?: string;
  editComment?: Comment;
  onCreated?: (comment: Comment) => void;
  onEdited?: (comment: Comment) => void;
  onCancel?: () => void;
}

export default function CommentForm({ cardId, parentId, editComment, onCreated, onEdited, onCancel }: Props) {
  const { token } = useAuth();
  const { handleError } = useErrorHandler();
  const [content, setContent] = useState(editComment?.content ?? '');
  const [submitting, setSubmitting] = useState(false);
  const isEdit = Boolean(editComment);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = content.trim();
    if (!trimmed) return;
    setSubmitting(true);
    try {
      if (isEdit && editComment) {
        const updated = await apiClient.patch<Comment>(`/api/comments/${editComment.id}`, { content: trimmed }, { token });
        onEdited?.(updated);
      } else {
        const created = await apiClient.post<Comment>(
          `/api/cards/${cardId}/comments`,
          { content: trimmed, parent_id: parentId ?? null },
          { token },
        );
        onCreated?.(created);
      }
      setContent('');
    } catch (err) {
      handleError(err);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mt-2 flex flex-col gap-2">
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        rows={2}
        placeholder={isEdit ? 'Edit comment…' : parentId ? 'Reply…' : 'Add a comment…'}
        className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <div className="flex gap-2">
        <BaseButton type="submit" variant="primary" disabled={submitting || !content.trim()}>
          {submitting ? 'Saving…' : isEdit ? 'Update' : 'Comment'}
        </BaseButton>
        {onCancel && (
          <BaseButton type="button" variant="secondary" onClick={onCancel}>Cancel</BaseButton>
        )}
      </div>
    </form>
  );
}
