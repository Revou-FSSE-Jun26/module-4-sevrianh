import { act, renderHook } from '@testing-library/react';
import { useDebouncedValue } from '@/hooks/useDebouncedValue';

describe('useDebouncedValue', () => {
  beforeEach(() => jest.useFakeTimers());
  afterEach(() => jest.useRealTimers());

  it('returns the initial value immediately', () => {
    const { result } = renderHook(() => useDebouncedValue('a', 300));
    expect(result.current).toBe('a');
  });

  it('does not update at 299 ms and updates at 300 ms', () => {
    const { result, rerender } = renderHook(({ v }) => useDebouncedValue(v, 300), {
      initialProps: { v: 'a' },
    });
    rerender({ v: 'ab' });
    act(() => {
      jest.advanceTimersByTime(299);
    });
    expect(result.current).toBe('a');
    act(() => {
      jest.advanceTimersByTime(1);
    });
    expect(result.current).toBe('ab');
  });

  it('restarts the delay when the value changes again', () => {
    const { result, rerender } = renderHook(({ v }) => useDebouncedValue(v, 300), {
      initialProps: { v: 'a' },
    });
    rerender({ v: 'ab' });
    act(() => {
      jest.advanceTimersByTime(200);
    });
    rerender({ v: 'abc' });
    act(() => {
      jest.advanceTimersByTime(200);
    });
    expect(result.current).toBe('a');
    act(() => {
      jest.advanceTimersByTime(100);
    });
    expect(result.current).toBe('abc');
  });
});
