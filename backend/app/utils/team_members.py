"""Team membership helpers used by the boards service (R12). No flask imports."""
from typing import Any
from uuid import UUID

from sqlalchemy import func

from app.extensions import db
from app.models import (
    BoardColumnEntity,
    BoardEntity,
    CardEntity,
    TeamMembershipEntity,
    UserEntity,
)
from app.utils.time import utc_now

ADMIN = 'admin'


def find_membership(team_id: UUID, user_id: UUID, lock: bool = False):
    """Active membership of `user_id` in the Team, optionally row-locked."""
    query = (
        db.session.query(TeamMembershipEntity)
        .filter(TeamMembershipEntity.team_id == team_id)
        .filter(TeamMembershipEntity.user_id == user_id)
        .filter(TeamMembershipEntity.deleted_at.is_(None))
    )
    return (query.with_for_update() if lock else query).first()


def find_user_by_email(email: str):
    """Case-insensitive lookup of a registered user (matches `uq_users_email_lower`)."""
    return (
        db.session.query(UserEntity)
        .filter(func.lower(UserEntity.email) == email.strip().lower())
        .filter(UserEntity.deleted_at.is_(None))
        .first()
    )


def member_dict(membership: TeamMembershipEntity, user: UserEntity) -> dict[str, Any]:
    return {
        'user_id': user.id,
        'name': user.name,
        'username': user.username,
        'role': membership.role,
    }


def list_member_rows(team_id: UUID) -> list[dict[str, Any]]:
    rows = (
        db.session.query(TeamMembershipEntity, UserEntity)
        .join(UserEntity, UserEntity.id == TeamMembershipEntity.user_id)
        .filter(TeamMembershipEntity.team_id == team_id)
        .filter(TeamMembershipEntity.deleted_at.is_(None))
        .order_by(UserEntity.name, UserEntity.id)
        .all()
    )
    return [member_dict(membership, user) for membership, user in rows]


def lock_admins(team_id: UUID) -> list[TeamMembershipEntity]:
    """Row-lock the Team's Admin memberships so concurrent demotions serialize (R12.10)."""
    return (
        db.session.query(TeamMembershipEntity)
        .filter(TeamMembershipEntity.team_id == team_id)
        .filter(TeamMembershipEntity.role == ADMIN)
        .filter(TeamMembershipEntity.deleted_at.is_(None))
        .order_by(TeamMembershipEntity.id)
        .with_for_update()
        .all()
    )


def clear_assignee(team_id: UUID, user_id: UUID) -> None:
    """Null `assignee_id` on the user's non-deleted Cards of the Team's Boards (R12.6)."""
    column_ids = (
        db.session.query(BoardColumnEntity.id)
        .join(BoardEntity, BoardEntity.id == BoardColumnEntity.board_id)
        .filter(BoardEntity.team_id == team_id)
        .subquery()
    )
    (
        db.session.query(CardEntity)
        .filter(CardEntity.assignee_id == user_id)
        .filter(CardEntity.deleted_at.is_(None))
        .filter(CardEntity.column_id.in_(db.session.query(column_ids.c.id)))
        .update(
            {CardEntity.assignee_id: None, CardEntity.updated_at: utc_now()},
            synchronize_session=False,
        )
    )
