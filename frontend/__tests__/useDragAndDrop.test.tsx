import { act, renderHook } from '@testing-library/react';
import type { DragEvent } from 'react';
import { useDragAndDrop } from '@/hooks/useDragAndDrop';
import { apiClient } from '@/lib/apiClient';
import { ApiError } from '@/lib/errors';
import type { BoardDetail, Card } from '@/types/api';

const refresh = jest.fn();
const handleError = jest.fn();

jest.mock('next/navigation', () => ({ useRouter: () => ({ refresh }) }));
jest.mock('@/context/AuthContext', () => ({ useAuth: () => ({ token: 'tok' }) }));
jest.mock('@/hooks/useErrorHandler', () => ({ useErrorHandler: () => ({ handleError }) }));
jest.mock('@/lib/apiClient', () => ({ apiClient: { patch: jest.fn() } }));

const patch = apiClient.patch as jest.Mock;

function card(id: string, columnId: string, order: number): Card {
  return {
    id,
    title: id,
    description: '',
    order,
    column_id: columnId,
    assignee_id: null,
    assignee: null,
    created_by_id: 'u',
    completed_at: null,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  };
}

function makeBoard(): BoardDetail {
  return {
    id: 'b',
    name: 'Board',
    team_id: 't',
    created_at: '2025-01-01T00:00:00Z',
    columns: [
      { id: 'todo', name: 'To Do', order: 1024, is_done: false, cards: [card('a', 'todo', 1024)] },
      {
        id: 'done',
        name: 'Done',
        order: 2048,
        is_done: true,
        cards: [card('x', 'done', 1024), card('y', 'done', 2048)],
      },
    ],
  };
}

const event = (): DragEvent =>
  ({
    preventDefault: jest.fn(),
    dataTransfer: { setData: jest.fn(), getData: jest.fn() },
  }) as never;

async function drop(
  result: { current: ReturnType<typeof useDragAndDrop> },
  columnId: string,
  index?: number,
): Promise<void> {
  act(() => result.current.handleDragStart(event(), 'a'));
  await act(async () => {
    await result.current.handleDrop(event(), columnId, index);
  });
}

describe('useDragAndDrop', () => {
  beforeEach(() => jest.clearAllMocks());

  it('moves optimistically, sends the computed order and keeps the server card', async () => {
    const stable = makeBoard();
    const server = { ...card('a', 'done', 1536), title: 'from server' };
    patch.mockResolvedValue({ card: server, rebalanced: false });
    const { result } = renderHook(() => useDragAndDrop(stable));
    await drop(result, 'done', 1);
    expect(patch).toHaveBeenCalledWith(
      '/api/cards/a/position',
      { column_id: 'done', order: 1536 },
      { token: 'tok' },
    );
    expect(result.current.board.columns[0].cards).toHaveLength(0);
    expect(result.current.board.columns[1].cards.map((c) => c.title)).toEqual([
      'x',
      'from server',
      'y',
    ]);
    expect(refresh).not.toHaveBeenCalled();
  });

  it('calls router.refresh() once when rebalanced is true', async () => {
    const stable = makeBoard();
    patch.mockResolvedValue({ card: card('a', 'done', 3072), rebalanced: true });
    const { result } = renderHook(() => useDragAndDrop(stable));
    await drop(result, 'done');
    expect(refresh).toHaveBeenCalledTimes(1);
  });

  it.each([
    ['403', new ApiError(403, 'Forbidden')],
    ['409', new ApiError(409, 'Order already in use')],
    ['status 0', new ApiError(0, 'Network error')],
  ])('restores the pre-drop state and reports the error on %s', async (_label, error) => {
    patch.mockRejectedValue(error);
    const before = makeBoard();
    const { result } = renderHook(() => useDragAndDrop(before));
    await drop(result, 'done', 0);
    expect(result.current.board).toEqual(before);
    expect(handleError).toHaveBeenCalledWith(error);
    expect(refresh).not.toHaveBeenCalled();
  });

  it('replaces its state when a new initialBoard arrives', () => {
    const first = makeBoard();
    const { result, rerender } = renderHook(({ b }) => useDragAndDrop(b), {
      initialProps: { b: first },
    });
    const next = { ...makeBoard(), name: 'Refreshed' };
    rerender({ b: next });
    expect(result.current.board.name).toBe('Refreshed');
  });

  it('prevents default on dragover so the column accepts a drop', () => {
    const stable = makeBoard();
    const { result } = renderHook(() => useDragAndDrop(stable));
    const e = event();
    result.current.handleDragOver(e);
    expect(e.preventDefault).toHaveBeenCalled();
  });
});
