import Link from 'next/link';
import BaseBadge from '@/components/shared/BaseBadge';
import type { CardListItem } from '@/types/api';

interface Props {
  card: CardListItem;
}

export default function MyTaskRow({ card }: Props) {
  return (
    <li className="flex items-center justify-between gap-3 rounded-lg border border-gray-200 bg-white px-4 py-3 shadow-sm">
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-gray-800">{card.title}</p>
        <div className="mt-1 flex items-center gap-2">
          <span className="text-xs text-gray-400">{card.board_name}</span>
          <BaseBadge>{card.column_name}</BaseBadge>
        </div>
      </div>
      <Link
        href={`/boards/${card.board_id}?card=${card.id}`}
        className="shrink-0 rounded bg-blue-500 px-3 py-1 text-xs font-medium text-white hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        View
      </Link>
    </li>
  );
}
