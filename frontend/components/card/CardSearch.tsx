'use client';

import { useState } from 'react';
import { useCardSearch } from '@/hooks/useCardSearch';
import BaseBadge from '@/components/shared/BaseBadge';
import Link from 'next/link';

interface Props {
  boardId: string;
}

export default function CardSearch({ boardId }: Props) {
  const [term, setTerm] = useState('');
  const { results, isLoading } = useCardSearch(term, boardId);

  return (
    <div className="relative mb-4 max-w-sm">
      <label htmlFor="card-search" className="sr-only">Search cards</label>
      <input
        id="card-search"
        type="search"
        value={term}
        onChange={(e) => setTerm(e.target.value)}
        maxLength={100}
        placeholder="Search cards…"
        className="min-h-11 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      {isLoading && (
        <p className="mt-1 text-xs text-gray-400">Searching…</p>
      )}
      {term.trim() && !isLoading && results.length === 0 && (
        <p className="mt-1 text-xs text-gray-500">No cards found.</p>
      )}
      {results.length > 0 && (
        <ul className="absolute z-10 mt-1 w-full rounded-lg border border-gray-200 bg-white shadow-lg">
          {results.map((card) => (
            <li key={card.id}>
              <Link
                href={`/boards/${card.board_id}?card=${card.id}`}
                className="flex items-center justify-between gap-2 px-3 py-2 text-sm hover:bg-gray-50"
              >
                <span className="truncate font-medium text-gray-800">{card.title}</span>
                <BaseBadge>{card.column_name}</BaseBadge>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
