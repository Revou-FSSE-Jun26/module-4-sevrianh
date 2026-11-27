import uuid

from sqlalchemy.sql.elements import conv

from app.extensions import db
from app.utils.time import utc_now


class NotificationEntity(db.Model):
    __tablename__ = 'notifications'
    __table_args__ = (
        # conv() keeps the exact name; the ck convention would prefix it again.
        db.CheckConstraint("type IN ('mention')", name=conv('ck_notifications_type')),
        db.UniqueConstraint(
            'recipient_id', 'comment_id', 'type',
            name='uq_notifications_recipient_id_comment_id_type',
        ),
        db.Index(
            'ix_notifications_recipient_id_created_at', 'recipient_id', 'created_at'
        ),
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

    # recipient_id needs no separate index: the composite index starts with it.
    # No user_id and no card_id column (DB-09): the Card is reached through comment.
    recipient_id = db.Column(
        db.UUID,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
    )
    comment_id = db.Column(
        db.UUID,
        db.ForeignKey('card_comments.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
