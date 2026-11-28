"""Unit tests for the notifications service (T-41; R9.1-R9.13)."""
import uuid

import pytest

from app.blueprints.boards.service import remove_team_member_service
from app.blueprints.comments.service import (
    create_comment_service,
    delete_comment_service,
    update_comment_service,
)
from app.blueprints.notifications.service import (
    list_notifications_service,
    mark_notification_read_service,
)
from app.exceptions import NotificationNotFoundException
from app.models import NotificationEntity
from app.utils.time import utc_now

QUERY = {'page': 1, 'per_page': 10}


def _recipients(db_session):
    return sorted(
        r.recipient_id for r in db_session.query(NotificationEntity).all())


def _comment(world, content, author=None):
    return create_comment_service(world.card.id, {'content': content}, (author or world.alice).id)


def test_single_mention_creates_one_unread_notification(world, db_session):
    _comment(world, '@bob please review')
    rows = db_session.query(NotificationEntity).all()
    assert [r.recipient_id for r in rows] == [world.bob.id]
    assert rows[0].is_read is False and rows[0].type == 'mention'


def test_repeated_mention_in_one_comment_creates_one_notification(world, db_session):
    _comment(world, '@bob @bob and again @BOB')
    assert _recipients(db_session) == [world.bob.id]


def test_self_mention_creates_none(world, db_session):
    _comment(world, 'note to self @alice')
    assert db_session.query(NotificationEntity).count() == 0


def test_mention_of_username_outside_team_creates_none(world, db_session):
    _comment(world, '@outsider @nobody_here')
    assert db_session.query(NotificationEntity).count() == 0


def test_mention_of_removed_member_creates_none(world, db_session):
    remove_team_member_service(world.board.id, world.alice.id, world.carol.id)
    _comment(world, '@carol')
    assert db_session.query(NotificationEntity).count() == 0


def test_mention_is_case_insensitive_and_needs_three_characters(world, db_session):
    _comment(world, '@BoB @bo')
    assert _recipients(db_session) == [world.bob.id]


def test_mention_inside_a_longer_token_does_not_match(world, db_session):
    _comment(world, '@' + 'b' * 31)
    assert db_session.query(NotificationEntity).count() == 0


def test_two_mentions_create_one_each(world, db_session):
    _comment(world, '@bob @carol')
    assert _recipients(db_session) == sorted([world.bob.id, world.carol.id])


def test_message_format_and_255_character_limit(world, db_session):
    _comment(world, '@bob')
    assert db_session.query(NotificationEntity).one().message == \
        'Alice mentioned you on "Deploy to Railway"'
    db_session.query(NotificationEntity).delete()
    db_session.commit()
    world.card.title = 'T' * 200
    world.alice.name = 'A' * 100
    db_session.commit()
    _comment(world, '@carol')
    note = db_session.query(NotificationEntity).one()
    assert len(note.message) == 255 and note.message.startswith('A' * 100 + ' mentioned')


def test_edit_notifies_only_newly_mentioned_members(world, db_session):
    comment = _comment(world, '@bob')
    update_comment_service(comment.id, {'content': '@bob @carol'}, world.alice.id)
    assert _recipients(db_session) == sorted([world.bob.id, world.carol.id])
    update_comment_service(comment.id, {'content': '@bob @carol again'}, world.alice.id)
    assert db_session.query(NotificationEntity).count() == 2


def test_list_returns_pagination_fields_and_newest_first(world):
    for _ in range(3):
        _comment(world, '@bob')
    page = list_notifications_service(world.bob.id, {'page': 1, 'per_page': 2})
    assert set(page) == {'items', 'page', 'per_page', 'total', 'total_pages', 'unread_count'}
    assert len(page['items']) == 2 and page['total'] == 3 and page['total_pages'] == 2
    assert page['items'][0]['created_at'] >= page['items'][1]['created_at']
    assert page['items'][0]['card_id'] == world.card.id
    assert page['items'][0]['board_id'] == world.board.id


def test_list_empty_has_zero_total_pages(world):
    page = list_notifications_service(world.bob.id, QUERY)
    assert (page['items'], page['total'], page['total_pages'], page['unread_count']) == \
        ([], 0, 0, 0)


def test_list_page_past_the_end_is_empty_but_counts_hold(world):
    _comment(world, '@bob')
    page = list_notifications_service(world.bob.id, {'page': 5, 'per_page': 10})
    assert page['items'] == [] and page['total'] == 1 and page['unread_count'] == 1


def test_unread_count_covers_all_pages_not_only_current_page(world):
    for _ in range(3):
        _comment(world, '@bob')
    page = list_notifications_service(world.bob.id, {'page': 1, 'per_page': 1})
    assert len(page['items']) == 1 and page['unread_count'] == 3


def test_list_shows_only_own_notifications(world):
    _comment(world, '@bob')
    assert list_notifications_service(world.carol.id, QUERY)['total'] == 0


def test_list_hides_notifications_of_soft_deleted_card(world, db_session):
    _comment(world, '@bob')
    world.card.deleted_at = utc_now()
    db_session.commit()
    page = list_notifications_service(world.bob.id, QUERY)
    assert page['total'] == 0 and page['unread_count'] == 0


def test_mark_read_sets_flag_and_is_idempotent(world, db_session):
    _comment(world, '@bob')
    note = db_session.query(NotificationEntity).one()
    first = mark_notification_read_service(note.id, world.bob.id)
    second = mark_notification_read_service(note.id, world.bob.id)
    assert first['is_read'] is True and second['is_read'] is True
    assert list_notifications_service(world.bob.id, QUERY)['unread_count'] == 0


def test_mark_read_of_other_users_notification_is_not_found(world, db_session):
    _comment(world, '@bob')
    note = db_session.query(NotificationEntity).one()
    with pytest.raises(NotificationNotFoundException):
        mark_notification_read_service(note.id, world.carol.id)
    db_session.refresh(note)
    assert note.is_read is False


def test_mark_read_unknown_id_is_not_found(world):
    with pytest.raises(NotificationNotFoundException):
        mark_notification_read_service(uuid.uuid4(), world.bob.id)


def test_deleting_comment_removes_its_notifications(world, db_session):
    comment = _comment(world, '@bob @carol')
    delete_comment_service(comment.id, world.alice.id)
    assert db_session.query(NotificationEntity).count() == 0


def test_removing_member_deletes_their_notifications_only(world, db_session):
    _comment(world, '@bob @carol')
    remove_team_member_service(world.board.id, world.alice.id, world.bob.id)
    assert _recipients(db_session) == [world.carol.id]
