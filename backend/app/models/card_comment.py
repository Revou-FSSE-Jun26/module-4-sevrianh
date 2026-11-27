import uuid

from app.extensions import db
from app.utils.time import utc_now


class CardCommentEntity(db.Model):
    __tablename__ = 'card_comments'

    id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False,
        default=utc_now, onupdate=utc_now,
    )
    # The only tombstone marker (DB-06): there is no is_deleted column.
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)

    card_id = db.Column(
        db.UUID,
        db.ForeignKey('cards.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    author_id = db.Column(
        db.UUID,
        db.ForeignKey('users.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
    )
    parent_comment_id = db.Column(
        db.UUID,
        db.ForeignKey('card_comments.id', ondelete='CASCADE'),
        nullable=True,
        index=True,
    )
    content = db.Column(db.Text, nullable=False)

    # DB-12: self-referential; a soft-deleted parent keeps its replies.
    replies = db.relationship(
        'CardCommentEntity',
        backref=db.backref('parent', remote_side='CardCommentEntity.id'),
        lazy='select',
        order_by='CardCommentEntity.created_at',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )
    notifications = db.relationship(
        'NotificationEntity',
        backref='comment',
        lazy='select',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )
