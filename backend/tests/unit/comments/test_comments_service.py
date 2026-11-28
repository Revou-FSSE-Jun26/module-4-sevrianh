"""Unit tests for the comments service (T-43; R8, R9.13, R2.8)."""
import uuid
from datetime import timedelta

import pytest
from marshmallow import ValidationError

from app.blueprints.comments.service import (
    create_comment_service,
    delete_comment_service,
    list_comments_service,
    update_comment_service,
)
from app.exceptions import (
    CardNotFoundException,
    CommentNotFoundException,
    CommentOwnershipError,
    TeamAccessDeniedError,
)
from app.models import ActivityEventEntity, NotificationEntity
from app.utils.time import utc_now


def test_create_comment_service_stores_comment_and_activity(world, db_session):
    comment = create_comment_service(world.card.id, {'content': 'Hello'}, world.member.id)
    assert comment.content == 'Hello'
    assert comment.author_id == world.member.id
    assert comment.parent_comment_id is None
    assert db_session.query(ActivityEventEntity).count() == 1


def test_create_comment_service_accepts_reply_on_same_card(world):
    parent = create_comment_service(world.card.id, {'content': 'Parent'}, world.admin.id)
    reply = create_comment_service(
        world.card.id, {'content': 'Reply', 'parent_id': parent.id}, world.member.id)
    assert reply.parent_comment_id == parent.id


def test_create_comment_service_rejects_parent_from_other_card(world, factory):
    other_card = factory.card(factory.column(world.board, order=2048.0), created_by=world.admin)
    other = factory.comment(other_card, world.admin)
    with pytest.raises(ValidationError):
        create_comment_service(
            world.card.id, {'content': 'x', 'parent_id': other.id}, world.member.id)


def test_create_comment_service_rejects_unknown_parent(world):
    with pytest.raises(ValidationError):
        create_comment_service(
            world.card.id, {'content': 'x', 'parent_id': uuid.uuid4()}, world.member.id)


def test_create_comment_service_rejects_non_member(world):
    with pytest.raises(TeamAccessDeniedError):
        create_comment_service(world.card.id, {'content': 'x'}, world.outsider.id)


def test_create_comment_service_rejects_unknown_card(world):
    with pytest.raises(CardNotFoundException):
        create_comment_service(uuid.uuid4(), {'content': 'x'}, world.member.id)


def test_create_comment_service_rejects_soft_deleted_card(world, db_session):
    world.card.deleted_at = utc_now()
    db_session.commit()
    with pytest.raises(CardNotFoundException):
        create_comment_service(world.card.id, {'content': 'x'}, world.member.id)


def test_create_comment_service_creates_mention_notification(world, db_session):
    create_comment_service(world.card.id, {'content': 'hi @cm_member2'}, world.member.id)
    rows = db_session.query(NotificationEntity).all()
    assert [r.recipient_id for r in rows] == [world.member2.id]


def test_list_comments_service_orders_by_created_at_ascending(world, factory, db_session):
    now = utc_now()
    second = factory.comment(world.card, world.admin, content='second')
    first = factory.comment(world.card, world.admin, content='first')
    first.created_at = now - timedelta(minutes=5)
    second.created_at = now
    db_session.commit()
    assert [c.content for c in list_comments_service(world.card.id)] == ['first', 'second']


def test_list_comments_service_keeps_tombstone_with_live_reply(world, factory, db_session):
    parent = factory.comment(world.card, world.admin, content='parent')
    factory.comment(world.card, world.member, content='reply', parent_comment_id=parent.id)
    parent.deleted_at = utc_now()
    db_session.commit()
    ids = [c.id for c in list_comments_service(world.card.id)]
    assert parent.id in ids and len(ids) == 2


def test_list_comments_service_omits_deleted_without_live_reply(world, factory, db_session):
    parent = factory.comment(world.card, world.admin, content='parent')
    reply = factory.comment(world.card, world.member, parent_comment_id=parent.id)
    parent.deleted_at = utc_now()
    reply.deleted_at = utc_now()
    db_session.commit()
    assert list_comments_service(world.card.id) == []


def test_list_comments_service_rejects_soft_deleted_card(world, db_session):
    world.card.deleted_at = utc_now()
    db_session.commit()
    with pytest.raises(CardNotFoundException):
        list_comments_service(world.card.id)


def test_update_comment_service_changes_content_and_updated_at(world, factory, db_session):
    comment = factory.comment(world.card, world.member, content='old')
    db_session.commit()
    created = comment.created_at
    updated = update_comment_service(comment.id, {'content': 'new'}, world.member.id)
    assert updated.content == 'new'
    assert updated.updated_at >= created


def test_update_comment_service_notifies_only_new_mentions(world, db_session):
    comment = create_comment_service(world.card.id, {'content': '@cm_member2'}, world.member.id)
    update_comment_service(comment.id, {'content': '@cm_member2 @cm_admin'}, world.member.id)
    recipients = sorted(str(r.recipient_id) for r in db_session.query(NotificationEntity))
    assert recipients == sorted([str(world.member2.id), str(world.admin.id)])


def test_update_comment_service_rejects_non_author(world, factory, db_session):
    comment = factory.comment(world.card, world.member)
    db_session.commit()
    with pytest.raises(CommentOwnershipError):
        update_comment_service(comment.id, {'content': 'x'}, world.member2.id)


def test_update_comment_service_rejects_admin_who_is_not_author(world, factory, db_session):
    comment = factory.comment(world.card, world.member)
    db_session.commit()
    with pytest.raises(CommentOwnershipError):
        update_comment_service(comment.id, {'content': 'x'}, world.admin.id)


def test_update_comment_service_rejects_unknown_and_deleted(world, factory, db_session):
    with pytest.raises(CommentNotFoundException):
        update_comment_service(uuid.uuid4(), {'content': 'x'}, world.member.id)
    comment = factory.comment(world.card, world.member)
    comment.deleted_at = utc_now()
    db_session.commit()
    with pytest.raises(CommentNotFoundException):
        update_comment_service(comment.id, {'content': 'x'}, world.member.id)


def test_delete_comment_service_returns_id_and_keeps_row(world, factory, db_session):
    comment = factory.comment(world.card, world.member)
    db_session.commit()
    assert delete_comment_service(comment.id, world.member.id) == {'id': comment.id}
    db_session.refresh(comment)
    assert comment.deleted_at is not None


def test_delete_comment_service_removes_its_notifications(world, db_session):
    comment = create_comment_service(world.card.id, {'content': '@cm_member2'}, world.member.id)
    assert db_session.query(NotificationEntity).count() == 1
    delete_comment_service(comment.id, world.member.id)
    assert db_session.query(NotificationEntity).count() == 0


def test_delete_comment_service_rejects_non_author_and_admin(world, factory, db_session):
    comment = factory.comment(world.card, world.member)
    db_session.commit()
    for other in (world.member2, world.admin):
        with pytest.raises(CommentOwnershipError):
            delete_comment_service(comment.id, other.id)


def test_delete_comment_service_rejects_second_delete(world, factory, db_session):
    comment = factory.comment(world.card, world.member)
    db_session.commit()
    delete_comment_service(comment.id, world.member.id)
    with pytest.raises(CommentNotFoundException):
        delete_comment_service(comment.id, world.member.id)
