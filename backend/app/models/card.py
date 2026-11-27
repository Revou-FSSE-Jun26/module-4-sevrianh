import uuid

from sqlalchemy.sql.elements import conv

from app.extensions import db
from app.utils.time import utc_now


class CardEntity(db.Model):
    __tablename__ = 'cards'
    __table_args__ = (
        # conv() keeps the exact name; the ck convention would prefix it again.
        db.CheckConstraint('"order" > 0', name=conv('ck_cards_order_positive')),
        db.Index('ix_cards_column_id_order', 'column_id', 'order'),
        db.Index(
            'uq_cards_column_id_order_active', 'column_id', 'order',
            unique=True,
            postgresql_where=db.text('deleted_at IS NULL'),
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

    # column_id needs no separate index: ix_cards_column_id_order starts with it.
    column_id = db.Column(
        db.UUID,
        db.ForeignKey('board_columns.id', ondelete='CASCADE'),
        nullable=False,
    )
    created_by_id = db.Column(
        db.UUID,
        db.ForeignKey('users.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
    )
    assignee_id = db.Column(
        db.UUID,
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    order = db.Column(db.Float, nullable=False)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # DB-12: the ORM cascade applies to physical deletes only, never to a soft delete.
    comments = db.relationship(
        'CardCommentEntity',
        backref='card',
        lazy='select',
        order_by='CardCommentEntity.created_at',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )
