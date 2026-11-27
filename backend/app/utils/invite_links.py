"""Invite Link helpers for the boards service (R3.1, R3.2, R3.6, R3.7). No flask imports."""
import secrets
import uuid
from typing import Any, Optional
from uuid import UUID

from app.exceptions import InviteLinkNotFoundException
from app.extensions import db
from app.models import InviteLinkEntity
from app.utils.auth import hash_invite_token
from app.utils.time import utc_now

TOKEN_BYTES = 32  # 256 bits of entropy (R3.2)


def create_link(board_id: UUID, user_id: UUID) -> dict[str, Any]:
    """Store a new link by token hash and return the raw token once."""
    token = secrets.token_urlsafe(TOKEN_BYTES)
    link = InviteLinkEntity(
        board_id=board_id, created_by_id=user_id, token_hash=hash_invite_token(token)
    )
    try:
        db.session.add(link)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return {
        'id': link.id,
        'board_id': link.board_id,
        'token': token,
        'created_at': link.created_at,
    }


def find_link(board_id: UUID, invite_id: Any) -> InviteLinkEntity:
    """Link bound to the Board; unknown, foreign or malformed ids give 404 `Not found`."""
    try:
        link_id: Optional[UUID] = uuid.UUID(str(invite_id))
    except ValueError:
        link_id = None
    link = db.session.get(InviteLinkEntity, link_id) if link_id else None
    if link is None or link.deleted_at is not None or link.board_id != board_id:
        raise InviteLinkNotFoundException()
    return link


def revoke_link(link: InviteLinkEntity) -> dict[str, str]:
    """Set `revoked_at` once; the row is kept (R3.6, R3.7)."""
    link_id = str(link.id)
    if link.revoked_at is None:
        link.revoked_at = utc_now()
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return {'id': link_id}
