'use client';

import { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useErrorHandler } from '@/hooks/useErrorHandler';
import { apiClient } from '@/lib/apiClient';
import BaseButton from '@/components/shared/BaseButton';

interface Props {
  columnId: string;
  name: string;
  cardCount: number;
  isAdmin: boolean;
  onRenamed: (name: string) => void;
  onDeleted: () => void;
}

export default function ColumnHeader({ columnId, name, cardCount, isAdmin, onRenamed, onDeleted }: Props) {
  const { token } = useAuth();
  const { handleError } = useErrorHandler();
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(name);

  async function handleRename(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = draft.trim();
    if (!trimmed || trimmed === name) { setEditing(false); return; }
    try {
      await apiClient.patch(`/api/columns/${columnId}`, { name: trimmed }, { token });
      onRenamed(trimmed);
    } catch (err) {
      handleError(err);
    }
    setEditing(false);
  }

  async function handleDelete() {
    if (!confirm(`Delete column "${name}" and all its cards?`)) return;
    try {
      await apiClient.delete(`/api/columns/${columnId}`, { token });
      onDeleted();
    } catch (err) {
      handleError(err);
    }
  }

  return (
    <div className="mb-2 flex items-center justify-between">
      {editing ? (
        <form onSubmit={handleRename} className="flex flex-1 gap-1">
          <input
            autoFocus
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            className="flex-1 rounded border border-gray-300 px-2 py-1 text-sm"
            maxLength={100}
          />
          <BaseButton type="submit" variant="primary">Save</BaseButton>
          <BaseButton type="button" variant="secondary" onClick={() => setEditing(false)}>✕</BaseButton>
        </form>
      ) : (
        <>
          <h3 className="font-semibold text-gray-700">
            {name}
            <span className="ml-2 text-xs font-normal text-gray-400">({cardCount})</span>
          </h3>
          {isAdmin && (
            <div className="flex gap-1">
              <BaseButton
                variant="secondary"
                onClick={() => { setDraft(name); setEditing(true); }}
                aria-label={`Rename column ${name}`}
              >
                ✏️
              </BaseButton>
              <BaseButton
                variant="secondary"
                onClick={handleDelete}
                aria-label={`Delete column ${name}`}
              >
                🗑️
              </BaseButton>
            </div>
          )}
        </>
      )}
    </div>
  );
}
