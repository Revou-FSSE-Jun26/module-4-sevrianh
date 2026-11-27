import { act, renderHook } from '@testing-library/react';
import { SEARCH_DEBOUNCE_MS, useCardSearch } from '@/hooks/useCardSearch';
import { apiClient } from '@/lib/apiClient';
import type { CardListItem } from '@/types/api';

const handleError = jest.fn();

jest.mock('@/context/AuthContext', () => ({ useAuth: () => ({ token: 'tok' }) }));
jest.mock('@/hooks/useErrorHandler', () => ({ useErrorHandler: () => ({ handleError }) }));
jest.mock('@/lib/apiClient', () => ({ apiClient: { get: jest.fn() } }));

const get = apiClient.get as jest.Mock;

function item(id: string, title: string): CardListItem {
  return {
    id,
    title,
    order: 1,
    column_id: 'c',
    column_name: 'To Do',
    board_id: 'b',
    board_name: 'B',
    assignee_id: null,
    assignee: null,
  };
}

async function advance(ms: number): Promise<void> {
  await act(async () => {
    jest.advanceTimersByTime(ms);
  });
}

describe('useCardSearch', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.clearAllMocks();
  });
  afterEach(() => jest.useRealTimers());

  it('sends 0 requests at 299 ms and 1 request at 300 ms', async () => {
    get.mockResolvedValue([item('1', 'Deploy')]);
    const { result } = renderHook(() => useCardSearch('deploy', 'b1'));
    await advance(SEARCH_DEBOUNCE_MS - 1);
    expect(get).not.toHaveBeenCalled();
    await advance(1);
    expect(get).toHaveBeenCalledTimes(1);
    expect(result.current.results).toHaveLength(1);
  });

  it('sends no request for empty or whitespace-only input', async () => {
    const { rerender } = renderHook(({ t }) => useCardSearch(t, 'b1'), {
      initialProps: { t: '' },
    });
    await advance(SEARCH_DEBOUNCE_MS * 2);
    rerender({ t: '   ' });
    await advance(SEARCH_DEBOUNCE_MS * 2);
    expect(get).not.toHaveBeenCalled();
  });

  it('sends the trimmed term with board_id for the default scope', async () => {
    get.mockResolvedValue([]);
    renderHook(() => useCardSearch('  deploy ', 'b1'));
    await advance(SEARCH_DEBOUNCE_MS);
    expect(get).toHaveBeenCalledWith('/api/cards?q=deploy&board_id=b1', { token: 'tok' });
  });

  it('omits board_id for the q-only scope', async () => {
    get.mockResolvedValue([]);
    renderHook(() => useCardSearch('deploy'));
    await advance(SEARCH_DEBOUNCE_MS);
    const url = get.mock.calls[0][0] as string;
    expect(url).toBe('/api/cards?q=deploy');
    expect(url).not.toContain('board_id');
  });

  it('sends one request for "dep" then "deploy" typed within 300 ms', async () => {
    get.mockResolvedValue([]);
    const { rerender } = renderHook(({ t }) => useCardSearch(t, 'b1'), {
      initialProps: { t: 'dep' },
    });
    await advance(100);
    rerender({ t: 'deploy' });
    await advance(SEARCH_DEBOUNCE_MS);
    expect(get).toHaveBeenCalledTimes(1);
    expect(get).toHaveBeenCalledWith('/api/cards?q=deploy&board_id=b1', { token: 'tok' });
  });

  it('ignores a stale response when a newer term is pending', async () => {
    let resolveFirst: (v: CardListItem[]) => void = () => undefined;
    get.mockReturnValueOnce(new Promise<CardListItem[]>((r) => (resolveFirst = r)));
    const { result, rerender } = renderHook(({ t }) => useCardSearch(t, 'b1'), {
      initialProps: { t: 'old' },
    });
    await advance(SEARCH_DEBOUNCE_MS);
    rerender({ t: 'new' });
    await act(async () => {
      resolveFirst([item('1', 'old card')]);
    });
    expect(result.current.results).toEqual([]);
  });

  it('clears results when the input becomes empty', async () => {
    get.mockResolvedValue([item('1', 'Deploy')]);
    const { result, rerender } = renderHook(({ t }) => useCardSearch(t, 'b1'), {
      initialProps: { t: 'deploy' },
    });
    await advance(SEARCH_DEBOUNCE_MS);
    expect(result.current.results).toHaveLength(1);
    rerender({ t: '' });
    await advance(SEARCH_DEBOUNCE_MS);
    expect(result.current.results).toEqual([]);
  });

  it('routes a request failure to the error handler', async () => {
    const error = new Error('boom');
    get.mockRejectedValue(error);
    renderHook(() => useCardSearch('deploy', 'b1'));
    await advance(SEARCH_DEBOUNCE_MS);
    expect(handleError).toHaveBeenCalledWith(error);
  });
});
