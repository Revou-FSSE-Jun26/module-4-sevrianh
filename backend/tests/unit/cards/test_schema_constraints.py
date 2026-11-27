"""Constraint and partial-index tests on PostgreSQL (DB-06, DB-08, DB-09)."""
import re

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import (
    ActivityEventEntity, BoardColumnEntity, CardCommentEntity, CardEntity, NotificationEntity,
    TeamEntity,
)
from app.utils.time import utc_now


def violated(session, action) -> str:
    """Run `action` in a savepoint, expect an IntegrityError and return the constraint name."""
    with pytest.raises(IntegrityError) as exc:
        with session.begin_nested():
            action()
    return exc.value.orig.diag.constraint_name


def index_def(session, name: str) -> str:
    return session.execute(
        text('SELECT indexdef FROM pg_indexes WHERE indexname = :n'), {'n': name}).scalar_one()


# ---- users ----------------------------------------------------------------------------

@pytest.mark.parametrize('username', ['Alice', 'has space', 'ab', 'bad-dash'])
def test_username_format_check_rejects_invalid_values(db_session, factory, username):
    assert violated(db_session, lambda: factory.user(username=username)) == \
        'ck_users_username_format'


@pytest.mark.parametrize('username', ['abc', 'a_1', 'a' * 30])
def test_username_format_check_accepts_valid_values(db_session, factory, username):
    assert factory.user(username=username).username == username


def test_username_is_unique(db_session, factory):
    factory.user(username='dupe_name')
    assert violated(db_session, lambda: factory.user(username='dupe_name')) == \
        'uq_users_username'


def test_email_is_unique_case_insensitively(db_session, factory):
    factory.user(email='a@example.com')
    assert violated(db_session, lambda: factory.user(email='A@example.com')) == \
        'uq_users_email_lower'


def test_email_unique_index_is_on_lower_email(db_session):
    definition = index_def(db_session, 'uq_users_email_lower')
    assert 'UNIQUE' in definition and 'lower((email)::text)' in definition


# ---- team memberships and teams ---------------------------------------------------------

def test_membership_pair_is_unique(db_session, factory):
    team, user = factory.team(), factory.user()
    factory.membership(team, user)
    assert violated(db_session, lambda: factory.membership(team, user)) == \
        'uq_team_memberships_team_id_user_id'


def test_membership_role_check_accepts_only_admin_and_member(db_session, factory):
    team, user = factory.team(), factory.user()
    assert violated(db_session, lambda: factory.membership(team, user, role='owner')) == \
        'ck_team_memberships_role'
    assert factory.membership(team, user, role='admin').role == 'admin'


def test_second_personal_team_for_same_owner_is_rejected(db_session, factory):
    owner = factory.user()
    factory.team(owner=owner, is_personal=True)
    assert violated(db_session, lambda: factory.team(owner=owner, is_personal=True)) == \
        'uq_teams_owner_id_personal'


def test_owner_may_have_many_shared_teams_and_one_personal(db_session, factory):
    owner = factory.user()
    factory.team(owner=owner, is_personal=True)
    factory.team(owner=owner)
    factory.team(owner=owner)
    other = factory.user()
    factory.team(owner=other, is_personal=True)
    count = db_session.scalar(select(db.func.count()).select_from(TeamEntity))
    assert count == 4


def test_personal_team_index_predicate(db_session):
    definition = index_def(db_session, 'uq_teams_owner_id_personal')
    assert 'UNIQUE' in definition
    assert re.search(r'WHERE \(?is_personal IS TRUE\)?', definition)


# ---- notifications and activity events ----------------------------------------------------

def _notification(factory, db_session, **kw):
    comment = kw.pop('comment', None) or factory.comment()
    recipient = kw.pop('recipient', None) or factory.user()
    row = NotificationEntity(recipient_id=recipient.id, comment_id=comment.id,
                             type=kw.pop('type', 'mention'), message='m', **kw)
    db_session.add(row)
    db_session.flush()
    return row


def test_notification_recipient_comment_type_is_unique(db_session, factory):
    comment, recipient = factory.comment(), factory.user()
    _notification(factory, db_session, comment=comment, recipient=recipient)
    assert violated(db_session, lambda: _notification(
        factory, db_session, comment=comment, recipient=recipient)) == \
        'uq_notifications_recipient_id_comment_id_type'


def test_notification_type_check_accepts_only_mention(db_session, factory):
    assert violated(db_session, lambda: _notification(
        factory, db_session, type='reply')) == 'ck_notifications_type'


def test_notification_recipient_created_at_index_exists(db_session):
    definition = index_def(db_session, 'ix_notifications_recipient_id_created_at')
    assert '(recipient_id, created_at)' in definition


@pytest.mark.parametrize('event_type', [
    'card_created', 'card_updated', 'card_moved', 'card_deleted', 'comment_added'])
def test_activity_event_type_accepts_the_five_values(db_session, factory, event_type):
    board, actor, card = factory.board(), factory.user(), factory.card()
    db_session.add(ActivityEventEntity(
        board_id=board.id, actor_id=actor.id, event_type=event_type,
        entity_type='card', entity_id=card.id))
    db_session.flush()


def test_activity_event_type_rejects_other_values(db_session, factory):
    board, actor, card = factory.board(), factory.user(), factory.card()

    def insert():
        db_session.add(ActivityEventEntity(
            board_id=board.id, actor_id=actor.id, event_type='card_archived',
            entity_type='card', entity_id=card.id))
        db_session.flush()

    assert violated(db_session, insert) == 'ck_activity_events_event_type'


