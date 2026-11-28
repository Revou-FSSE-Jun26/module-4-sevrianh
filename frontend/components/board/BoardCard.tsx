import Link from 'next/link';
import type { Board } from '@/types/api';

interface Props {
  board: Board;
}

export default function BoardCard({ board }: Props) {
  return (
    <Link
      href={`/boards/${board.id}`}
      className="block rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      aria-label={`Open board ${board.name}`}
    >
      <h2 className="truncate text-lg font-semibold text-gray-800">{board.name}</h2>
      <p className="mt-1 text-xs text-gray-400">
        Created {new Date(board.created_at).toLocaleDateString()}
      </p>
    </Link>
  );
}
