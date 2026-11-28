"""Cards business rules, FLOAT reordering, search, and My Tasks (BE-09, BE-14).

No flask imports.
"""
from typing import Any

from sqlalchemy import func

from app.blueprints.boards.service import require_team_member_service
from app.exceptions import (
    AdminAccessRequiredError,
    InvalidTargetColumnError,
    OrderConflictError,
)
from app.extensions import db
from app.models import BoardColumnEntity, CardEntity, TeamMembershipEntity
from app.utils.card_helpers import (
    check_board_filter,
    load_card,
    load_column,
    lock_columns_and_cards,
    query_card_list,
    rebalance_cards,
    record_card_activity,
    sync_completed_at,
    to_uuid,
    validate_assignee,
)
from app.utils.ordering import append_order, has_small_gap
from app.utils.time import utc_now


def create_card_service(column_id: Any, data: dict[str, Any], user_id: Any) -> CardEntity:
    """Append a Card to a Column for a Member or Admin (R6.1-R6.3, R6.13)."""
    column = load_column(column_id)
    board = require_team_member_service(column.board_id, user_id)
    uid = to_uuid(user_id)
    assignee_id = data.get('assignee_id')
    validate_assignee(assignee_id, board.team_id)

    try:
        db.session.query(BoardColumnEntity).filter(
            BoardColumnEntity.id == column.id
        ).with_for_update().one()
        last_order = (
            db.session.query(func.max(CardEntity.order))
            .filter(CardEntity.column_id == column.id)
            .filter(CardEntity.deleted_at.is_(None))
            .scalar()
        )
        card = CardEntity(
            column_id=column.id,
            created_by_id=uid,
            title=data['title'],
            description=data.get('description'),
            order=append_order(last_order),
            assignee_id=to_uuid(assignee_id) if assignee_id else None,
            completed_at=utc_now() if column.is_done else None,
        )
        db.session.add(card)
        db.session.flush()
        record_card_activity(board.id, uid, 'card_created', card.id)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return card


def update_card_service(card_id: Any, data: dict[str, Any], user_id: Any) -> CardEntity:
    """Edit title, description, or assignee_id under row lock (R6.4-R6.5, R15.3)."""
    card_peek = load_card(card_id)
    board = require_team_member_service(card_peek.column.board_id, user_id)
    uid = to_uuid(user_id)
    if 'assignee_id' in data:
        validate_assignee(data['assignee_id'], board.team_id)

    try:
        card = load_card(card_id, lock=True)
        if 'title' in data:
            card.title = data['title']
        if 'description' in data:
            card.description = data['description']
        if 'assignee_id' in data:
            card.assignee_id = to_uuid(data['assignee_id']) if data['assignee_id'] else None
        card.updated_at = utc_now()
        record_card_activity(board.id, uid, 'card_updated', card.id)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return card


def delete_card_service(card_id: Any, user_id: Any) -> dict[str, str]:
    """Soft-delete a Card: Admin any, Member own only (R6.6-R6.7, R6.13, OD-08)."""
    card = load_card(card_id)
    board = require_team_member_service(card.column.board_id, user_id)
    uid = to_uuid(user_id)

    membership = (
        db.session.query(TeamMembershipEntity)
        .filter(TeamMembershipEntity.team_id == board.team_id)
        .filter(TeamMembershipEntity.user_id == uid)
        .filter(TeamMembershipEntity.deleted_at.is_(None))
        .one()
    )
    if membership.role != 'admin' and card.created_by_id != uid:
        raise AdminAccessRequiredError()

    deleted_id = str(card.id)
    try:
        now = utc_now()
        card.deleted_at = now
        card.updated_at = now
        record_card_activity(board.id, uid, 'card_deleted', card.id)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return {'id': deleted_id}


def move_card_service(card_id: Any, data: dict[str, Any], user_id: Any) -> dict[str, Any]:
    """Move a Card to column_id/order; 409 on conflict; rebalance if gap < MIN_GAP (R7)."""
    card_peek = load_card(card_id)
    board = require_team_member_service(card_peek.column.board_id, user_id)
    uid = to_uuid(user_id)
    target_col_id = to_uuid(data['column_id'])
    new_order = float(data['order'])

    target_col = db.session.get(BoardColumnEntity, target_col_id)
    if target_col is None or target_col.deleted_at is not None or target_col.board_id != board.id:
        raise InvalidTargetColumnError()

    try:
        cards_by_col = lock_columns_and_cards([card_peek.column_id, target_col_id])
        card = load_card(card_id)
        target_siblings = cards_by_col[target_col_id]
        if any(c.order == new_order for c in target_siblings if c.id != card.id):
            raise OrderConflictError()

        card.column_id = target_col_id
        card.order = new_order
        sync_completed_at(card, target_col)
        card.updated_at = utc_now()
        db.session.flush()

        ordered = sorted(
            [c for c in target_siblings if c.id != card.id] + [card],
            key=lambda c: (c.order, c.id),
        )
        rebalanced = has_small_gap([c.order for c in ordered])
        if rebalanced:
            rebalance_cards(ordered)

        record_card_activity(board.id, uid, 'card_moved', card.id)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return {'card': card, 'rebalanced': rebalanced}


def list_cards_service(user_id: Any, query: dict[str, Any]) -> list[dict[str, Any]]:
    """Search Cards by title and/or `assignee=me` across accessible Boards (R10, R18)."""
    uid = to_uuid(user_id)
    board_id = check_board_filter(uid, query['board_id']) if 'board_id' in query else None
    return query_card_list(
        uid,
        q=query.get('q'),
        assignee=query.get('assignee'),
        board_id=board_id,
    )
