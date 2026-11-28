"""Cards service unit tests (R6, R7, R10, R18, R24, R28)."""
import uuid
from datetime import timedelta

import pytest

from app.blueprints.cards import service as svc
from app.exceptions import (
    AdminAccessRequiredError,
    BoardNotFoundException,
    CardNotFoundException,
    ColumnNotFoundException,
    InvalidAssigneeError,
    InvalidTargetColumnError,
    OrderConflictError,
    TeamAccessDeniedError,
)
from app.extensions import db
from app.models import (
    ActivityEventEntity,
    CardCommentEntity,
    CardEntity,
    NotificationEntity,
)
from app.utils.time import utc_now


def _fail_commit(monkeypatch):
    def boom():
        raise RuntimeError('commit failed')

    monkeypatch.setattr(db.session, 'commit', boom)


# ---- create_card_service -------------------------------------------------------------------

def test_create_card_appends_order_sets_completed_in_done_and_records_event(world):
    c1 = svc.create_card_service(
        world.todo.id,
        {'title': 'First', 'description': 'Desc', 'assignee_id': world.member.id},
        world.member.id,
    )
    c2 = svc.create_card_service(world.todo.id, {'title': 'Second'}, world.admin.id)
    c_done = svc.create_card_service(world.done.id, {'title': 'Already done'}, world.member.id)

    assert c1.order == 1024.0 and c1.completed_at is None
    assert c1.assignee_id == world.member.id and c1.created_by_id == world.member.id
    assert c2.order == 2048.0
    assert c_done.order == 1024.0 and c_done.completed_at is not None

    events = (
        db.session.query(ActivityEventEntity)
        .filter(ActivityEventEntity.entity_id == c1.id)
        .all()
    )
    assert len(events) == 1 and events[0].event_type == 'card_created'


def test_create_card_rejects_missing_column_non_member_and_bad_assignee(world):
    with pytest.raises(ColumnNotFoundException):
        svc.create_card_service(uuid.uuid4(), {'title': 'X'}, world.admin.id)
    with pytest.raises(TeamAccessDeniedError):
        svc.create_card_service(world.todo.id, {'title': 'X'}, world.outsider.id)
    with pytest.raises(InvalidAssigneeError):
        svc.create_card_service(
            world.todo.id, {'title': 'X', 'assignee_id': world.outsider.id}, world.admin.id
        )
    with pytest.raises(InvalidAssigneeError):
        svc.create_card_service(
            world.todo.id, {'title': 'X', 'assignee_id': uuid.uuid4()}, world.admin.id
        )
    assert db.session.query(ActivityEventEntity).count() == 0


def test_create_card_rolls_back_on_commit_error(world, monkeypatch):
    _fail_commit(monkeypatch)
    with pytest.raises(RuntimeError):
        svc.create_card_service(world.todo.id, {'title': 'Lost'}, world.admin.id)
    monkeypatch.undo()
    assert db.session.query(CardEntity).count() == 0
    assert db.session.query(ActivityEventEntity).count() == 0


# ---- update_card_service -------------------------------------------------------------------

def test_update_card_updates_fields_clears_assignee_and_records_event(world, factory):
    card = factory.card(world.todo, world.member, title='Old', assignee=world.member)
    factory.session.commit()

    updated = svc.update_card_service(
        card.id,
        {'title': 'New', 'description': 'Details', 'assignee_id': None},
        world.member2.id,
    )
    assert updated.title == 'New'
    assert updated.description == 'Details'
    assert updated.assignee_id is None
    events = (
        db.session.query(ActivityEventEntity)
        .filter(
            ActivityEventEntity.entity_id == card.id,
            ActivityEventEntity.event_type == 'card_updated',
        )
        .all()
    )
    assert len(events) == 1 and events[0].actor_id == world.member2.id


def test_update_card_rejects_missing_soft_deleted_outsider_and_bad_assignee(world, factory):
    deleted = factory.card(world.todo, world.admin, deleted_at=utc_now())
    active = factory.card(world.todo, world.admin, title='Keep')
    factory.session.commit()

    with pytest.raises(CardNotFoundException):
        svc.update_card_service(uuid.uuid4(), {'title': 'X'}, world.admin.id)
    with pytest.raises(CardNotFoundException):
        svc.update_card_service(deleted.id, {'title': 'X'}, world.outsider.id)
    with pytest.raises(TeamAccessDeniedError):
        svc.update_card_service(active.id, {'title': 'X'}, world.outsider.id)
    with pytest.raises(InvalidAssigneeError):
        svc.update_card_service(active.id, {'assignee_id': world.outsider.id}, world.admin.id)
    assert db.session.get(CardEntity, active.id).title == 'Keep'


def test_update_card_rolls_back_on_commit_error(world, factory, monkeypatch):
    card = factory.card(world.todo, world.admin, title='Keep')
    factory.session.commit()
    _fail_commit(monkeypatch)
    with pytest.raises(RuntimeError):
        svc.update_card_service(card.id, {'title': 'Lost'}, world.admin.id)
    monkeypatch.undo()
    assert db.session.get(CardEntity, card.id).title == 'Keep'


# ---- delete_card_service -------------------------------------------------------------------

