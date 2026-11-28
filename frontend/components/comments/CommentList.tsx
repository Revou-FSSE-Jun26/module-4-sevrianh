'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useErrorHandler } from '@/hooks/useErrorHandler';
import { apiClient } from '@/lib/apiClient';
import CommentItem from '@/components/comments/CommentItem';
import CommentForm from '@/components/comments/CommentForm';
import type { Comment } from '@/types/api';

interface Props {
  cardId: string;
  isReadOnly: boolean;
  inviteToken?: string;
}

export default function CommentList({ cardId, isReadOnly, inviteToken }: Props) {
  const { token } = useAuth();
  const { handleError } = useErrorHandler();
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const opts = inviteToken ? { inviteToken } : { token };
    apiClient
      .get<Comment[]>(`/api/cards/${cardId}/comments`, opts)
      .then(setComments)
      .catch((err: unknown) => handleError(err))
      .finally(() => setLoading(false));
  }, [cardId, token, inviteToken, handleError]);

  function handleCreated(comment: Comment) {
    setComments((cs) => [...cs, comment]);
  }

  function handleEdited(updated: Comment) {
    setComments((cs) => cs.map((c) => (c.id === updated.id ? updated : c)));
  }

  function handleDeleted(commentId: string) {
    setComments((cs) => cs.map((c) => (c.id === commentId ? { ...c, is_deleted: true } : c)));
  }

  function handleReplied(reply: Comment) {
    setComments((cs) => [...cs, reply]);
  }

  const roots = comments.filter((c) => !c.parent_id);
  const replies = (parentId: string) => comments.filter((c) => c.parent_id === parentId);

  if (loading) return <p className="text-sm text-gray-400">Loading comments…</p>;

  return (
    <div>
      <h3 className="mb-3 text-sm font-semibold text-gray-700">Comments</h3>
      {roots.length === 0 && !isReadOnly && (
        <p className="mb-3 text-xs text-gray-400">No comments yet. Be the first!</p>
      )}
      {roots.map((c) => (
        <CommentItem
          key={c.id}
          comment={c}
          authorId={c.author_id}
          isReadOnly={isReadOnly}
          replies={replies(c.id)}
          onEdited={handleEdited}
          onDeleted={handleDeleted}
          onReplied={handleReplied}
          cardId={cardId}
        />
      ))}
      {!isReadOnly && (
        <CommentForm cardId={cardId} onCreated={handleCreated} />
      )}
    </div>
  );
}
