'use client';

import { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useErrorHandler } from '@/hooks/useErrorHandler';
import { apiClient } from '@/lib/apiClient';
import BaseButton from '@/components/shared/BaseButton';
import BaseModal from '@/components/shared/BaseModal';
import type { Column } from '@/types/api';

interface Props {
  boardId: string;
  onClose: () => void;
  onCreated: (column: Column) => void;
}

export default function ColumnForm({ boardId, onClose, onCreated }: Props) {
  const { token } = useAuth();
  const { handleError } = useErrorHandler();
  const [name, setName] = useState('');
  const [isDone, setIsDone] = useState(false);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) { setError('Column name is required.'); return; }
    if (trimmed.length > 100) { setError('Column name must be 100 characters or fewer.'); return; }
    setError('');
    setSubmitting(true);
    try {
      const col = await apiClient.post<Column>(
        `/api/boards/${boardId}/columns`,
        { name: trimmed, is_done: isDone },
        { token },
      );
      onCreated(col);
      onClose();
    } catch (err) {
      handleError(err);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <BaseModal isOpen={true} title="New Column" onClose={onClose}>
      <form onSubmit={handleSubmit} noValidate>
        <div className="mb-3">
          <label htmlFor="col-name" className="mb-1 block text-sm font-medium text-gray-700">
            Column Name <span aria-hidden="true">*</span>
          </label>
          <input
            id="col-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            maxLength={100}
            required
            className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g. In Progress"
          />
          {error && <p role="alert" className="mt-1 text-xs text-red-600">{error}</p>}
        </div>
        <label className="mb-4 flex items-center gap-2 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={isDone}
            onChange={(e) => setIsDone(e.target.checked)}
          />
          Mark as &quot;done&quot; column
        </label>
        <div className="flex justify-end gap-2">
          <BaseButton type="button" variant="secondary" onClick={onClose} disabled={submitting}>
            Cancel
          </BaseButton>
          <BaseButton type="submit" variant="primary" disabled={submitting}>
            {submitting ? 'Creating…' : 'Add Column'}
          </BaseButton>
        </div>
      </form>
    </BaseModal>
  );
}