def test_delete_card_soft_deletes_and_retains_comments_and_notifications(world, factory):
    card = factory.card(world.todo, world.member)
    comment = factory.comment(card, world.member, content='Hi @card_admin')
    notif = NotificationEntity(
        recipient_id=world.admin.id,
        type='mention',
        message='m',
        comment_id=comment.id,
    )
    db.session.add(notif)
    factory.session.commit()

    # Member deletes own card; Admin can delete another member's card
    res = svc.delete_card_service(card.id, world.member.id)
    assert res == {'id': str(card.id)}
    assert db.session.get(CardEntity, card.id).deleted_at is not None
    assert db.session.get(CardCommentEntity, comment.id) is not None
    assert db.session.get(NotificationEntity, notif.id) is not None

    card2 = factory.card(world.todo, world.member, order=2048.0)
    factory.session.commit()
    assert svc.delete_card_service(card2.id, world.admin.id) == {'id': str(card2.id)}


def test_delete_card_rejects_other_member_outsider_and_soft_deleted(world, factory):
    card = factory.card(world.todo, world.member)
    deleted = factory.card(world.todo, world.member, order=2048.0, deleted_at=utc_now())
    factory.session.commit()

    with pytest.raises(AdminAccessRequiredError):
        svc.delete_card_service(card.id, world.member2.id)
    with pytest.raises(TeamAccessDeniedError):
        svc.delete_card_service(card.id, world.outsider.id)
    with pytest.raises(CardNotFoundException):
        svc.delete_card_service(deleted.id, world.outsider.id)
    assert db.session.get(CardEntity, card.id).deleted_at is None


def test_delete_card_rolls_back_on_commit_error(world, factory, monkeypatch):
    card = factory.card(world.todo, world.admin)
    factory.session.commit()
    _fail_commit(monkeypatch)
    with pytest.raises(RuntimeError):
        svc.delete_card_service(card.id, world.admin.id)
    monkeypatch.undo()
    assert db.session.get(CardEntity, card.id).deleted_at is None


# ---- move_card_service ---------------------------------------------------------------------

def test_move_card_transitions_completed_at_and_is_idempotent(world, factory):
    c1 = factory.card(world.todo, world.member, order=1024.0)
    done2 = factory.column(world.board, name='Archive Done', order=3072.0, is_done=True)
    factory.session.commit()

    # todo -> done sets completed_at
    r1 = svc.move_card_service(
        c1.id, {'column_id': world.done.id, 'order': 1024.0}, world.member.id
    )
    assert r1['rebalanced'] is False
    assert r1['card'].completed_at is not None
    ts = r1['card'].completed_at

    # idempotent repeat move
    r1_repeat = svc.move_card_service(
        c1.id, {'column_id': world.done.id, 'order': 1024.0}, world.member.id
    )
    assert r1_repeat['card'].order == 1024.0 and r1_repeat['card'].column_id == world.done.id

    # done -> done2 preserves existing completed_at
    past = utc_now() - timedelta(days=3)
    c1.completed_at = past
    db.session.commit()
    r2 = svc.move_card_service(c1.id, {'column_id': done2.id, 'order': 1024.0}, world.member.id)
    assert r2['card'].completed_at == past

    # done2 -> todo clears completed_at
    r3 = svc.move_card_service(
        c1.id, {'column_id': world.todo.id, 'order': 512.0}, world.member.id
    )
    assert r3['card'].completed_at is None and ts is not None


def test_move_card_rejects_conflict_other_board_and_allows_deleted_sibling_order(world, factory):
    c1 = factory.card(world.todo, world.member, order=1024.0)
    c2 = factory.card(world.todo, world.member, order=2048.0)
    factory.card(world.todo, world.member, order=3072.0, deleted_at=utc_now())
    factory.session.commit()

    with pytest.raises(OrderConflictError):
        svc.move_card_service(
            c1.id, {'column_id': world.todo.id, 'order': 2048.0}, world.member.id
        )
    # Soft-deleted sibling's order (3072.0) does not block active card
    res = svc.move_card_service(
        c1.id, {'column_id': world.todo.id, 'order': 3072.0}, world.member.id
    )
    assert res['card'].order == 3072.0

    with pytest.raises(InvalidTargetColumnError):
        svc.move_card_service(c2.id, {'column_id': uuid.uuid4(), 'order': 512.0}, world.member.id)
    with pytest.raises(InvalidTargetColumnError):
        svc.move_card_service(c2.id, {'column_id': world.col_b.id, 'order': 512.0}, world.member.id)


# ---- list_cards_service --------------------------------------------------------------------

def test_list_cards_search_and_my_tasks(world, factory):
    c1 = factory.card(world.todo, world.member, title='Fix Login Bug', description='secret',
                      assignee=world.member, order=1024.0)
    c2 = factory.card(world.done, world.member, title='Write Docs',
                      assignee=world.admin, order=1024.0)
    factory.card(world.todo, world.member, title='Deleted Login',
                 assignee=world.member, order=2048.0, deleted_at=utc_now())
    factory.card(world.col_b, world.admin_b, title='Other Team Login',
                 assignee=world.admin_b, order=1024.0)
    factory.session.commit()

    # Search by title case-insensitive, ignores description
    found = svc.list_cards_service(world.member.id, {'q': 'login'})
    assert [c['id'] for c in found] == [c1.id]
    assert svc.list_cards_service(world.member.id, {'q': 'secret'}) == []

    # My Tasks (assignee=me)
    mine = svc.list_cards_service(world.member.id, {'assignee': 'me'})
    assert [c['id'] for c in mine] == [c1.id]

    # Combined filters + board_id checks
    both = svc.list_cards_service(
        world.admin.id, {'q': 'docs', 'board_id': world.board.id}
    )
    assert [c['id'] for c in both] == [c2.id]

    with pytest.raises(BoardNotFoundException):
        svc.list_cards_service(world.member.id, {'q': 'a', 'board_id': uuid.uuid4()})
    with pytest.raises(TeamAccessDeniedError):
        svc.list_cards_service(world.member.id, {'q': 'a', 'board_id': world.board_b.id})
