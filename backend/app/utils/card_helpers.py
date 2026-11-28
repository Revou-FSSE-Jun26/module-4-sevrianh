"""Card query, locking, rebalance, and serialization helpers (BE-14, R6, R7, R10, R18).

No flask imports.
"""
import uuid
from typing import Any
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.exceptions import (
    BoardNotFoundException,
    CardNotFoundException,
    ColumnNotFoundException,
    InvalidAssigneeError,
    TeamAccessDeniedError,
)
from app.extensions import db
from app.models import (
    ActivityEventEntity,
    BoardColumnEntity,
    BoardEntity,
    CardEntity,
    TeamMembershipEntity,
)
from app.utils.ordering import ORDER_STEP, rebalanced_orders, temporary_orders
from app.utils.time import utc_now


def to_uuid(value: Any) -> UUID:
    return value if isinstance(value, UUID) else uuid.UUID(str(value))


def load_card(card_id: Any, *, lock: bool = False) -> CardEntity:
    """Load an active Card; 404 if missing or soft-deleted (R6.14)."""
    uid = to_uuid(card_id)
    if lock:
        card = (
            db.session.query(CardEntity)
            .filter(CardEntity.id == uid)
            .with_for_update()
            .first()
        )
    else:
        card = db.session.get(CardEntity, uid)
    if card is None or card.deleted_at is not None:
        raise CardNotFoundException()
    return card


def load_column(column_id: Any) -> BoardColumnEntity:
    """Load an active Column; 404 if missing."""
    col = db.session.get(BoardColumnEntity, to_uuid(column_id))
    if col is None or col.deleted_at is not None:
        raise ColumnNotFoundException()
    return col


def validate_assignee(assignee_id: Any, team_id: UUID) -> None:
    """Raise InvalidAssigneeError (400) if assignee_id is not a Team member (R6.15)."""
    if assignee_id is None:
        return
    membership = (
        db.session.query(TeamMembershipEntity)
        .filter(TeamMembershipEntity.team_id == team_id)
        .filter(TeamMembershipEntity.user_id == to_uuid(assignee_id))
        .filter(TeamMembershipEntity.deleted_at.is_(None))
        .first()
    )
    if membership is None:
        raise InvalidAssigneeError()


def record_card_activity(
    board_id: UUID, actor_id: UUID, event_type: str, entity_id: UUID
) -> None:
    """Append an ActivityEvent row in the current transaction (R6.13, BE-15)."""
    db.session.add(
        ActivityEventEntity(
            board_id=board_id,
            actor_id=actor_id,
            event_type=event_type,
            entity_type='card',
            entity_id=entity_id,
        )
    )


def lock_columns_and_cards(column_ids: list[UUID]) -> dict[UUID, list[CardEntity]]:
    """Lock parent Columns in id order, then their active Cards in (order, id) order."""
    ordered_col_ids = sorted(set(column_ids))
    db.session.query(BoardColumnEntity).filter(
        BoardColumnEntity.id.in_(ordered_col_ids)
    ).order_by(BoardColumnEntity.id.asc()).with_for_update().all()

    cards_by_col: dict[UUID, list[CardEntity]] = {cid: [] for cid in ordered_col_ids}
    for cid in ordered_col_ids:
        cards_by_col[cid] = (
            db.session.query(CardEntity)
            .filter(CardEntity.column_id == cid)
            .filter(CardEntity.deleted_at.is_(None))
            .order_by(CardEntity.order.asc(), CardEntity.id.asc())
            .with_for_update()
            .all()
        )
    return cards_by_col


def rebalance_cards(ordered: list[CardEntity]) -> None:
    """Two-phase rebalance so no statement hits the partial unique index (BE-14)."""
    orders = [c.order for c in ordered]
    phase1_vals = temporary_orders([*orders, ORDER_STEP * len(ordered)], len(ordered))
    for card, temp_val in zip(ordered, phase1_vals):
        card.order = temp_val
    db.session.flush()
    for card, final_val in zip(ordered, rebalanced_orders(len(ordered))):
        card.order = final_val
    db.session.flush()


def sync_completed_at(card: CardEntity, target_col: BoardColumnEntity) -> None:
    """Update `completed_at` when moving into or out of an `is_done` Column (R24.2-24.5)."""
    if target_col.is_done and card.completed_at is None:
        card.completed_at = utc_now()
    elif not target_col.is_done and card.completed_at is not None:
        card.completed_at = None


def check_board_filter(user_id: UUID, board_id: Any) -> UUID:
    """Verify board existence (404) then membership (403) for `GET /api/cards` (R10.3)."""
    bid = to_uuid(board_id)
    board = db.session.get(BoardEntity, bid)
    if board is None or board.deleted_at is not None:
        raise BoardNotFoundException()
    member = (
        db.session.query(TeamMembershipEntity)
        .filter(TeamMembershipEntity.team_id == board.team_id)
        .filter(TeamMembershipEntity.user_id == user_id)
        .filter(TeamMembershipEntity.deleted_at.is_(None))
        .first()
    )
    if member is None:
        raise TeamAccessDeniedError()
    return bid


def query_card_list(
    user_id: UUID,
    *,
    q: str | None = None,
    assignee: str | None = None,
    board_id: UUID | None = None,
) -> list[dict[str, Any]]:
    """Query accessible non-deleted Cards matching optional `q`, `assignee=me`, `board_id`."""
    stmt = (
        db.session.query(
            CardEntity,
            BoardColumnEntity.name.label('column_name'),
            BoardEntity.id.label('board_id'),
            BoardEntity.name.label('board_name'),
        )
        .options(joinedload(CardEntity.assignee))
        .join(BoardColumnEntity, BoardColumnEntity.id == CardEntity.column_id)
        .join(BoardEntity, BoardEntity.id == BoardColumnEntity.board_id)
        .join(TeamMembershipEntity, TeamMembershipEntity.team_id == BoardEntity.team_id)
        .filter(TeamMembershipEntity.user_id == user_id)
        .filter(TeamMembershipEntity.deleted_at.is_(None))
        .filter(CardEntity.deleted_at.is_(None))
        .filter(BoardColumnEntity.deleted_at.is_(None))
        .filter(BoardEntity.deleted_at.is_(None))
    )
    if assignee == 'me':
        stmt = stmt.filter(CardEntity.assignee_id == user_id)
    if q is not None:
        stmt = stmt.filter(func.lower(CardEntity.title).contains(q.lower(), autoescape=True))
    if board_id is not None:
        stmt = stmt.filter(BoardEntity.id == board_id)

    rows = stmt.order_by(BoardEntity.name.asc(), CardEntity.order.asc()).all()
    return [
        {
            'id': card.id,
            'title': card.title,
            'order': card.order,
            'column_id': card.column_id,
            'column_name': col_name,
            'board_id': bid,
            'board_name': bname,
            'assignee_id': card.assignee_id,
            'assignee': card.assignee,
        }
        for card, col_name, bid, bname in rows
    ]
