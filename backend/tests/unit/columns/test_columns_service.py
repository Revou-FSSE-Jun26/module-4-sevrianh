"""Columns service tests: success, failure, cascade, is_done and PG rebalance (R5, R24, R28)."""
import uuid
from datetime import timedelta

import pytest

from app.blueprints.columns import service as svc
from app.exceptions import (
    AdminAccessRequiredError,
    BoardNotFoundException,
    ColumnNotFoundException,
    InvalidTargetColumnError,
    OrderConflictError,
    TeamAccessDeniedError,
)
from app.extensions import db
from app.models import (
    BoardColumnEntity,
    CardCommentEntity,
    CardEntity,
    NotificationEntity,
)
from app.utils.ordering import MIN_GAP, ORDER_STEP, has_small_gap, head_order
from app.utils.time import utc_now


def _fail_commit(monkeypatch):
    def boom():
        raise RuntimeError('commit failed')

    monkeypatch.setattr(db.session, 'commit', boom)


# ---- create_column_service -----------------------------------------------------------------

def test_create_column_service_appends_orders_and_defaults_is_done(world):
    c1 = svc.create_column_service(world.board.id, {'name': 'To Do'}, world.member.id)
    c2 = svc.create_column_service(
        world.board.id, {'name': 'Done', 'is_done': True}, world.admin.id
    )
    assert c1.order == 1024.0 and c1.is_done is False
    assert c2.order == 2048.0 and c2.is_done is True


def test_create_column_service_rejects_missing_board_and_non_member(world):
    with pytest.raises(BoardNotFoundException):
        svc.create_column_service(uuid.uuid4(), {'name': 'X'}, world.admin.id)
    with pytest.raises(TeamAccessDeniedError):
        svc.create_column_service(world.board.id, {'name': 'X'}, world.outsider.id)


def test_create_column_service_rolls_back_on_commit_error(world, monkeypatch):
    _fail_commit(monkeypatch)
    with pytest.raises(RuntimeError):
        svc.create_column_service(world.board.id, {'name': 'Lost'}, world.admin.id)
    monkeypatch.undo()
    assert db.session.query(BoardColumnEntity).count() == 0


# ---- update_column_service -----------------------------------------------------------------

def test_update_column_service_renames_for_admin(world, factory):
    col = factory.column(world.board, name='Old')
    factory.session.commit()
    updated = svc.update_column_service(col.id, {'name': 'New'}, world.admin.id)
    assert updated.name == 'New'


def test_update_column_service_is_done_toggle_sets_and_clears_completed_at(world, factory):
    col = factory.column(world.board, is_done=False)
    past = utc_now() - timedelta(days=2)
    open_card = factory.card(col, world.admin, order=1024.0, completed_at=None)
    already_done = factory.card(col, world.admin, order=2048.0, completed_at=past)
    deleted_card = factory.card(
        col, world.admin, order=3072.0, completed_at=None, deleted_at=utc_now()
    )
    factory.session.commit()

    # false -> true sets completed_at only on non-deleted cards with completed_at IS NULL
    svc.update_column_service(col.id, {'is_done': True}, world.admin.id)
    assert db.session.get(CardEntity, open_card.id).completed_at is not None
    assert db.session.get(CardEntity, already_done.id).completed_at == past
    assert db.session.get(CardEntity, deleted_card.id).completed_at is None

    # true -> true leaves timestamps unchanged
    before = db.session.get(CardEntity, open_card.id).completed_at
    svc.update_column_service(col.id, {'is_done': True}, world.admin.id)
    assert db.session.get(CardEntity, open_card.id).completed_at == before

    # true -> false clears completed_at on active cards
    svc.update_column_service(col.id, {'is_done': False}, world.admin.id)
    assert db.session.get(CardEntity, open_card.id).completed_at is None
    assert db.session.get(CardEntity, already_done.id).completed_at is None


