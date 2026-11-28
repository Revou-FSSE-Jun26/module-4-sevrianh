"""Initial schema: ten tables, named CHECK constraints and partial unique indexes.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2025-01-01 00:00:00.000000

Hand-written from the models (tech.md TC-10, database.md DB-05, DB-08, DB-09, DB-11).
No title-search index and no pg_trgm extension is created (design D-07, U-03).
"""
from alembic import op
import sqlalchemy as sa

revision = '0001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def _base_columns() -> list:
    """The four required columns of DB-05."""
    return [
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    ]


def _fk(column: str, target: str, ondelete: str, table: str) -> sa.ForeignKeyConstraint:
    ref_table = target.split('.')[0]
    return sa.ForeignKeyConstraint(
        [column], [target], ondelete=ondelete,
        name=op.f(f'fk_{table}_{column}_{ref_table}'),
    )


def upgrade():
    op.create_table(
        'users',
        *_base_columns(),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=30), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.CheckConstraint(
            "username ~ '^[a-z0-9_]{3,30}$'", name=op.f('ck_users_username_format')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
        sa.UniqueConstraint('username', name='uq_users_username'),
    )
    op.create_index('uq_users_email_lower', 'users', [sa.text('lower(email)')], unique=True)

    op.create_table(
        'teams',
        *_base_columns(),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('is_personal', sa.Boolean(), nullable=False),
        sa.Column('owner_id', sa.UUID(), nullable=False),
        _fk('owner_id', 'users.id', 'RESTRICT', 'teams'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_teams')),
    )
    op.create_index('ix_teams_owner_id', 'teams', ['owner_id'])
    op.create_index(
        'uq_teams_owner_id_personal', 'teams', ['owner_id'], unique=True,
        postgresql_where=sa.text('is_personal IS TRUE'),
    )

    op.create_table(
        'team_memberships',
        *_base_columns(),
        sa.Column('team_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.CheckConstraint(
            "role IN ('admin', 'member')", name=op.f('ck_team_memberships_role')),
        _fk('team_id', 'teams.id', 'CASCADE', 'team_memberships'),
        _fk('user_id', 'users.id', 'CASCADE', 'team_memberships'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_team_memberships')),
        sa.UniqueConstraint(
            'team_id', 'user_id', name='uq_team_memberships_team_id_user_id'),
    )
    op.create_index('ix_team_memberships_user_id', 'team_memberships', ['user_id'])

    op.create_table(
        'boards',
        *_base_columns(),
        sa.Column('team_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        _fk('team_id', 'teams.id', 'RESTRICT', 'boards'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_boards')),
    )
    op.create_index('ix_boards_team_id', 'boards', ['team_id'])

    op.create_table(
        'board_columns',
        *_base_columns(),
        sa.Column('board_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('order', sa.Float(), nullable=False),
        sa.Column('is_done', sa.Boolean(), nullable=False),
        sa.CheckConstraint('"order" > 0', name=op.f('ck_board_columns_order_positive')),
        _fk('board_id', 'boards.id', 'CASCADE', 'board_columns'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_board_columns')),
    )
    op.create_index('ix_board_columns_board_id_order', 'board_columns', ['board_id', 'order'])
    op.create_index(
        'uq_board_columns_board_id_order_active', 'board_columns', ['board_id', 'order'],
        unique=True, postgresql_where=sa.text('deleted_at IS NULL'),
    )

    op.create_table(
        'cards',
        *_base_columns(),
        sa.Column('column_id', sa.UUID(), nullable=False),
        sa.Column('created_by_id', sa.UUID(), nullable=False),
        sa.Column('assignee_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('order', sa.Float(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('"order" > 0', name=op.f('ck_cards_order_positive')),
        _fk('column_id', 'board_columns.id', 'CASCADE', 'cards'),
        _fk('created_by_id', 'users.id', 'RESTRICT', 'cards'),
        _fk('assignee_id', 'users.id', 'SET NULL', 'cards'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_cards')),
    )
    op.create_index('ix_cards_column_id_order', 'cards', ['column_id', 'order'])
    op.create_index(
        'uq_cards_column_id_order_active', 'cards', ['column_id', 'order'],
        unique=True, postgresql_where=sa.text('deleted_at IS NULL'),
    )
    op.create_index('ix_cards_created_by_id', 'cards', ['created_by_id'])
    op.create_index('ix_cards_assignee_id', 'cards', ['assignee_id'])

    op.create_table(
        'card_comments',
        *_base_columns(),
        sa.Column('card_id', sa.UUID(), nullable=False),
        sa.Column('author_id', sa.UUID(), nullable=False),
        sa.Column('parent_comment_id', sa.UUID(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        _fk('card_id', 'cards.id', 'CASCADE', 'card_comments'),
        _fk('author_id', 'users.id', 'RESTRICT', 'card_comments'),
        sa.ForeignKeyConstraint(
            ['parent_comment_id'], ['card_comments.id'], ondelete='CASCADE',
            name=op.f('fk_card_comments_parent_comment_id_card_comments')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_card_comments')),
    )
    op.create_index('ix_card_comments_card_id', 'card_comments', ['card_id'])
    op.create_index('ix_card_comments_author_id', 'card_comments', ['author_id'])
    op.create_index(
        'ix_card_comments_parent_comment_id', 'card_comments', ['parent_comment_id'])

    op.create_table(
        'notifications',
        *_base_columns(),
        sa.Column('recipient_id', sa.UUID(), nullable=False),
        sa.Column('comment_id', sa.UUID(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('message', sa.String(length=255), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False),
        sa.CheckConstraint("type IN ('mention')", name=op.f('ck_notifications_type')),
        _fk('recipient_id', 'users.id', 'CASCADE', 'notifications'),
        _fk('comment_id', 'card_comments.id', 'CASCADE', 'notifications'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_notifications')),
        sa.UniqueConstraint(
            'recipient_id', 'comment_id', 'type',
            name='uq_notifications_recipient_id_comment_id_type'),
    )
    op.create_index(
        'ix_notifications_recipient_id_created_at', 'notifications',
        ['recipient_id', 'created_at'])
    op.create_index('ix_notifications_comment_id', 'notifications', ['comment_id'])

    op.create_table(
        'activity_events',
        *_base_columns(),
        sa.Column('board_id', sa.UUID(), nullable=False),
        sa.Column('actor_id', sa.UUID(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.UUID(), nullable=False),
        sa.CheckConstraint(
            "event_type IN ('card_created', 'card_updated', 'card_moved', "
            "'card_deleted', 'comment_added')",
            name=op.f('ck_activity_events_event_type')),
        _fk('board_id', 'boards.id', 'CASCADE', 'activity_events'),
        _fk('actor_id', 'users.id', 'RESTRICT', 'activity_events'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_activity_events')),
    )
    op.create_index(
        'ix_activity_events_board_id_created_at', 'activity_events',
        ['board_id', 'created_at'])
    op.create_index('ix_activity_events_actor_id', 'activity_events', ['actor_id'])

    op.create_table(
        'invite_links',
        *_base_columns(),
        sa.Column('board_id', sa.UUID(), nullable=False),
        sa.Column('created_by_id', sa.UUID(), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        _fk('board_id', 'boards.id', 'CASCADE', 'invite_links'),
        _fk('created_by_id', 'users.id', 'RESTRICT', 'invite_links'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_invite_links')),
        sa.UniqueConstraint('token_hash', name='uq_invite_links_token_hash'),
    )
    op.create_index('ix_invite_links_board_id', 'invite_links', ['board_id'])
    op.create_index('ix_invite_links_created_by_id', 'invite_links', ['created_by_id'])


def downgrade():
    # Dropping a table drops its indexes and constraints; children go first.
    for table in (
        'invite_links', 'activity_events', 'notifications', 'card_comments',
        'cards', 'board_columns', 'boards', 'team_memberships', 'teams',
    ):
        op.drop_table(table)
    op.drop_index('uq_users_email_lower', table_name='users')
    op.drop_table('users')
