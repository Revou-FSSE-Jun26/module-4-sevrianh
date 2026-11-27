"""Schema, naming, foreign-key and relationship tests on PostgreSQL (DB-01 to DB-12, TC-10)."""
import pytest
from sqlalchemy import delete, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import configure_mappers

from app.extensions import db
from app.models import (
    ActivityEventEntity, BoardColumnEntity, BoardEntity, CardCommentEntity, CardEntity,
    InviteLinkEntity, NotificationEntity, TeamEntity, TeamMembershipEntity, UserEntity,
)

BASE_COLUMNS = ['id', 'created_at', 'updated_at', 'deleted_at']

DOMAIN_COLUMNS = {
    'users': ['name', 'username', 'email', 'password_hash'],
    'teams': ['name', 'is_personal', 'owner_id'],
    'team_memberships': ['team_id', 'user_id', 'role'],
    'boards': ['team_id', 'name'],
    'board_columns': ['board_id', 'name', 'order', 'is_done'],
    'cards': ['column_id', 'created_by_id', 'assignee_id', 'title', 'description', 'order',
              'completed_at'],
    'card_comments': ['card_id', 'author_id', 'parent_comment_id', 'content'],
    'notifications': ['recipient_id', 'comment_id', 'type', 'message', 'is_read'],
    'activity_events': ['board_id', 'actor_id', 'event_type', 'entity_type', 'entity_id'],
    'invite_links': ['board_id', 'created_by_id', 'token_hash', 'revoked_at'],
}

FOREIGN_KEY_INDEXES = [
    'ix_team_memberships_user_id', 'ix_teams_owner_id', 'ix_boards_team_id',
    'ix_cards_assignee_id', 'ix_cards_created_by_id', 'ix_card_comments_card_id',
    'ix_card_comments_author_id', 'ix_card_comments_parent_comment_id',
    'ix_notifications_comment_id', 'ix_activity_events_actor_id',
    'ix_invite_links_board_id', 'ix_invite_links_created_by_id',
]

# DB-11 delete policy: (table, column) -> ondelete
ON_DELETE = {
    ('teams', 'owner_id'): 'RESTRICT',
    ('team_memberships', 'team_id'): 'CASCADE',
    ('team_memberships', 'user_id'): 'CASCADE',
    ('boards', 'team_id'): 'RESTRICT',
    ('board_columns', 'board_id'): 'CASCADE',
    ('cards', 'column_id'): 'CASCADE',
    ('cards', 'created_by_id'): 'RESTRICT',
    ('cards', 'assignee_id'): 'SET NULL',
    ('card_comments', 'card_id'): 'CASCADE',
    ('card_comments', 'author_id'): 'RESTRICT',
    ('card_comments', 'parent_comment_id'): 'CASCADE',
    ('notifications', 'recipient_id'): 'CASCADE',
    ('notifications', 'comment_id'): 'CASCADE',
    ('activity_events', 'board_id'): 'CASCADE',
    ('activity_events', 'actor_id'): 'RESTRICT',
    ('invite_links', 'board_id'): 'CASCADE',
    ('invite_links', 'created_by_id'): 'RESTRICT',
}

# DB-12 catalog: (parent, parent attribute, child, backref on child)
RELATIONSHIPS = [
    (TeamEntity, 'memberships', TeamMembershipEntity, 'team'),
    (TeamEntity, 'boards', BoardEntity, 'team'),
    (UserEntity, 'owned_teams', TeamEntity, 'owner'),
    (UserEntity, 'memberships', TeamMembershipEntity, 'user'),
    (BoardEntity, 'columns', BoardColumnEntity, 'board'),
    (BoardEntity, 'activity_events', ActivityEventEntity, 'board'),
    (BoardEntity, 'invite_links', InviteLinkEntity, 'board'),
    (BoardColumnEntity, 'cards', CardEntity, 'column'),
    (UserEntity, 'assigned_cards', CardEntity, 'assignee'),
    (UserEntity, 'created_cards', CardEntity, 'creator'),
    (CardEntity, 'comments', CardCommentEntity, 'card'),
    (CardCommentEntity, 'replies', CardCommentEntity, 'parent'),
    (CardCommentEntity, 'notifications', NotificationEntity, 'comment'),
    (UserEntity, 'comments', CardCommentEntity, 'author'),
    (UserEntity, 'notifications', NotificationEntity, 'recipient'),
    (UserEntity, 'activity_events', ActivityEventEntity, 'actor'),
    (UserEntity, 'created_invite_links', InviteLinkEntity, 'created_by'),
]


