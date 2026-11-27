import uuid

from app.extensions import db
from app.utils.time import utc_now


class BoardEntity(db.Model):
    __tablename__ = 'boards'

    id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False,
        default=utc_now, onupdate=utc_now,
    )
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)

    team_id = db.Column(
        db.UUID,
        db.ForeignKey('teams.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(100), nullable=False)

    columns = db.relationship(
        'BoardColumnEntity',
        backref='board',
        lazy='select',
        order_by='BoardColumnEntity.order',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )
    activity_events = db.relationship(
        'ActivityEventEntity',
        backref='board',
        lazy='select',
        order_by='ActivityEventEntity.created_at',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )
    invite_links = db.relationship(
        'InviteLinkEntity',
        backref='board',
        lazy='select',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )
