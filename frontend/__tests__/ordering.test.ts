import { ORDER_STEP, computeOrder } from '@/lib/ordering';

describe('computeOrder', () => {
  it('returns ORDER_STEP for an empty column', () => {
    expect(ORDER_STEP).toBe(1024.0);
    expect(computeOrder(null, null)).toBe(1024.0);
  });

  it('appends at prev + ORDER_STEP', () => {
    expect(computeOrder(2048, null)).toBe(3072);
  });

  it('inserts at the head at next / 2', () => {
    expect(computeOrder(null, 1024)).toBe(512);
  });

  it('inserts between at the midpoint', () => {
    expect(computeOrder(1024, 2048)).toBe(1536);
  });

  it('stays strictly increasing and positive over 60 head insertions', () => {
    const list: number[] = [ORDER_STEP];
    for (let i = 0; i < 60; i += 1) {
      list.unshift(computeOrder(null, list[0]));
    }
    expect(list.every((v) => v > 0)).toBe(true);
    for (let i = 1; i < list.length; i += 1) {
      expect(list[i]).toBeGreaterThan(list[i - 1]);
    }
  });
});
