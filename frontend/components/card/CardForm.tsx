'use client';

import { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useErrorHandler } from '@/hooks/useErrorHandler';
import { apiClient } from '@/lib/apiClient';
import BaseButton from '@/components/shared/BaseButton';
import BaseBadge from '@/components/shared/BaseBadge';
import type { Card, TeamMember } from '@/types/api';

interface Props {
  columnId: string;
  members: TeamMember[];
  card?: Card;
  onClose: () => void;
  onSaved: (card: Card) => void;
}

export default function CardForm({ columnId, members, card, onClose, onSaved }: Props) {
  const { token } = useAuth();
  const { handleError } = useErrorHandler();
  const [title, setTitle] = useState(card?.title ?? '');
  const [description, setDescription] = useState(card?.description ?? '');
  const [assigneeId, setAssigneeId] = useState<string>(card?.assignee_id ?? '');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const isEdit = Boolean(card);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmedTitle = title.trim();
    if (!trimmedTitle) { setError('Title is required.'); return; }
    if (trimmedTitle.length > 200) { setError('Title must be 200 characters or fewer.'); return; }
    setError('');
    setSubmitting(true);
    try {
      const body = {
        title: trimmedTitle,
        description: description.trim() || undefined,
        assignee_id: assigneeId || null,
      };
      const saved = isEdit
        ? await apiClient.patch<Card>(`/api/cards/${card!.id}`, body, { token })
        : await apiClient.post<Card>(`/api/columns/${columnId}/cards`, body, { token });
      onSaved(saved);
      onClose();
    } catch (err) {
      handleError(err);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <div className="mb-3">
        <label htmlFor="card-title" className="mb-1 block text-sm font-medium text-gray-700">
          Title <span aria-hidden="true">*</span>
        </label>
        <input
          id="card-title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          maxLength={200}
          required
          className="min-h-11 w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        {error && <p role="alert" className="mt-1 text-xs text-red-600">{error}</p>}
      </div>
      <div className="mb-3">
        <label htmlFor="card-desc" className="mb-1 block text-sm font-medium text-gray-700">Description</label>
        <textarea
          id="card-desc"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          className="min-h-11 w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <div className="mb-4">
        <label htmlFor="card-assignee" className="mb-1 block text-sm font-medium text-gray-700">Assignee</label>
        <select
          id="card-assignee"
          value={assigneeId}
          onChange={(e) => setAssigneeId(e.target.value)}
          className="min-h-11 w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Unassigned</option>
          {members.map((m) => (
            <option key={m.user_id} value={m.user_id}>
              {m.name} (@{m.username})
            </option>
          ))}
        </select>
        {assigneeId && (
          <div className="mt-1">
            <BaseBadge>{members.find((m) => m.user_id === assigneeId)?.username ?? assigneeId}</BaseBadge>
          </div>
        )}
      </div>
      <div className="flex justify-end gap-2">
        <BaseButton type="button" variant="secondary" onClick={onClose} disabled={submitting}>Cancel</BaseButton>
        <BaseButton type="submit" variant="primary" disabled={submitting}>
          {submitting ? 'Saving…' : isEdit ? 'Save Changes' : 'Add Card'}
        </BaseButton>
      </div>
    </form>
  );
}
