from app.utils.ordering import (
    MIN_GAP,
    ORDER_STEP,
    append_order,
    between_order,
    first_order,
    has_small_gap,
    head_order,
    rebalanced_orders,
    temporary_orders,
)


def test_constants_match_guideline():
    assert ORDER_STEP == 1024.0
    assert MIN_GAP == 1e-6


def test_first_order_is_step():
    assert first_order() == 1024.0
    assert append_order(None) == 1024.0
    assert head_order(None) == 1024.0


def test_append_adds_step_to_last():
    assert append_order(2048.0) == 3072.0


def test_head_halves_first():
    assert head_order(1024.0) == 512.0


def test_between_is_midpoint():
    assert between_order(1024.0, 2048.0) == 1536.0


def test_has_small_gap_detects_close_neighbours():
    assert not has_small_gap([])
    assert not has_small_gap([1024.0])
    assert not has_small_gap([1024.0, 2048.0])
    assert has_small_gap([1.0, 1.0 + MIN_GAP / 2, 5.0])
    assert has_small_gap([5.0, 1.0, 1.0])


def test_rebalanced_orders_sequence():
    assert rebalanced_orders(0) == []
    assert rebalanced_orders(3) == [1024.0, 2048.0, 3072.0]


def test_temporary_orders_start_above_maximum():
    assert temporary_orders([1.0, 2.0], 2) == [2.0 + 1024.0, 2.0 + 2048.0]
    assert temporary_orders([], 2) == [1024.0, 2048.0]


def test_head_insertion_60_times_stays_positive_and_increasing_with_rebalance():
    orders = [first_order()]
    rebalanced = False
    for _ in range(60):
        new = head_order(orders[0])
        orders = [new] + orders
        if has_small_gap(orders):
            orders = rebalanced_orders(len(orders))
            rebalanced = True
        assert all(o > 0 for o in orders)
        assert all(b > a for a, b in zip(orders, orders[1:]))
        assert not has_small_gap(orders)
    assert rebalanced
