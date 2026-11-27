import uuid

from sqlalchemy.sql.elements import conv

from app.extensions import db
from app.utils.time import utc_now


class ActivityEventEntity(db.Model):
    __tablename__ = 'activity_events'
    __table_args__ = (
        # conv() keeps the exact name; the ck convention would prefix it again.
        db.CheckConstraint(
            "event_type IN ('card_created', 'card_updated', 'card_moved', "
            "'card_deleted', 'comment_added')",
            name=conv('ck_activity_events_event_type'),
        ),
        db.Index('ix_activity_events_board_id_created_at', 'board_id', 'created_at'),
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

    # board_id needs no separate index: the composite index starts with it.
    board_id = db.Column(
        db.UUID,
        db.ForeignKey('boards.id', ondelete='CASCADE'),
        nullable=False,
    )
    actor_id = db.Column(
        db.UUID,
        db.ForeignKey('users.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
    )
    event_type = db.Column(db.String(50), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)
    # Polymorphic reference (Card or Comment): deliberately not a foreign key.
    entity_id = db.Column(db.UUID, nullable=False)
