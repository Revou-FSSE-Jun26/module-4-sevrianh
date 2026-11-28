"""Comments business logic. No flask imports (BE-03)."""
from typing import Any

from marshmallow import ValidationError

from app.blueprints.boards.service import require_team_member_service
from app.blueprints.notifications.service import (
    create_mention_notifications_service,
    delete_comment_notifications_service,
)
from app.exceptions import CommentNotFoundException, CommentOwnershipError
from app.extensions import db
from app.models import BoardColumnEntity, BoardEntity, CardCommentEntity, UserEntity
from app.utils.card_helpers import load_card, record_card_activity, to_uuid
from app.utils.time import utc_now


def _board_for_card(card) -> BoardEntity:
    column = db.session.get(BoardColumnEntity, card.column_id)
    return db.session.get(BoardEntity, column.board_id)


def _load_active_comment(comment_id: Any) -> CardCommentEntity:
    comment = db.session.get(CardCommentEntity, to_uuid(comment_id))
    if comment is None or comment.deleted_at is not None:
        raise CommentNotFoundException()
    return comment


def create_comment_service(card_id: Any, data: dict[str, Any], user_id: Any) -> CardCommentEntity:
    user_uuid = to_uuid(user_id)
    card = load_card(card_id)
    board = _board_for_card(card)
    require_team_member_service(board.id, user_uuid)

    parent_id = data.get('parent_id')
    if parent_id is not None:
        parent = db.session.get(CardCommentEntity, to_uuid(parent_id))
        if parent is None or parent.card_id != card.id:
            raise ValidationError('Parent comment must belong to the same card.')

    comment = CardCommentEntity(
        card_id=card.id,
        author_id=user_uuid,
        parent_comment_id=to_uuid(parent_id) if parent_id is not None else None,
        content=data['content'],
    )
    db.session.add(comment)
    db.session.flush()
    author = db.session.get(UserEntity, user_uuid)
    create_mention_notifications_service(
        comment.id,
        comment.content,
        user_uuid,
        author.name if author is not None else '',
        card.title,
        board.team_id,
    )
    record_card_activity(board.id, user_uuid, 'comment_added', card.id)
    db.session.commit()
    return comment


def list_comments_service(card_id: Any) -> list[CardCommentEntity]:
    card = load_card(card_id)
    rows = (
        db.session.query(CardCommentEntity)
        .filter(CardCommentEntity.card_id == card.id)
        .order_by(CardCommentEntity.created_at.asc(), CardCommentEntity.id.asc())
        .all()
    )
    parents_with_live_reply = {
        row.parent_comment_id
        for row in rows
        if row.deleted_at is None and row.parent_comment_id is not None
    }
    return [
        row for row in rows
        if row.deleted_at is None or row.id in parents_with_live_reply
    ]


def update_comment_service(
    comment_id: Any, data: dict[str, Any], user_id: Any
) -> CardCommentEntity:
    user_uuid = to_uuid(user_id)
    comment = _load_active_comment(comment_id)
    card = load_card(comment.card_id)
    board = _board_for_card(card)
    require_team_member_service(board.id, user_uuid)
    if comment.author_id != user_uuid:
        raise CommentOwnershipError()

    comment.content = data['content']
    author = db.session.get(UserEntity, user_uuid)
    create_mention_notifications_service(
        comment.id,
        comment.content,
        user_uuid,
        author.name if author is not None else '',
        card.title,
        board.team_id,
    )
    db.session.commit()
    return comment


def delete_comment_service(comment_id: Any, user_id: Any) -> dict[str, Any]:
    user_uuid = to_uuid(user_id)
    comment = _load_active_comment(comment_id)
    board = _board_for_card(load_card(comment.card_id))
    require_team_member_service(board.id, user_uuid)
    if comment.author_id != user_uuid:
        raise CommentOwnershipError()

    comment.deleted_at = utc_now()
    delete_comment_notifications_service(comment.id)
    db.session.commit()
    return {'id': comment.id}
