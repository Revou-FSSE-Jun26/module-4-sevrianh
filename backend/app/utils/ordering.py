"""Pure FLOAT order allocation helpers (backend.md BE-14).

No database or Flask access: callers pass the active siblings' orders in.
"""
from typing import Optional, Sequence

ORDER_STEP = 1024.0
MIN_GAP = 1e-6


def first_order() -> float:
    """Order of the first item in an empty parent."""
    return ORDER_STEP


def append_order(last_order: Optional[float]) -> float:
    """Order for a new last item; ``None`` means the parent has no active sibling."""
    if last_order is None:
        return first_order()
    return last_order + ORDER_STEP


def head_order(first_order_value: Optional[float]) -> float:
    """Order for an item inserted before the current first active sibling."""
    if first_order_value is None:
        return first_order()
    return first_order_value / 2


def between_order(prev_order: float, next_order: float) -> float:
    """Order for an item inserted between two adjacent active siblings."""
    return (prev_order + next_order) / 2


def has_small_gap(orders: Sequence[float]) -> bool:
    """True if any two adjacent orders (ascending) differ by less than MIN_GAP."""
    ordered = sorted(orders)
    return any(b - a < MIN_GAP for a, b in zip(ordered, ordered[1:]))


def rebalanced_orders(count: int) -> list[float]:
    """Final values for a rebalance of ``count`` siblings: 1024.0, 2048.0, ..."""
    return [ORDER_STEP * (i + 1) for i in range(count)]


def temporary_orders(current_orders: Sequence[float], count: int) -> list[float]:
    """Phase-1 values above the current maximum: ``max + ORDER_STEP * (i + 1)``."""
    top = max(current_orders) if current_orders else 0.0
    return [top + ORDER_STEP * (i + 1) for i in range(count)]
