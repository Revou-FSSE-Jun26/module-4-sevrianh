export const ORDER_STEP = 1024.0;

/** Order for a Card dropped between `prev` and `next` (same rules as backend BE-14). */
export function computeOrder(prev: number | null, next: number | null): number {
  if (prev === null && next === null) return ORDER_STEP;
  if (next === null) return (prev as number) + ORDER_STEP;
  if (prev === null) return next / 2;
  return (prev + next) / 2;
}
