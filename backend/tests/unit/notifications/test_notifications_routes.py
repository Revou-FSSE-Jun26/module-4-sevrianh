"""Unit tests for notifications routes (T-41; R9.7-R9.12)."""
import uuid

from app.blueprints.comments.service import create_comment_service
from app.models import NotificationEntity


def _mention(world, content='@bob'):
    create_comment_service(world.card.id, {'content': content}, world.alice.id)


def test_list_route_returns_200_with_pagination_envelope(client, world, auth):
    _mention(world)
    resp = client.get('/api/notifications', headers=auth(world.bob))
    assert resp.status_code == 200
    data = resp.get_json()['data']
    assert set(data) == {'items', 'page', 'per_page', 'total', 'total_pages', 'unread_count'}
    assert (data['page'], data['per_page'], data['total']) == (1, 10, 1)
    item = data['items'][0]
    assert item['card_id'] == str(world.card.id) and item['board_id'] == str(world.board.id)
    assert 'recipient_id' not in item


def test_list_route_honours_per_page_and_never_exceeds_it(client, world, auth):
    for _ in range(4):
        _mention(world)
    data = client.get(
        '/api/notifications?page=2&per_page=3', headers=auth(world.bob)).get_json()['data']
    assert len(data['items']) == 1 and data['total_pages'] == 2 and data['unread_count'] == 4


def test_list_route_returns_400_for_invalid_query(client, world, auth):
    for query in ('page=0', 'per_page=0', 'per_page=51', 'page=abc', 'per_page=-1'):
        resp = client.get(f'/api/notifications?{query}', headers=auth(world.bob))
        assert resp.status_code == 400, query
        assert isinstance(resp.get_json()['error'], str)


def test_list_route_accepts_per_page_50(client, world, auth):
    assert client.get(
        '/api/notifications?per_page=50', headers=auth(world.bob)).status_code == 200


def test_list_route_returns_401_without_token(client, world):
    resp = client.get('/api/notifications')
    assert resp.status_code == 401 and 'error' in resp.get_json()


def test_list_route_rejects_guest_invite_token(client, world):
    resp = client.get('/api/notifications', headers={'X-Invite-Token': 'whatever'})
    assert resp.status_code == 401


def test_mark_read_route_returns_200_and_is_idempotent(client, world, auth, db_session):
    _mention(world)
    note = db_session.query(NotificationEntity).one()
    for _ in range(2):
        resp = client.patch(f'/api/notifications/{note.id}/read', headers=auth(world.bob))
        assert resp.status_code == 200
        assert resp.get_json()['data']['is_read'] is True
    data = client.get('/api/notifications', headers=auth(world.bob)).get_json()['data']
    assert data['unread_count'] == 0 and data['total'] == 1


def test_mark_read_route_returns_404_for_other_users_notification(
        client, world, auth, db_session):
    _mention(world)
    note = db_session.query(NotificationEntity).one()
    resp = client.patch(f'/api/notifications/{note.id}/read', headers=auth(world.carol))
    assert resp.status_code == 404
    assert resp.get_json() == {'error': 'Not found'}
    db_session.refresh(note)
    assert note.is_read is False


def test_mark_read_route_returns_404_for_unknown_id(client, world, auth):
    resp = client.patch(f'/api/notifications/{uuid.uuid4()}/read', headers=auth(world.bob))
    assert resp.status_code == 404


def test_mark_read_route_returns_401_without_token(client, world):
    assert client.patch(f'/api/notifications/{uuid.uuid4()}/read').status_code == 401
