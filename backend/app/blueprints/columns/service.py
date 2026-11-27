"""Columns business rules and FLOAT reordering (BE-09, BE-14, R5, R24). No flask imports."""
import uuid
from typing import Any
from uuid import UUID

from sqlalchemy import func

from app.blueprints.boards.service import (
    require_team_admin_service,
    require_team_member_service,
)
from app.exceptions import (
    ColumnNotFoundException,
    InvalidTargetColumnError,
    OrderConflictError,
)
from app.extensions import db
from app.models import BoardColumnEntity, BoardEntity, CardEntity
from app.utils.ordering import (
    ORDER_STEP,
    append_order,
    has_small_gap,
    rebalanced_orders,
    temporary_orders,
)
from app.utils.time import utc_now


def _to_uuid(value: Any) -> UUID:
    return value if isinstance(value, UUID) else uuid.UUID(str(value))


def _load_column(column_id: Any) -> BoardColumnEntity:
    column = db.session.get(BoardColumnEntity, _to_uuid(column_id))
    if column is None or column.deleted_at is not None:
        raise ColumnNotFoundException()
    return column


def _lock_board_and_columns(board_id: UUID) -> list[BoardColumnEntity]:
    """Lock the parent Board row, then all active Columns in deterministic order (BE-14)."""
    db.session.query(BoardEntity).filter(BoardEntity.id == board_id).with_for_update().one()
    return (
        db.session.query(BoardColumnEntity)
        .filter(BoardColumnEntity.board_id == board_id)
        .filter(BoardColumnEntity.deleted_at.is_(None))
        .order_by(BoardColumnEntity.order.asc(), BoardColumnEntity.id.asc())
        .with_for_update()
        .all()
    )


def _apply_is_done_transition(column_id: UUID, old_is_done: bool, new_is_done: bool) -> None:
    """Update `completed_at` on non-deleted Cards when `is_done` changes (R24.6)."""
    if new_is_done == old_is_done:
        return
    now = utc_now()
    query = (
        db.session.query(CardEntity)
        .filter(CardEntity.column_id == column_id)
        .filter(CardEntity.deleted_at.is_(None))
    )
    if new_is_done:
        query.filter(CardEntity.completed_at.is_(None)).update(
            {CardEntity.completed_at: now, CardEntity.updated_at: now},
            synchronize_session=False,
        )
    else:
        query.filter(CardEntity.completed_at.is_not(None)).update(
            {CardEntity.completed_at: None, CardEntity.updated_at: now},
            synchronize_session=False,
        )


def _rebalance_columns(ordered: list[BoardColumnEntity]) -> None:
    """Two-phase rebalance so no statement hits the partial unique index (BE-14)."""
    orders = [col.order for col in ordered]
    # Ensure phase-1 values stay above both current max and phase-2 max regardless of flush order.
    phase1_vals = temporary_orders([*orders, ORDER_STEP * len(ordered)], len(ordered))
    for col, temp_val in zip(ordered, phase1_vals):
        col.order = temp_val
    db.session.flush()
    for col, final_val in zip(ordered, rebalanced_orders(len(ordered))):
        col.order = final_val
    db.session.flush()


def create_column_service(
    board_id: Any, data: dict[str, Any], user_id: Any
) -> BoardColumnEntity:
    """Append a Column to a Board for a Member or Admin (R5.1-R5.3)."""
    board = require_team_member_service(board_id, user_id)
    try:
        db.session.query(BoardEntity).filter(BoardEntity.id == board.id).with_for_update().one()
        last_order = (
            db.session.query(func.max(BoardColumnEntity.order))
            .filter(BoardColumnEntity.board_id == board.id)
            .filter(BoardColumnEntity.deleted_at.is_(None))
            .scalar()
        )
        column = BoardColumnEntity(
            board_id=board.id,
            name=data['name'],
            order=append_order(last_order),
            is_done=data.get('is_done', False),
        )
        db.session.add(column)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return column


def update_column_service(
    column_id: Any, data: dict[str, Any], user_id: Any
) -> BoardColumnEntity:
    """Rename or toggle `is_done` on a Column (Admin only, R5.5, R24.6)."""
    column = _load_column(column_id)
    require_team_admin_service(column.board_id, user_id)
    old_is_done = column.is_done
    try:
        if 'name' in data:
            column.name = data['name']
        if 'is_done' in data:
            column.is_done = data['is_done']
            _apply_is_done_transition(column.id, old_is_done, data['is_done'])
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return column


def delete_column_service(column_id: Any, user_id: Any) -> dict[str, str]:
    """Hard-delete a Column and cascade-delete its Cards and Comments (Admin only, R5.10)."""
    column = _load_column(column_id)
    require_team_admin_service(column.board_id, user_id)
    deleted_id = str(column.id)
    try:
        db.session.delete(column)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return {'id': deleted_id}


def reorder_column_service(
    board_id: Any, data: dict[str, Any], user_id: Any
) -> dict[str, Any]:
    """Move a Column to `order`, rejecting conflicts (409) and rebalancing small gaps (BE-14)."""
    board = require_team_admin_service(board_id, user_id)
    target_id = _to_uuid(data['column_id'])
    new_order = float(data['order'])
    try:
        siblings = _lock_board_and_columns(board.id)
        target = next((col for col in siblings if col.id == target_id), None)
        if target is None:
            raise InvalidTargetColumnError()
        if any(col.order == new_order for col in siblings if col.id != target.id):
            raise OrderConflictError()
        target.order = new_order
        db.session.flush()
        ordered = sorted(siblings, key=lambda col: (col.order, col.id))
        rebalanced = has_small_gap([col.order for col in ordered])
        if rebalanced:
            _rebalance_columns(ordered)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return {'column': target, 'rebalanced': rebalanced}
