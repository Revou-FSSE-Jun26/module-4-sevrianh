"""Guard decorators and the Access Resolution Table (BE-08, BE-13, requirements R3)."""
import hashlib
import uuid
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Optional

from flask import request
from flask_jwt_extended import create_access_token, get_jwt_identity, verify_jwt_in_request
from marshmallow import ValidationError

from app.exceptions import (
    ACCESS_OR_NOT_FOUND_MESSAGE,
    AuthenticationRequiredError,
    BoardNotFoundException,
    CardNotFoundException,
    InviteLinkNotFoundException,
    TeamAccessDeniedError,
)
from app.extensions import db
from app.models import (
    BoardColumnEntity,
    BoardEntity,
    CardEntity,
    InviteLinkEntity,
    TeamMembershipEntity,
    UserEntity,
)

INVITE_TOKEN_HEADER = 'X-Invite-Token'
GUEST_ROLE = 'guest'


@dataclass(frozen=True)
class Access:
    """Result of the Access Resolution Table: `user` is None for a Guest."""

    user: Optional[UserEntity]
    role: str  # 'admin', 'member' or 'guest'


def hash_invite_token(raw_token: str) -> str:
    """Return the SHA-256 hex digest stored in `invite_links.token_hash`."""
    return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()


def issue_access_token(user_id: str) -> str:
    """Create a JWT whose identity is the user UUID string (BE-13)."""
    return create_access_token(identity=user_id)


def _validate_path_uuids(kwargs: dict[str, Any]) -> None:
    """Path identifiers ending in `_id` or named `id` must be UUIDs (BE-04)."""
    for name, value in kwargs.items():
        if name != 'id' and not name.endswith('_id'):
            continue
        try:
            uuid.UUID(str(value))
        except ValueError:
            raise ValidationError({name: ['Not a valid UUID.']})


def _load_jwt_user() -> UserEntity:
    """Verify the JWT of the current request and load its user, or raise 401."""
    try:
        verify_jwt_in_request()
        user_id = uuid.UUID(str(get_jwt_identity()))
    except Exception as exc:  # any JWT failure is a 401, never a 422 or 500
        raise AuthenticationRequiredError() from exc
    user = db.session.get(UserEntity, user_id)
    if user is None or user.deleted_at is not None:
        raise AuthenticationRequiredError()
    return user


def token_required(view: Callable) -> Callable:
    """Require a valid JWT; pass `current_user` as the first argument."""

    @wraps(view)
    def wrapper(*args: Any, **kwargs: Any):
        current_user = _load_jwt_user()
        _validate_path_uuids(kwargs)
        return view(current_user, *args, **kwargs)

    return wrapper


def _resolve_board(kwargs: dict[str, Any]) -> BoardEntity:
    """Board of the resource: the requested Board or the Card's Board (step 3)."""
    if 'card_id' in kwargs:
        row = (
            db.session.query(BoardEntity)
            .join(BoardColumnEntity, BoardColumnEntity.board_id == BoardEntity.id)
            .join(CardEntity, CardEntity.column_id == BoardColumnEntity.id)
            .filter(CardEntity.id == uuid.UUID(kwargs['card_id']))
            .filter(CardEntity.deleted_at.is_(None))
            .filter(BoardEntity.deleted_at.is_(None))
            .first()
        )
        if row is None:
            raise CardNotFoundException()
        return row
    board = db.session.get(BoardEntity, uuid.UUID(kwargs['board_id']))
    if board is None or board.deleted_at is not None:
        raise BoardNotFoundException()
    return board


def _membership_role(board: BoardEntity, user: UserEntity) -> Optional[str]:
    membership = (
        db.session.query(TeamMembershipEntity)
        .filter(TeamMembershipEntity.team_id == board.team_id)
        .filter(TeamMembershipEntity.user_id == user.id)
        .filter(TeamMembershipEntity.deleted_at.is_(None))
        .first()
    )
    return membership.role if membership else None


def _invite_token_board_id(raw_token: str) -> Optional[uuid.UUID]:
    """Board id of a valid, non-revoked invite token, else None (lookup by hash)."""
    link = (
        db.session.query(InviteLinkEntity)
        .filter(InviteLinkEntity.token_hash == hash_invite_token(raw_token))
        .filter(InviteLinkEntity.revoked_at.is_(None))
        .filter(InviteLinkEntity.deleted_at.is_(None))
        .first()
    )
    return link.board_id if link else None


def _resolve_guest(board: BoardEntity, raw_token: Optional[str]) -> Access:
    """Steps 5 to 8, reached only when the requester is not a Team member."""
    if raw_token is None:
        raise TeamAccessDeniedError()  # step 5 (no JWT and no token is step 2)
    token_board_id = _invite_token_board_id(raw_token)
    if token_board_id is None:
        raise InviteLinkNotFoundException()  # step 6
    if token_board_id != board.id:
        raise TeamAccessDeniedError(ACCESS_OR_NOT_FOUND_MESSAGE)  # step 8
    return Access(user=None, role=GUEST_ROLE)  # step 7


def resolve_board_access(kwargs: dict[str, Any]) -> Access:
    """Apply the ordered Access Resolution Table of BE-08."""
    has_jwt_header = request.headers.get('Authorization') is not None
    raw_token = request.headers.get(INVITE_TOKEN_HEADER)
    user = _load_jwt_user() if has_jwt_header else None  # step 1
    if user is None and raw_token is None:
        raise AuthenticationRequiredError()  # step 2
    _validate_path_uuids(kwargs)
    board = _resolve_board(kwargs)  # step 3
    if user is not None:
        role = _membership_role(board, user)
        if role is not None:
            return Access(user=user, role=role)  # step 4
    return _resolve_guest(board, raw_token)


def board_access_required(allow_guest_read: bool = False) -> Callable:
    """Resolve Board access; pass the `access` object as the first argument."""

    def decorator(view: Callable) -> Callable:
        @wraps(view)
        def wrapper(*args: Any, **kwargs: Any):
            access = resolve_board_access(kwargs)
            if access.role == GUEST_ROLE and not allow_guest_read:
                raise TeamAccessDeniedError()
            return view(access, *args, **kwargs)

        return wrapper

    return decorator


__all__ = [
    'Access',
    'board_access_required',
    'hash_invite_token',
    'issue_access_token',
    'resolve_board_access',
    'token_required',
]
