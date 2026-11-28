"""Unit tests for comments routes (T-43; R2.2, R8, R20)."""
import uuid

from app.blueprints.boards.service import create_invite_link_service
from app.utils.time import utc_now


def _url(card):
    return f'/api/cards/{card.id}/comments'


def test_create_comment_route_returns_201(client, world, auth):
    resp = client.post(_url(world.card), json={'content': 'Hi'}, headers=auth(world.member))
    assert resp.status_code == 201
    data = resp.get_json()['data']
    assert data['content'] == 'Hi'
    assert data['parent_id'] is None and data['is_deleted'] is False


def test_create_comment_route_returns_400_for_missing_blank_or_long_content(
        client, world, auth):
    for body in ({}, {'content': '   '}, {'content': 'x' * 2001}):
        resp = client.post(_url(world.card), json=body, headers=auth(world.member))
        assert resp.status_code == 400
        assert isinstance(resp.get_json()['error'], str)


def test_create_comment_route_accepts_2000_characters(client, world, auth):
    resp = client.post(_url(world.card), json={'content': 'x' * 2000}, headers=auth(world.member))
    assert resp.status_code == 201


def test_create_comment_route_returns_400_for_foreign_parent(client, world, auth, factory):
    other = factory.comment(factory.card(factory.column(world.board, order=2048.0)), world.admin)
    factory.session.commit()
    resp = client.post(
        _url(world.card), json={'content': 'x', 'parent_id': str(other.id)},
        headers=auth(world.member))
    assert resp.status_code == 400


def test_create_comment_route_returns_401_unauthenticated(client, world):
    resp = client.post(_url(world.card), json={'content': 'x'})
    assert resp.status_code == 401
    assert 'error' in resp.get_json()


def test_create_comment_route_returns_403_for_non_member(client, world, auth):
    resp = client.post(_url(world.card), json={'content': 'x'}, headers=auth(world.outsider))
    assert resp.status_code == 403


def test_create_comment_route_returns_404_for_missing_and_soft_deleted_card(
        client, world, auth, db_session):
    missing = client.post(
        f'/api/cards/{uuid.uuid4()}/comments', json={'content': 'x'}, headers=auth(world.member))
    assert missing.status_code == 404
    world.card.deleted_at = utc_now()
    db_session.commit()
    deleted = client.post(_url(world.card), json={'content': 'x'}, headers=auth(world.member))
    assert deleted.status_code == 404


def test_create_comment_route_rejects_guest_write(client, world):
    invite = create_invite_link_service(world.board.id, world.admin.id)
    resp = client.post(
        _url(world.card), json={'content': 'x'}, headers={'X-Invite-Token': invite['token']})
    assert resp.status_code == 401


def test_list_comments_route_returns_thread_for_member(client, world, auth, factory):
    parent = factory.comment(world.card, world.admin, content='parent')
    factory.comment(world.card, world.member, content='reply', parent_comment_id=parent.id)
    factory.session.commit()
    resp = client.get(_url(world.card), headers=auth(world.member))
    assert resp.status_code == 200
    items = resp.get_json()['data']
    assert [c['content'] for c in items] == ['parent', 'reply']
    assert items[1]['parent_id'] == str(parent.id)


def test_list_comments_route_guest_with_valid_link_reads(client, world, factory):
    factory.comment(world.card, world.admin, content='visible')
    factory.session.commit()
    invite = create_invite_link_service(world.board.id, world.admin.id)
    resp = client.get(_url(world.card), headers={'X-Invite-Token': invite['token']})
    assert resp.status_code == 200
    assert resp.get_json()['data'][0]['content'] == 'visible'


def test_list_comments_route_guest_link_for_other_board_is_refused(client, world, factory):
    other_admin = factory.user()
    other_team = factory.team(owner=other_admin)
    factory.membership(other_team, other_admin, 'admin')
    other_board = factory.board(other_team)
    factory.session.commit()
    invite = create_invite_link_service(other_board.id, other_admin.id)
    resp = client.get(_url(world.card), headers={'X-Invite-Token': invite['token']})
    assert resp.status_code in (403, 404)
    assert 'data' not in resp.get_json()


def test_list_comments_route_returns_401_without_token_or_link(client, world):
    assert client.get(_url(world.card)).status_code == 401


def test_list_comments_route_returns_403_for_non_member(client, world, auth):
    assert client.get(_url(world.card), headers=auth(world.outsider)).status_code == 403


def test_list_comments_route_returns_404_for_soft_deleted_card(client, world, auth, db_session):
    world.card.deleted_at = utc_now()
    db_session.commit()
    assert client.get(_url(world.card), headers=auth(world.member)).status_code == 404


def test_list_comments_route_tombstone_only_with_live_reply(client, world, auth, factory):
    kept = factory.comment(world.card, world.admin, content='kept parent')
    factory.comment(world.card, world.member, parent_comment_id=kept.id)
    gone = factory.comment(world.card, world.admin, content='gone')
    kept.deleted_at = utc_now()
    gone.deleted_at = utc_now()
    factory.session.commit()
    items = client.get(_url(world.card), headers=auth(world.member)).get_json()['data']
    tomb = [c for c in items if c['id'] == str(kept.id)]
    assert len(tomb) == 1 and tomb[0]['is_deleted'] is True and tomb[0]['content'] == ''
    assert str(gone.id) not in [c['id'] for c in items]


def test_update_comment_route_returns_200_and_edit_indicator(client, world, auth, factory):
    comment = factory.comment(world.card, world.member, content='old')
    factory.session.commit()
    resp = client.patch(
        f'/api/comments/{comment.id}', json={'content': 'new'}, headers=auth(world.member))
    assert resp.status_code == 200
    data = resp.get_json()['data']
    assert data['content'] == 'new'
    assert data['updated_at'] >= data['created_at']


def test_update_comment_route_returns_403_for_non_author_including_admin(
        client, world, auth, factory):
    comment = factory.comment(world.card, world.member)
    factory.session.commit()
    for other in (world.member2, world.admin):
        resp = client.patch(
            f'/api/comments/{comment.id}', json={'content': 'x'}, headers=auth(other))
        assert resp.status_code == 403


def test_update_comment_route_returns_400_for_blank_content(client, world, auth, factory):
    comment = factory.comment(world.card, world.member)
    factory.session.commit()
    resp = client.patch(
        f'/api/comments/{comment.id}', json={'content': ''}, headers=auth(world.member))
    assert resp.status_code == 400


def test_update_comment_route_returns_401_and_404(client, world, auth, factory):
    comment = factory.comment(world.card, world.member)
    factory.session.commit()
    assert client.patch(f'/api/comments/{comment.id}', json={'content': 'x'}).status_code == 401
    missing = client.patch(
        f'/api/comments/{uuid.uuid4()}', json={'content': 'x'}, headers=auth(world.member))
    assert missing.status_code == 404


def test_delete_comment_route_returns_id_of_deleted_comment(client, world, auth, factory):
    comment = factory.comment(world.card, world.member)
    factory.session.commit()
    resp = client.delete(f'/api/comments/{comment.id}', headers=auth(world.member))
    assert resp.status_code == 200
    assert resp.get_json() == {'data': {'id': str(comment.id)}}


def test_delete_comment_route_returns_403_for_non_author_including_admin(
        client, world, auth, factory):
    comment = factory.comment(world.card, world.member)
    factory.session.commit()
    for other in (world.member2, world.admin):
        resp = client.delete(f'/api/comments/{comment.id}', headers=auth(other))
        assert resp.status_code == 403
    assert client.get(_url(world.card), headers=auth(world.member)).get_json()['data']


def test_delete_comment_route_returns_401_and_404(client, world, auth, factory):
    comment = factory.comment(world.card, world.member)
    factory.session.commit()
    assert client.delete(f'/api/comments/{comment.id}').status_code == 401
    assert client.delete(
        f'/api/comments/{uuid.uuid4()}', headers=auth(world.member)).status_code == 404


def test_delete_comment_route_rejects_guest(client, world, factory):
    comment = factory.comment(world.card, world.member)
    factory.session.commit()
    invite = create_invite_link_service(world.board.id, world.admin.id)
    resp = client.delete(
        f'/api/comments/{comment.id}', headers={'X-Invite-Token': invite['token']})
    assert resp.status_code == 401
