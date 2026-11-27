import uuid

from app.extensions import db
from app.utils.time import utc_now


class InviteLinkEntity(db.Model):
    __tablename__ = 'invite_links'
    __table_args__ = (
        db.UniqueConstraint('token_hash', name='uq_invite_links_token_hash'),
    )

    id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False,
        default=utc_now, onupdate=utc_now,
    )
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)

    board_id = db.Column(
        db.UUID,
        db.ForeignKey('boards.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    created_by_id = db.Column(
        db.UUID,
        db.ForeignKey('users.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
    )
    # Only the hash is stored, never the raw token. Revoking sets revoked_at.
    token_hash = db.Column(db.String(255), nullable=False)
    revoked_at = db.Column(db.DateTime(timezone=True), nullable=True)