@pytest.fixture()
def inspector(app, db_session):
    return inspect(db.engine)


def test_expected_table_set_is_exactly_ten(inspector):
    tables = set(inspector.get_table_names()) - {'alembic_version'}
    assert tables == set(DOMAIN_COLUMNS)
    assert len(db.metadata.tables) == 10
    assert set(db.metadata.tables) == set(DOMAIN_COLUMNS)


def test_no_board_level_membership_table_or_model(inspector):
    assert 'board_members' not in inspector.get_table_names()
    assert 'columns' not in inspector.get_table_names()
    names = {m.class_.__name__ for m in db.Model.registry.mappers}
    assert 'BoardMemberEntity' not in names


@pytest.mark.parametrize('table', sorted(DOMAIN_COLUMNS))
def test_model_and_database_columns_match_schema_catalog(table, inspector):
    expected = set(BASE_COLUMNS + DOMAIN_COLUMNS[table])
    assert set(db.metadata.tables[table].columns.keys()) == expected
    assert {c['name'] for c in inspector.get_columns(table)} == expected


def test_no_is_deleted_column_and_no_user_id_or_card_id_on_notifications(inspector):
    comment_cols = {c['name'] for c in inspector.get_columns('card_comments')}
    notification_cols = {c['name'] for c in inspector.get_columns('notifications')}
    assert 'is_deleted' not in comment_cols
    assert not any('is_deleted' in {c['name'] for c in inspector.get_columns(t)}
                   for t in DOMAIN_COLUMNS)
    assert 'user_id' not in notification_cols
    assert 'card_id' not in notification_cols
    assert {'recipient_id', 'comment_id'} <= notification_cols


def test_order_columns_are_float_and_required(inspector):
    for table in ('cards', 'board_columns'):
        col = next(c for c in inspector.get_columns(table) if c['name'] == 'order')
        assert str(col['type']).upper().startswith('DOUBLE') or 'FLOAT' in str(col['type']).upper()
        assert col['nullable'] is False


def test_primary_key_is_uuid_and_timestamps_are_timezone_aware(inspector):
    for table in DOMAIN_COLUMNS:
        cols = {c['name']: c for c in inspector.get_columns(table)}
        assert str(cols['id']['type']).upper() == 'UUID'
        for name in ('created_at', 'updated_at', 'deleted_at'):
            assert cols[name]['type'].timezone is True
        assert cols['deleted_at']['nullable'] is True
        assert cols['created_at']['nullable'] is False
        assert cols['updated_at']['nullable'] is False


def test_all_twelve_foreign_key_indexes_exist_by_name(db_session):
    rows = db_session.execute(
        text("SELECT indexname FROM pg_indexes WHERE schemaname = 'public'")).scalars().all()
    missing = [name for name in FOREIGN_KEY_INDEXES if name not in rows]
    assert missing == []
    assert len(FOREIGN_KEY_INDEXES) == 12


def test_no_title_search_index_exists(db_session):
    rows = db_session.execute(text(
        "SELECT indexname, indexdef FROM pg_indexes "
        "WHERE schemaname = 'public' AND tablename = 'cards'")).all()
    assert 'ix_cards_title_lower_trgm' not in [r[0] for r in rows]
    assert not any('trgm' in r[1] or 'lower(' in r[1] for r in rows)


def test_constraint_and_index_names_use_configured_prefixes(inspector):
    for table in DOMAIN_COLUMNS:
        assert inspector.get_pk_constraint(table)['name'].startswith('pk_')
        for fk in inspector.get_foreign_keys(table):
            assert fk['name'].startswith('fk_')
        for uq in inspector.get_unique_constraints(table):
            assert uq['name'].startswith('uq_')
        for ck in inspector.get_check_constraints(table):
            assert ck['name'].startswith('ck_')
        for ix in inspector.get_indexes(table):
            assert ix['name'].startswith(('ix_', 'uq_'))


def test_foreign_key_delete_policy_matches_db_11(inspector):
    actual = {}
    for table in DOMAIN_COLUMNS:
        for fk in inspector.get_foreign_keys(table):
            column = fk['constrained_columns'][0]
            actual[(table, column)] = (fk['options'].get('ondelete') or '').upper()
    assert actual == ON_DELETE


def test_relationships_both_sides():
    configure_mappers()
    for parent, attribute, child, backref in RELATIONSHIPS:
        assert hasattr(parent, attribute), f'{parent.__name__}.{attribute}'
        assert hasattr(child, backref), f'{child.__name__}.{backref}'


