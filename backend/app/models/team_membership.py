import uuid

from sqlalchemy.sql.elements import conv

from app.extensions import db
from app.utils.time import utc_now


class TeamMembershipEntity(db.Model):
    __tablename__ = 'team_memberships'
    __table_args__ = (
        db.UniqueConstraint(
            'team_id', 'user_id', name='uq_team_memberships_team_id_user_id'
        ),
        db.CheckConstraint(
            "role IN ('admin', 'member')", name=conv('ck_team_memberships_role')
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

    # team_id needs no separate index: the unique constraint starts with it.
    team_id = db.Column(
        db.UUID,
        db.ForeignKey('teams.id', ondelete='CASCADE'),
        nullable=False,
    )
    user_id = db.Column(
        db.UUID,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    role = db.Column(db.String(20), nullable=False, default='member')