def test_update_column_service_rejects_missing_member_and_non_member(world, factory):
    col = factory.column(world.board, name='Keep')
    factory.session.commit()
    with pytest.raises(ColumnNotFoundException):
        svc.update_column_service(uuid.uuid4(), {'name': 'X'}, world.admin.id)
    with pytest.raises(AdminAccessRequiredError):
        svc.update_column_service(col.id, {'name': 'X'}, world.member.id)
    with pytest.raises(TeamAccessDeniedError):
        svc.update_column_service(col.id, {'is_done': True}, world.outsider.id)
    assert db.session.get(BoardColumnEntity, col.id).name == 'Keep'


def test_update_column_service_rolls_back_on_commit_error(world, factory, monkeypatch):
    col = factory.column(world.board, name='Keep')
    factory.session.commit()
    _fail_commit(monkeypatch)
    with pytest.raises(RuntimeError):
        svc.update_column_service(col.id, {'name': 'Lost'}, world.admin.id)
    monkeypatch.undo()
    assert db.session.get(BoardColumnEntity, col.id).name == 'Keep'


# ---- delete_column_service -----------------------------------------------------------------

def test_delete_column_service_cascades_children_and_keeps_other_orders(world, factory):
    c1 = factory.column(world.board, name='C1', order=1024.0)
    c2 = factory.column(world.board, name='C2', order=2048.0)
    c3 = factory.column(world.board, name='C3', order=3072.0)
    card = factory.card(c2, world.admin)
    comment = factory.comment(card, world.admin, content='hi @col_member')
    db.session.add(NotificationEntity(
        recipient_id=world.member.id, comment_id=comment.id, type='mention', message='msg',
    ))
    factory.session.commit()

    res = svc.delete_column_service(c2.id, world.admin.id)
    assert res == {'id': str(c2.id)}
    assert db.session.get(BoardColumnEntity, c2.id) is None
    assert db.session.query(CardEntity).count() == 0
    assert db.session.query(CardCommentEntity).count() == 0
    assert db.session.query(NotificationEntity).count() == 0
    assert db.session.get(BoardColumnEntity, c1.id).order == 1024.0
    assert db.session.get(BoardColumnEntity, c3.id).order == 3072.0


def test_delete_column_service_rejects_missing_member_and_non_member(world, factory):
    col = factory.column(world.board)
    factory.session.commit()
    with pytest.raises(ColumnNotFoundException):
        svc.delete_column_service(uuid.uuid4(), world.admin.id)
    with pytest.raises(AdminAccessRequiredError):
        svc.delete_column_service(col.id, world.member.id)
    with pytest.raises(TeamAccessDeniedError):
        svc.delete_column_service(col.id, world.outsider.id)
    assert db.session.get(BoardColumnEntity, col.id) is not None


def test_delete_column_service_rolls_back_on_commit_error(world, factory, monkeypatch):
    col = factory.column(world.board)
    factory.session.commit()
    _fail_commit(monkeypatch)
    with pytest.raises(RuntimeError):
        svc.delete_column_service(col.id, world.admin.id)
    monkeypatch.undo()
    assert db.session.get(BoardColumnEntity, col.id) is not None


# ---- reorder_column_service ----------------------------------------------------------------

def test_reorder_column_service_moves_and_is_idempotent(world, factory):
    c1 = factory.column(world.board, name='C1', order=1024.0)
    c2 = factory.column(world.board, name='C2', order=2048.0)
    c3 = factory.column(world.board, name='C3', order=3072.0)
    factory.session.commit()

    res = svc.reorder_column_service(
        world.board.id, {'column_id': c3.id, 'order': 1536.0}, world.admin.id
    )
    assert res['rebalanced'] is False and res['column'].order == 1536.0
    # Repeating the identical reorder is idempotent (moved column excluded from conflict check)
    repeat = svc.reorder_column_service(
        world.board.id, {'column_id': c3.id, 'order': 1536.0}, world.admin.id
    )
    assert repeat['rebalanced'] is False and repeat['column'].order == 1536.0
    ordered = (
        db.session.query(BoardColumnEntity)
        .filter_by(board_id=world.board.id)
        .order_by(BoardColumnEntity.order.asc())
        .all()
    )
    assert [c.id for c in ordered] == [c1.id, c3.id, c2.id]


