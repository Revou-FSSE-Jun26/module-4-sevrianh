"""Mention notifications, listing, mark-read, and cleanup (R9, BE-15). No flask imports."""
import math
import re
import uuid
from typing import Any
from uuid import UUID

from app.exceptions import NotificationNotFoundException
from app.extensions import db
from app.models import (
    BoardColumnEntity,
    BoardEntity,
    CardCommentEntity,
    CardEntity,
    NotificationEntity,
    TeamMembershipEntity,
    UserEntity,
)

MENTION_TYPE = 'mention'
MESSAGE_LIMIT = 255
MENTION_RE = re.compile(r'@([A-Za-z0-9_]{3,30})(?![A-Za-z0-9_])')


def _as_uuid(value: Any) -> UUID:
    return value if isinstance(value, UUID) else uuid.UUID(str(value))


def _commit() -> None:
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def _mentioned_usernames(content: str) -> list[str]:
    """Unique lowercased mentions, in order. A token longer than 30 characters is ignored."""
    seen: list[str] = []
    for match in MENTION_RE.findall(content or ''):
        name = match.lower()
        if name not in seen:
            seen.append(name)
    return seen


def _mention_message(mentioner_name: str, card_title: str) -> str:
    text = f'{mentioner_name} mentioned you on "{card_title}"'
    return text[:MESSAGE_LIMIT]


def _members_by_username(team_id: UUID) -> dict[str, UserEntity]:
    rows = (
        db.session.query(UserEntity)
        .join(TeamMembershipEntity, TeamMembershipEntity.user_id == UserEntity.id)
        .filter(TeamMembershipEntity.team_id == team_id)
        .filter(TeamMembershipEntity.deleted_at.is_(None))
        .filter(UserEntity.deleted_at.is_(None))
        .all()
    )
    return {user.username: user for user in rows}


def _notified_recipient_ids(comment_id: UUID) -> set[UUID]:
    rows = (
        db.session.query(NotificationEntity.recipient_id)
        .filter(NotificationEntity.comment_id == comment_id)
        .filter(NotificationEntity.type == MENTION_TYPE)
        .all()
    )
    return {row[0] for row in rows}


def _add_mention(comment_id: UUID, recipient_id: UUID, message: str) -> NotificationEntity:
    note = NotificationEntity(
        recipient_id=recipient_id,
        comment_id=comment_id,
        type=MENTION_TYPE,
        message=message,
        is_read=False,
    )
    db.session.add(note)
    return note


def _build_mentions(
    comment_id: UUID,
    content: str,
    author_id: UUID,
    members: dict[str, UserEntity],
    already: set[UUID],
    message: str,
) -> list[NotificationEntity]:
    created: list[NotificationEntity] = []
    for username in _mentioned_usernames(content):
        user = members.get(username)
        if user is None or user.id == author_id or user.id in already:
            continue
        created.append(_add_mention(comment_id, user.id, message))
    return created


def create_mention_notifications_service(
    comment_id: Any,
    content: str,
    author_id: Any,
    mentioner_name: str,
    card_title: str,
    team_id: Any,
) -> list[NotificationEntity]:
    """One unread mention per newly mentioned member. The caller commits (R9.1-R9.6, D-08).

    Repeated, self, and unmatched names are skipped. An edit notifies only members who
    do not already have a mention Notification for this Comment (R9.5, A-05).
    """
    comment_uuid = _as_uuid(comment_id)
    created = _build_mentions(
        comment_uuid,
        content,
        _as_uuid(author_id),
        _members_by_username(_as_uuid(team_id)),
        _notified_recipient_ids(comment_uuid),
        _mention_message(mentioner_name, card_title),
    )
    if created:
        db.session.flush()
    return created


def delete_comment_notifications_service(comment_id: Any) -> None:
    """Delete every Notification of a Comment. The caller commits (R9.13, BE-15)."""
    (
        db.session.query(NotificationEntity)
        .filter(NotificationEntity.comment_id == _as_uuid(comment_id))
        .delete(synchronize_session=False)
    )


def delete_team_member_notifications_service(user_id: Any, team_id: Any) -> None:
    """Delete the user's Notifications for Comments on the Team's Boards (R9.13, R12.5)."""
    comment_ids = (
        db.session.query(CardCommentEntity.id)
        .join(CardEntity, CardEntity.id == CardCommentEntity.card_id)
        .join(BoardColumnEntity, BoardColumnEntity.id == CardEntity.column_id)
        .join(BoardEntity, BoardEntity.id == BoardColumnEntity.board_id)
        .filter(BoardEntity.team_id == _as_uuid(team_id))
    )
    (
        db.session.query(NotificationEntity)
        .filter(NotificationEntity.recipient_id == _as_uuid(user_id))
        .filter(NotificationEntity.comment_id.in_(comment_ids))
        .delete(synchronize_session=False)
    )


def _joined_notifications():
    return (
        db.session.query(NotificationEntity, CardEntity.id, BoardColumnEntity.board_id)
        .join(CardCommentEntity, CardCommentEntity.id == NotificationEntity.comment_id)
        .join(CardEntity, CardEntity.id == CardCommentEntity.card_id)
        .join(BoardColumnEntity, BoardColumnEntity.id == CardEntity.column_id)
    )


def _visible_for(user_id: UUID):
    """The user's Notifications whose Card is not soft-deleted (U-04, R6.16)."""
    return (
        _joined_notifications()
        .filter(NotificationEntity.recipient_id == user_id)
        .filter(NotificationEntity.deleted_at.is_(None))
        .filter(CardEntity.deleted_at.is_(None))
    )


def _notification_dict(note: NotificationEntity, card_id: Any, board_id: Any) -> dict[str, Any]:
    return {
        'id': note.id,
        'type': note.type,
        'message': note.message,
        'is_read': note.is_read,
        'created_at': note.created_at,
        'comment_id': note.comment_id,
        'card_id': card_id,
        'board_id': board_id,
    }


def _total_pages(total: int, per_page: int) -> int:
    if total == 0:
        return 0
    return math.ceil(total / per_page)


def list_notifications_service(user_id: Any, query: dict[str, Any]) -> dict[str, Any]:
    """Page the user's visible Notifications, newest first (R9.7, R9.9)."""
    user_uuid = _as_uuid(user_id)
    page = query['page']
    per_page = query['per_page']
    visible = _visible_for(user_uuid)
    total = visible.count()
    unread_count = visible.filter(NotificationEntity.is_read.is_(False)).count()
    rows = (
        visible.order_by(NotificationEntity.created_at.desc(), NotificationEntity.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return {
        'items': [_notification_dict(note, card_id, board_id) for note, card_id, board_id in rows],
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': _total_pages(total, per_page),
        'unread_count': unread_count,
    }


def mark_notification_read_service(notification_id: Any, user_id: Any) -> dict[str, Any]:
    """Set `is_read` for the owner's Notification. Already-read is a no-op (R9.10-R9.12)."""
    row = (
        _joined_notifications()
        .filter(NotificationEntity.id == _as_uuid(notification_id))
        .filter(NotificationEntity.recipient_id == _as_uuid(user_id))
        .first()
    )
    if row is None:
        raise NotificationNotFoundException()
    note, card_id, board_id = row
    if not note.is_read:
        note.is_read = True
        _commit()
    return _notification_dict(note, card_id, board_id)
