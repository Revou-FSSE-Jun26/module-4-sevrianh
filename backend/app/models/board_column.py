import uuid

from sqlalchemy.sql.elements import conv

from app.extensions import db
from app.utils.time import utc_now


class BoardColumnEntity(db.Model):
    __tablename__ = 'board_columns'
    __table_args__ = (
        db.CheckConstraint('"order" > 0', name=conv('ck_board_columns_order_positive')),
        db.Index('ix_board_columns_board_id_order', 'board_id', 'order'),
        db.Index(
            'uq_board_columns_board_id_order_active', 'board_id', 'order',
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

    # board_id needs no separate index: ix_board_columns_board_id_order starts with it.
    board_id = db.Column(
        db.UUID,
        db.ForeignKey('boards.id', ondelete='CASCADE'),
        nullable=False,
    )
    name = db.Column(db.String(100), nullable=False)
    order = db.Column(db.Float, nullable=False)
    is_done = db.Column(db.Boolean, nullable=False, default=False)

    # Columns are hard-deleted (U-01): deleted_at is declared (DB-05) but never written.
    # Task 3.2 adds the cards relationship (DB-12) here.
