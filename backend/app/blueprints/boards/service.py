"""Boards business rules and Team authorization helpers (BE-09, R1, R2, R4). No flask imports."""
import uuid
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.attributes import set_committed_value

from app.exceptions import (
    AdminAccessRequiredError,
    BoardNotFoundException,
    LastAdminError,
    MemberAlreadyExistsError,
    MemberNotFoundException,
    TeamAccessDeniedError,
    UserNotFoundException,
)
from app.extensions import db
from app.models import (
    BoardColumnEntity,
    BoardEntity,
    CardEntity,
    TeamEntity,
    TeamMembershipEntity,
    UserEntity,
)
from app.utils import invite_links as il, team_members as tm
from app.utils.auth import Access

ADMIN = 'admin'


def _to_uuid(value: Any) -> UUID:
    return value if isinstance(value, UUID) else uuid.UUID(str(value))


def _membership(team_id: UUID, user_id: UUID) -> Optional[TeamMembershipEntity]:
    return tm.find_membership(team_id, _to_uuid(user_id))


def _load_board(board_id: Any) -> BoardEntity:
    board = db.session.get(BoardEntity, _to_uuid(board_id))
    if board is None or board.deleted_at is not None:
        raise BoardNotFoundException()
    return board


def require_team_member_service(board_id: Any, user_id: Any) -> BoardEntity:
    """Board of a Team the user belongs to: 404 missing Board, 403 non-member (BE-09)."""
    board = _load_board(board_id)
    if _membership(board.team_id, user_id) is None:
        raise TeamAccessDeniedError()
    return board


def require_team_admin_service(board_id: Any, user_id: Any) -> BoardEntity:
    """Board of a Team the user administers: 404, then 403 non-member, then 403 Member."""
    board = _load_board(board_id)
    membership = _membership(board.team_id, user_id)
    if membership is None:
        raise TeamAccessDeniedError()
    if membership.role != ADMIN:
        raise AdminAccessRequiredError()
    return board


def _target_team_id(user_id: UUID, team_id: Optional[UUID]) -> UUID:
    """Team that will own a new Board; any non-administered Team is a generic 403 (D-01)."""
    if team_id is None:
        team = (
            db.session.query(TeamEntity)
            .filter(TeamEntity.owner_id == user_id)
            .filter(TeamEntity.is_personal.is_(True))
            .filter(TeamEntity.deleted_at.is_(None))
            .first()
        )
        team_id = team.id if team else None
    membership = _membership(team_id, user_id) if team_id is not None else None
    if membership is None or membership.role != ADMIN:
        raise TeamAccessDeniedError()
    return team_id


def create_board_service(user_id: Any, data: dict[str, Any]) -> BoardEntity:
    """Create a Board in the requested or personal Team (R4.1, R4.2, R4.4)."""
    user_id = _to_uuid(user_id)
    team_id = _target_team_id(user_id, data.get('team_id'))
    board = BoardEntity(team_id=team_id, name=data['name'])
    try:
        db.session.add(board)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return board


def list_boards_service(user_id: Any) -> list[BoardEntity]:
    """Boards of the requester's Teams, newest first (R4.5)."""
    return (
        db.session.query(BoardEntity)
        .join(TeamMembershipEntity, TeamMembershipEntity.team_id == BoardEntity.team_id)
        .filter(TeamMembershipEntity.user_id == _to_uuid(user_id))
        .filter(TeamMembershipEntity.deleted_at.is_(None))
        .filter(BoardEntity.deleted_at.is_(None))
        .order_by(BoardEntity.created_at.desc())
        .all()
    )


def get_board_service(board_id: Any, access: Access) -> BoardEntity:
    """Board with Columns and Cards in two queries (R4.6, R14.2).

    The guard already authorized `access` (Member, Admin or Guest), so the Board is read only.
    """
    board = _load_board(board_id)
    columns = (
        db.session.query(BoardColumnEntity)
        .filter(BoardColumnEntity.board_id == board.id)
        .order_by(BoardColumnEntity.order)
        .all()
    )
    cards = (
        db.session.query(CardEntity)
        .join(BoardColumnEntity, BoardColumnEntity.id == CardEntity.column_id)
        .options(joinedload(CardEntity.assignee))
        .filter(BoardColumnEntity.board_id == board.id)
        .filter(CardEntity.deleted_at.is_(None))
        .order_by(CardEntity.order)
        .all()
    )
    by_column: dict[UUID, list[CardEntity]] = {column.id: [] for column in columns}
    for card in cards:
        by_column[card.column_id].append(card)
    for column in columns:
        set_committed_value(column, 'cards', by_column[column.id])
    set_committed_value(board, 'columns', columns)
    return board


