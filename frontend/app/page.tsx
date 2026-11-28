import { cookies } from 'next/headers';
import { apiClient } from '@/lib/apiClient';
import BoardCard from '@/components/board/BoardCard';
import type { Board } from '@/types/api';
import DashboardClient from './DashboardClient';

export default async function DashboardPage() {
  const cookieStore = await cookies();
  const token = cookieStore.get('sevy_token')?.value ?? null;

  let boards: Board[] = [];
  try {
    boards = await apiClient.get<Board[]>('/api/boards', { token });
  } catch {
    // Show empty state
  }

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">My Boards</h1>
        <DashboardClient />
      </div>

      {boards.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-300 p-12 text-center">
          <p className="text-gray-500">No boards yet.</p>
          <p className="mt-1 text-sm text-gray-400">Create your first board to get started.</p>
        </div>
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {boards.map((board) => (
            <li key={board.id}>
              <BoardCard board={board} />
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
