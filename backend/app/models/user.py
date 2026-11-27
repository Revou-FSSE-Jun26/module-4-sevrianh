import uuid

from sqlalchemy.sql.elements import conv

from app.extensions import db
from app.utils.time import utc_now


class UserEntity(db.Model):
    __tablename__ = 'users'
    __table_args__ = (
        db.UniqueConstraint('username', name='uq_users_username'),
        # conv() keeps the exact name; the ck convention would prefix it again.
        db.CheckConstraint(
            "username ~ '^[a-z0-9_]{3,30}$'", name=conv('ck_users_username_format')
        ),
        db.Index('uq_users_email_lower', db.text('lower(email)'), unique=True),
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

    name = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # DB-12: Team memberships; rows may be removed independently.
    memberships = db.relationship(
        'TeamMembershipEntity',
        backref='user',
        lazy='select',
    )
    # DB-12: Teams owned (TeamEntity.owner_id is RESTRICT, no ORM cascade).
    owned_teams = db.relationship(
        'TeamEntity',
        backref='owner',
        lazy='select',
        foreign_keys='TeamEntity.owner_id',
    )
    # DB-12: CardEntity has two foreign keys to users, so foreign_keys is explicit.
    assigned_cards = db.relationship(
        'CardEntity',
        backref='assignee',
        lazy='select',
        foreign_keys='CardEntity.assignee_id',
    )
    created_cards = db.relationship(
        'CardEntity',
        backref='creator',
        lazy='select',
        foreign_keys='CardEntity.created_by_id',
    )
    # DB-12: no ORM delete cascade; authored history is preserved.
    comments = db.relationship(
        'CardCommentEntity',
        backref='author',
        lazy='select',
        foreign_keys='CardCommentEntity.author_id',
    )
    notifications = db.relationship(
        'NotificationEntity',
        backref='recipient',
        lazy='select',
        foreign_keys='NotificationEntity.recipient_id',
    )
    activity_events = db.relationship(
        'ActivityEventEntity',
        backref='actor',
        lazy='select',
        foreign_keys='ActivityEventEntity.actor_id',
    )
    created_invite_links = db.relationship(
        'InviteLinkEntity',
        backref='created_by',
        lazy='select',
        foreign_keys='InviteLinkEntity.created_by_id',
    )
