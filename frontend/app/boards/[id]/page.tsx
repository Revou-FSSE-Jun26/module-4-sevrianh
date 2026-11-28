import { cookies } from 'next/headers';
import { notFound } from 'next/navigation';
import { apiClient } from '@/lib/apiClient';
import KanbanBoard from '@/components/board/KanbanBoard';
import CardSearch from '@/components/card/CardSearch';
import AnalyticsPanel from '@/components/board/AnalyticsPanel';
import type { BoardDetail, TeamMember } from '@/types/api';

interface Props {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ invite?: string }>;
}

export default async function BoardDetailPage({ params, searchParams }: Props) {
  const { id } = await params;
  const { invite } = await searchParams;
  const isGuest = Boolean(invite);

  const cookieStore = await cookies();
  const token = isGuest ? null : (cookieStore.get('access_token')?.value ?? null);
  const opts = isGuest ? { inviteToken: invite } : { token };

  let board: BoardDetail;
  try {
    board = await apiClient.get<BoardDetail>(`/api/boards/${id}`, opts);
  } catch {
    notFound();
  }

  let members: TeamMember[] = [];
  let role: 'admin' | 'member' | 'guest' = 'guest';

  if (!isGuest && token) {
    try {
      members = await apiClient.get<TeamMember[]>(`/api/boards/${id}/members`, { token });
      const me = members.find((m) => m.role === 'admin');
      role = me ? 'admin' : 'member';
    } catch {
      role = 'member';
    }
  }

  const isAdmin = role === 'admin';

  return (
    <main className="flex h-full flex-col px-4 py-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-800">{board.name}</h1>
        {isGuest && (
          <span className="rounded bg-yellow-100 px-2 py-1 text-xs font-medium text-yellow-700">
            Guest — Read only
          </span>
        )}
      </div>

      {!isGuest && (
        <CardSearch boardId={id} />
      )}

      <KanbanBoard
        initialBoard={board}
        isReadOnly={isGuest}
        isAdmin={isAdmin}
        members={members}
      />

      {isAdmin && (
        <div className="mt-6 max-w-lg">
          <AnalyticsPanel boardId={id} />
        </div>
      )}
    </main>
  );
}
