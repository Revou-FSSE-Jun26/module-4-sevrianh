'use client';

import { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useErrorHandler } from '@/hooks/useErrorHandler';
import { apiClient } from '@/lib/apiClient';
import BaseButton from '@/components/shared/BaseButton';
import CommentForm from '@/components/comments/CommentForm';
import type { Comment } from '@/types/api';

interface Props {
  comment: Comment;
  authorId: string;
  isReadOnly: boolean;
  replies: Comment[];
  onEdited: (comment: Comment) => void;
  onDeleted: (commentId: string) => void;
  onReplied: (comment: Comment) => void;
  cardId: string;
}

export default function CommentItem({
  comment,
  authorId,
  isReadOnly,
  replies,
  onEdited,
  onDeleted,
  onReplied,
  cardId,
}: Props) {
  const { token, user } = useAuth();
  const { handleError } = useErrorHandler();
  const [editing, setEditing] = useState(false);
  const [replying, setReplying] = useState(false);
  const isAuthor = user?.id === authorId;
  const wasEdited = comment.updated_at > comment.created_at;

  if (comment.is_deleted && replies.length === 0) return null;

  async function handleDelete() {
    try {
      await apiClient.delete(`/api/comments/${comment.id}`, { token });
      onDeleted(comment.id);
    } catch (err) {
      handleError(err);
    }
  }

  return (
    <div className="mb-3">
      <div className="rounded-lg border border-gray-100 bg-gray-50 p-3">
        {comment.is_deleted ? (
          <p className="text-xs italic text-gray-400">This comment was deleted.</p>
        ) : (
          <>
            <p className="whitespace-pre-wrap text-sm text-gray-800">{comment.content}</p>
            <div className="mt-1 flex items-center gap-3 text-xs text-gray-400">
              <span>{new Date(comment.created_at).toLocaleString()}</span>
              {wasEdited && <span className="italic">edited</span>}
              {!isReadOnly && !editing && (
                <>
                  <BaseButton variant="secondary" onClick={() => setReplying((r) => !r)} aria-label="Reply to comment">
                    Reply
                  </BaseButton>
                  {isAuthor && (
                    <>
                      <BaseButton variant="secondary" onClick={() => setEditing(true)} aria-label="Edit comment">
                        Edit
                      </BaseButton>
                      <BaseButton variant="secondary" onClick={handleDelete} aria-label="Delete comment">
                        Delete
                      </BaseButton>
                    </>
                  )}
                </>
              )}
            </div>
            {editing && (
              <CommentForm
                cardId={cardId}
                editComment={comment}
                onEdited={(c) => { onEdited(c); setEditing(false); }}
                onCancel={() => setEditing(false)}
              />
            )}
            {replying && (
              <CommentForm
                cardId={cardId}
                parentId={comment.id}
                onCreated={(c) => { onReplied(c); setReplying(false); }}
                onCancel={() => setReplying(false)}
              />
            )}
          </>
        )}
      </div>
      {replies.length > 0 && (
        <div className="ml-6 mt-2 border-l-2 border-gray-200 pl-3">
          {replies.map((reply) => (
            <CommentItem
              key={reply.id}
              comment={reply}
              authorId={reply.author_id}
              isReadOnly={isReadOnly}
              replies={[]}
              onEdited={onEdited}
              onDeleted={onDeleted}
              onReplied={onReplied}
              cardId={cardId}
            />
          ))}
        </div>
      )}
    </div>
  );
}
