import { cookies } from 'next/headers';
import { apiClient } from '@/lib/apiClient';
import MyTaskRow from '@/components/card/MyTaskRow';
import type { CardListItem } from '@/types/api';

export default async function MyTasksPage() {
  const cookieStore = await cookies();
  const token = cookieStore.get('access_token')?.value ?? null;

  let tasks: CardListItem[] = [];
  try {
    tasks = await apiClient.get<CardListItem[]>('/api/users/me/tasks', { token });
  } catch {
    // Show empty state
  }

  // Group by board_name
  const groups = new Map<string, CardListItem[]>();
  for (const task of tasks) {
    const existing = groups.get(task.board_name) ?? [];
    groups.set(task.board_name, [...existing, task]);
  }

  return (
    <main className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold text-gray-800">My Tasks</h1>
      {tasks.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-300 p-12 text-center">
          <p className="text-gray-500">No tasks assigned to you.</p>
        </div>
      ) : (
        Array.from(groups.entries()).map(([boardName, cards]) => (
          <section key={boardName} className="mb-6">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500">{boardName}</h2>
            <ul className="space-y-2">
              {cards.map((card) => (
                <MyTaskRow key={card.id} card={card} />
              ))}
            </ul>
          </section>
        ))
      )}
    </main>
  );
}