# ---- ordering: check constraints and partial unique indexes -----------------------------------

@pytest.mark.parametrize('order', [0.0, -1.0])
def test_card_order_must_be_positive(db_session, factory, order):
    column = factory.column()
    assert violated(db_session, lambda: factory.card(column, order=order)) == \
        'ck_cards_order_positive'


@pytest.mark.parametrize('order', [0.0, -5.0])
def test_column_order_must_be_positive(db_session, factory, order):
    board = factory.board()
    assert violated(db_session, lambda: factory.column(board, order=order)) == \
        'ck_board_columns_order_positive'


@pytest.mark.parametrize('table,name,columns', [
    ('cards', 'uq_cards_column_id_order_active', '(column_id, "order")'),
    ('board_columns', 'uq_board_columns_board_id_order_active', '(board_id, "order")'),
])
def test_partial_unique_index_metadata(db_session, table, name, columns):
    definition = index_def(db_session, name)
    assert 'UNIQUE INDEX' in definition
    assert columns in definition
    assert re.search(r'WHERE \(?deleted_at IS NULL\)?', definition)
    model = {'cards': CardEntity, 'board_columns': BoardColumnEntity}[table]
    index = next(i for i in model.__table__.indexes if i.name == name)
    assert index.unique is True
    assert str(index.dialect_options['postgresql']['where']) == 'deleted_at IS NULL'


@pytest.mark.parametrize('table', ['cards', 'board_columns'])
def test_composite_lookup_index_exists_and_no_full_unique_on_order(db_session, table):
    lookup = {'cards': 'ix_cards_column_id_order',
              'board_columns': 'ix_board_columns_board_id_order'}[table]
    definition = index_def(db_session, lookup)
    assert 'UNIQUE' not in definition and '"order"' in definition
    constraints = db_session.execute(text(
        "SELECT pg_get_constraintdef(c.oid) FROM pg_constraint c "
        "JOIN pg_class t ON t.oid = c.conrelid WHERE t.relname = :t AND c.contype = 'u'"),
        {'t': table}).scalars().all()
    assert not [c for c in constraints if 'order' in c]
    full_unique = db_session.execute(text(
        "SELECT indexdef FROM pg_indexes WHERE tablename = :t AND indexdef LIKE 'CREATE UNIQUE%' "
        'AND indexdef LIKE \'%"order"%\' AND indexdef NOT LIKE \'%WHERE%\''), {'t': table}).all()
    assert full_unique == []


def test_two_active_cards_in_one_column_cannot_share_an_order(db_session, factory):
    column = factory.column()
    factory.card(column, order=1024.0)
    assert violated(db_session, lambda: factory.card(column, order=1024.0)) == \
        'uq_cards_column_id_order_active'


def test_same_card_order_is_allowed_in_different_columns(db_session, factory):
    board = factory.board()
    factory.card(factory.column(board, order=1.0), order=1024.0)
    factory.card(factory.column(board, order=2.0), order=1024.0)


def test_soft_deleted_card_order_does_not_block_an_active_card(db_session, factory):
    column = factory.column()
    old = factory.card(column, order=1024.0)
    old.deleted_at = utc_now()
    db_session.flush()
    new = factory.card(column, order=1024.0)
    assert new.id != old.id
    # A second soft-deleted card with the same order is also allowed.
    factory.card(column, order=1024.0, deleted_at=utc_now())


def test_two_active_columns_in_one_board_cannot_share_an_order(db_session, factory):
    board = factory.board()
    factory.column(board, order=1024.0)
    assert violated(db_session, lambda: factory.column(board, order=1024.0)) == \
        'uq_board_columns_board_id_order_active'


def test_soft_deleted_column_order_does_not_block_an_active_column(db_session, factory):
    board = factory.board()
    old = factory.column(board, order=1024.0)
    old.deleted_at = utc_now()
    db_session.flush()
    factory.column(board, order=1024.0)


# ---- soft delete retention (DB-06) ---------------------------------------------------------

def test_soft_deleted_card_keeps_comments_notifications_and_events(db_session, factory):
    card = factory.card()
    comment = factory.comment(card)
    note = _notification(factory, db_session, comment=comment)
    event = ActivityEventEntity(board_id=card.column.board_id, actor_id=card.created_by_id,
                                event_type='card_created', entity_type='card',
                                entity_id=card.id)
    db_session.add(event)
    db_session.flush()
    card.deleted_at = utc_now()
    db_session.flush()
    db_session.expire_all()
    assert db_session.get(CardEntity, card.id).deleted_at is not None
    assert db_session.get(CardCommentEntity, comment.id).deleted_at is None
    assert db_session.get(NotificationEntity, note.id) is not None
    assert db_session.get(ActivityEventEntity, event.id) is not None
    active = db_session.scalars(select(CardEntity).where(CardEntity.deleted_at.is_(None))).all()
    assert active == []


def test_soft_deleted_parent_comment_keeps_content_and_replies(db_session, factory):
    card = factory.card()
    parent = factory.comment(card, content='original text')
    reply = factory.comment(card, parent_comment_id=parent.id)
    parent.deleted_at = utc_now()
    db_session.flush()
    db_session.expire_all()
    kept = db_session.get(CardCommentEntity, parent.id)
    assert kept.content == 'original text'
    assert kept.deleted_at is not None
    assert db_session.get(CardCommentEntity, reply.id).parent_comment_id == parent.id