def update_board_service(board_id: Any, user_id: Any, data: dict[str, Any]) -> BoardEntity:
    """Rename a Board (Admin only, R4.7)."""
    board = require_team_admin_service(board_id, user_id)
    board.name = data['name']
    _commit()
    return board


def _commit() -> None:
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def add_team_member_service(board_id: Any, user_id: Any, data: dict[str, Any]) -> dict[str, Any]:
    """Add a registered user to the Board's Team; Admin check first (R12.1-R12.3, R12.9)."""
    board = require_team_admin_service(board_id, user_id)
    user = tm.find_user_by_email(data['email'])
    if user is None:
        raise UserNotFoundException()
    if tm.find_membership(board.team_id, user.id) is not None:
        raise MemberAlreadyExistsError()
    membership = TeamMembershipEntity(
        team_id=board.team_id, user_id=user.id, role=data.get('role', 'member')
    )
    db.session.add(membership)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise MemberAlreadyExistsError()
    except Exception:
        db.session.rollback()
        raise
    return tm.member_dict(membership, user)


def list_team_members_service(board_id: Any, user_id: Any) -> list[dict[str, Any]]:
    """Members of the Board's Team, for Admins and Members (R12.7)."""
    board = require_team_member_service(board_id, user_id)
    return tm.list_member_rows(board.team_id)


def _locked_target(board: BoardEntity, target_id: Any) -> TeamMembershipEntity:
    """Lock the Team's Admin rows, then return the target membership (404 if absent)."""
    tm.lock_admins(board.team_id)
    target = tm.find_membership(board.team_id, _to_uuid(target_id), lock=True)
    if target is None:
        raise MemberNotFoundException()
    return target


def _ensure_not_last_admin(team_id: UUID, target: TeamMembershipEntity) -> None:
    if target.role == ADMIN and len(tm.lock_admins(team_id)) <= 1:
        raise LastAdminError()


def update_team_member_role_service(
    board_id: Any, user_id: Any, target_id: Any, data: dict[str, Any]
) -> dict[str, Any]:
    """Change a member's role; the last Admin cannot be demoted (R12.4, R12.8)."""
    board = require_team_admin_service(board_id, user_id)
    target = _locked_target(board, target_id)
    if data['role'] != ADMIN:
        _ensure_not_last_admin(board.team_id, target)
    target.role = data['role']
    user = db.session.get(UserEntity, target.user_id)
    result = tm.member_dict(target, user)
    _commit()
    return result


def remove_team_member_service(board_id: Any, user_id: Any, target_id: Any) -> dict[str, str]:
    """Remove a member; authored Cards and Comments stay, assignments are cleared (R12.5-R12.8)."""
    board = require_team_admin_service(board_id, user_id)
    target = _locked_target(board, target_id)
    _ensure_not_last_admin(board.team_id, target)
    removed_id = str(target.user_id)
    try:
        tm.clear_assignee(board.team_id, target.user_id)
        db.session.delete(target)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return {'id': removed_id}


def create_invite_link_service(board_id: Any, user_id: Any) -> dict[str, Any]:
    """Create a read-only Invite Link for the Board (Admin only, R3.1)."""
    return il.create_link(require_team_admin_service(board_id, user_id).id, _to_uuid(user_id))


def revoke_invite_link_service(board_id: Any, user_id: Any, invite_id: Any) -> dict[str, str]:
    """Revoke an Invite Link; Board and link 404 come before the Admin check (R3.6)."""
    link = il.find_link(_load_board(board_id).id, invite_id)
    require_team_admin_service(board_id, user_id)
    return il.revoke_link(link)


def delete_board_service(board_id: Any, user_id: Any) -> dict[str, str]:
    """Delete a Board; the database cascade removes its contents (Admin only, R4.9)."""
    board = require_team_admin_service(board_id, user_id)
    deleted_id = str(board.id)
    db.session.delete(board)
    _commit()
    return {'id': deleted_id}