def test_ambiguous_foreign_key_relationships_resolve(db_session, factory):
    owner = factory.user()
    team = factory.team(owner=owner)
    assignee = factory.user()
    card = factory.card(created_by=owner, assignee_id=assignee.id)
    db_session.refresh(card)
    assert card.assignee is assignee
    assert card.creator is owner
    assert team.owner is owner
    assert assignee.assigned_cards == [card]
    assert owner.created_cards == [card]
    assert owner.owned_teams == [team]


def test_relationship_navigation_and_ordering(db_session, factory):
    board = factory.board()
    second = factory.column(board, order=2048.0)
    first = factory.column(board, order=1024.0)
    creator = factory.user()
    c2 = factory.card(first, creator, order=2048.0)
    c1 = factory.card(first, creator, order=1024.0)
    parent = factory.comment(c1, creator)
    reply = factory.comment(c1, creator, parent_comment_id=parent.id)
    db_session.expire_all()
    assert board.columns == [first, second]
    assert first.cards == [c1, c2]
    assert c1.column is first
    assert parent.replies == [reply]
    assert reply.parent is parent
    assert c1.comments == [parent, reply]


def _board_with_everything(factory, db_session):
    owner = factory.user()
    team = factory.team(owner=owner)
    factory.membership(team, owner, role='admin')
    board = factory.board(team)
    column = factory.column(board)
    card = factory.card(column, owner)
    comment = factory.comment(card, owner)
    recipient = factory.user()
    db_session.add_all([
        NotificationEntity(recipient_id=recipient.id, comment_id=comment.id, type='mention',
                           message='You were mentioned'),
        ActivityEventEntity(board_id=board.id, actor_id=owner.id, event_type='card_created',
                            entity_type='card', entity_id=card.id),
        InviteLinkEntity(board_id=board.id, created_by_id=owner.id, token_hash='h' * 64),
    ])
    db_session.flush()
    return owner, team, board


def test_board_delete_cascades_to_all_dependents(db_session, factory):
    owner, team, board = _board_with_everything(factory, db_session)
    db_session.delete(board)
    db_session.flush()
    db_session.expire_all()
    for model in (BoardColumnEntity, CardEntity, CardCommentEntity, NotificationEntity,
                  ActivityEventEntity, InviteLinkEntity):
        assert db_session.scalar(select(db.func.count()).select_from(model)) == 0, model
    assert db_session.get(TeamEntity, team.id) is not None
    assert db_session.get(UserEntity, owner.id) is not None


def test_column_delete_cascades_to_cards_and_comments(db_session, factory):
    column = factory.column()
    card = factory.card(column)
    factory.comment(card)
    db_session.delete(column)
    db_session.flush()
    db_session.expire_all()
    assert db_session.scalar(select(db.func.count()).select_from(CardEntity)) == 0
    assert db_session.scalar(select(db.func.count()).select_from(CardCommentEntity)) == 0


def test_membership_delete_keeps_authored_cards_and_comments(db_session, factory):
    admin = factory.user()
    team = factory.team(owner=admin)
    author = factory.user()
    membership = factory.membership(team, author)
    column = factory.column(factory.board(team))
    card = factory.card(column, author)
    comment = factory.comment(card, author)
    db_session.delete(membership)
    db_session.flush()
    db_session.expire_all()
    assert db_session.get(TeamMembershipEntity, membership.id) is None
    assert db_session.get(CardEntity, card.id) is not None
    assert db_session.get(CardCommentEntity, comment.id) is not None
    assert db_session.get(UserEntity, author.id) is not None


def test_deleting_user_who_owns_a_team_is_rejected(db_session, factory):
    owner = factory.user()
    factory.team(owner=owner)
    with pytest.raises(IntegrityError) as exc:
        with db_session.begin_nested():
            db_session.execute(delete(UserEntity).where(UserEntity.id == owner.id))
    assert exc.value.orig.diag.constraint_name == 'fk_teams_owner_id_users'


def test_deleting_team_with_boards_is_rejected(db_session, factory):
    board = factory.board()
    with pytest.raises(IntegrityError) as exc:
        with db_session.begin_nested():
            db_session.execute(delete(TeamEntity).where(TeamEntity.id == board.team_id))
    assert exc.value.orig.diag.constraint_name == 'fk_boards_team_id_teams'


def test_deleting_assignee_sets_card_assignee_to_null(db_session, factory):
    assignee = factory.user()
    card = factory.card(assignee_id=assignee.id)
    db_session.execute(delete(UserEntity).where(UserEntity.id == assignee.id))
    db_session.expire_all()
    assert db_session.get(CardEntity, card.id).assignee_id is None