def test_reorder_column_service_rebalances_50_siblings_on_postgresql(world, factory):
    cols = [
        factory.column(world.board, name=f'Col {i}', order=1024.0 * (i + 1))
        for i in range(50)
    ]
    factory.session.commit()

    # Move last column into a sub-MIN_GAP slot just after Col 0 (1024.0)
    target = cols[-1]
    res = svc.reorder_column_service(
        world.board.id,
        {'column_id': target.id, 'order': 1024.0 + MIN_GAP / 2},
        world.admin.id,
    )
    assert res['rebalanced'] is True
    assert res['column'].order == 2048.0

    rows = (
        db.session.query(BoardColumnEntity)
        .filter_by(board_id=world.board.id)
        .order_by(BoardColumnEntity.order.asc())
        .all()
    )
    expected_ids = [cols[0].id, target.id] + [c.id for c in cols[1:-1]]
    assert [r.id for r in rows] == expected_ids
    assert [r.order for r in rows] == [ORDER_STEP * (i + 1) for i in range(50)]


def test_reorder_column_service_60_head_insertions_stay_positive_and_increasing(world, factory):
    first = factory.column(world.board, name='Anchor', order=1024.0)
    mover = factory.column(world.board, name='Mover', order=2048.0)
    factory.session.commit()
    rebalanced_seen = False

    for _ in range(60):
        current = (
            db.session.query(BoardColumnEntity)
            .filter_by(board_id=world.board.id)
            .order_by(BoardColumnEntity.order.asc())
            .all()
        )
        new_order = head_order(current[0].order)
        # Swap whichever column is second to the head so repeated halving shrinks the head gap
        target = current[1] if current[0].id == first.id else current[0]
        if target.id == current[0].id:
            target = current[1]
        res = svc.reorder_column_service(
            world.board.id, {'column_id': target.id, 'order': new_order}, world.admin.id
        )
        rebalanced_seen = rebalanced_seen or res['rebalanced']
        after = (
            db.session.query(BoardColumnEntity)
            .filter_by(board_id=world.board.id)
            .order_by(BoardColumnEntity.order.asc())
            .all()
        )
        orders = [c.order for c in after]
        assert all(o > 0 for o in orders)
        assert orders[1] > orders[0]
        assert not has_small_gap(orders)
    assert mover.id != first.id and rebalanced_seen


def test_reorder_column_service_rejects_conflict_invalid_target_and_unauthorized(world, factory):
    c1 = factory.column(world.board, order=1024.0)
    c2 = factory.column(world.board, order=2048.0)
    foreign = factory.column(world.board_b, order=1024.0)
    factory.session.commit()

    with pytest.raises(OrderConflictError):
        svc.reorder_column_service(
            world.board.id, {'column_id': c2.id, 'order': 1024.0}, world.admin.id
        )
    assert db.session.get(BoardColumnEntity, c2.id).order == 2048.0

    with pytest.raises(InvalidTargetColumnError):
        svc.reorder_column_service(
            world.board.id, {'column_id': uuid.uuid4(), 'order': 512.0}, world.admin.id
        )
    with pytest.raises(InvalidTargetColumnError):
        svc.reorder_column_service(
            world.board.id, {'column_id': foreign.id, 'order': 512.0}, world.admin.id
        )
    with pytest.raises(BoardNotFoundException):
        svc.reorder_column_service(
            uuid.uuid4(), {'column_id': c1.id, 'order': 512.0}, world.admin.id
        )
    with pytest.raises(AdminAccessRequiredError):
        svc.reorder_column_service(
            world.board.id, {'column_id': c2.id, 'order': 512.0}, world.member.id
        )
    with pytest.raises(TeamAccessDeniedError):
        svc.reorder_column_service(
            world.board.id, {'column_id': c2.id, 'order': 512.0}, world.outsider.id
        )


def test_reorder_column_service_rolls_back_on_commit_error(world, factory, monkeypatch):
    c1 = factory.column(world.board, order=1024.0)
    factory.session.commit()
    _fail_commit(monkeypatch)
    with pytest.raises(RuntimeError):
        svc.reorder_column_service(
            world.board.id, {'column_id': c1.id, 'order': 512.0}, world.admin.id
        )
    monkeypatch.undo()
    assert db.session.get(BoardColumnEntity, c1.id).order == 1024.0
