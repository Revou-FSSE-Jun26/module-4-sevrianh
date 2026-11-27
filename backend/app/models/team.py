import uuid

from app.extensions import db
from app.utils.time import utc_now


class TeamEntity(db.Model):
    __tablename__ = 'teams'
    __table_args__ = (
        db.Index(
            'uq_teams_owner_id_personal', 'owner_id',
            unique=True,
            postgresql_where=db.text('is_personal IS TRUE'),
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

    name = db.Column(db.String(255), nullable=False)
    is_personal = db.Column(db.Boolean, nullable=False, default=False)
    owner_id = db.Column(
        db.UUID,
        db.ForeignKey('users.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
    )

    memberships = db.relationship(
        'TeamMembershipEntity',
        backref='team',
        lazy='select',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )
    # Team deletion is RESTRICTed while Boards exist: no ORM cascade.
    boards = db.relationship(
        'BoardEntity',
        backref='team',
        lazy='select',
    )
