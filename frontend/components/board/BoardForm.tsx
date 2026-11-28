'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { useErrorHandler } from '@/hooks/useErrorHandler';
import { apiClient } from '@/lib/apiClient';
import BaseButton from '@/components/shared/BaseButton';
import type { Board } from '@/types/api';

interface Props {
  onClose: () => void;
}

export default function BoardForm({ onClose }: Props) {
  const router = useRouter();
  const { token } = useAuth();
  const { handleError } = useErrorHandler();
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) { setError('Board name is required.'); return; }
    if (trimmed.length > 100) { setError('Board name must be 100 characters or fewer.'); return; }
    setError('');
    setSubmitting(true);
    try {
      await apiClient.post<Board>('/api/boards', { name: trimmed }, { token });
      router.refresh();
      onClose();
    } catch (err) {
      handleError(err);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <div className="mb-4">
        <label htmlFor="board-name" className="mb-1 block text-sm font-medium text-gray-700">
          Board Name <span aria-hidden="true">*</span>
        </label>
        <input
          id="board-name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          maxLength={100}
          required
          className="min-h-11 w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="e.g. Project Alpha"
        />
        {error && <p role="alert" className="mt-1 text-xs text-red-600">{error}</p>}
      </div>
      <div className="flex justify-end gap-2">
        <BaseButton type="button" variant="secondary" onClick={onClose} disabled={submitting}>
          Cancel
        </BaseButton>
        <BaseButton type="submit" variant="primary" disabled={submitting}>
          {submitting ? 'Creating…' : 'Create Board'}
        </BaseButton>
      </div>
    </form>
  );
}
