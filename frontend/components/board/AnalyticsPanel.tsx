'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useErrorHandler } from '@/hooks/useErrorHandler';
import { apiClient } from '@/lib/apiClient';
import type { AnalyticsData } from '@/types/api';

interface Props {
  boardId: string;
}

export default function AnalyticsPanel({ boardId }: Props) {
  const { token } = useAuth();
  const { handleError } = useErrorHandler();
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    apiClient
      .get<AnalyticsData>(`/api/boards/${boardId}/analytics`, { token })
      .then(setData)
      .catch((err: unknown) => handleError(err))
      .finally(() => setLoading(false));
  }, [boardId, token, handleError]);

  if (loading) return <p className="text-sm text-gray-400">Loading analytics…</p>;
  if (!data) return null;

  return (
    <section aria-label="Board Analytics" className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <h2 className="mb-3 text-base font-semibold text-gray-700">Analytics</h2>

      <div className="mb-4">
        <p className="text-sm text-gray-600">
          Completed this week: <span className="font-bold text-green-600">{data.completed_this_week}</span>
        </p>
        <p className="text-xs text-gray-400">
          {data.start_date} → {data.end_date}
        </p>
      </div>

      <div className="mb-4">
        <h3 className="mb-2 text-sm font-medium text-gray-600">Cards per Column</h3>
        <ul className="space-y-1">
          {data.cards_per_column.map((col) => (
            <li key={col.column_id} className="flex justify-between text-sm">
              <span className="text-gray-700">{col.column_name}</span>
              <span className="font-medium text-gray-800">{col.count}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="mb-4">
        <h3 className="mb-2 text-sm font-medium text-gray-600">Member Activity</h3>
        <ul className="space-y-1">
          {data.member_activity.map((m) => (
            <li key={m.user_id} className="flex justify-between text-sm">
              <span className="text-gray-700">{m.name} <span className="text-gray-400">@{m.username}</span></span>
              <span className="font-medium text-gray-800">{m.event_count} events</span>
            </li>
          ))}
        </ul>
      </div>

      <div>
        <h3 className="mb-2 text-sm font-medium text-gray-600">Activity per Day</h3>
        <ul className="space-y-1">
          {data.activity_per_day.map((d) => (
            <li key={d.date} className="flex justify-between text-sm">
              <span className="text-gray-500">{d.date}</span>
              <span className="font-medium text-gray-800">{d.count}</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
