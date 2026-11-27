"""Columns route tests and permission checks (R2.5, R5, R24.6, BE-04, BE-07, BE-14)."""
import uuid

import pytest

from app.extensions import db
from app.models import BoardColumnEntity, CardCommentEntity, CardEntity
from app.utils.ordering import MIN_GAP

GENERIC = 'Not found or access denied'


def _error(res, status, message=None):
    assert res.status_code == status
    body = res.get_json()
    assert set(body) == {'error'} and isinstance(body['error'], str) and body['error']
    if message is not None:
        assert body['error'] == message


# ---- create column -------------------------------------------------------------------------

def test_create_column_returns_201_for_admin_and_member(client, world, auth):
    url = f'/api/boards/{world.board.id}/columns'
    res1 = client.post(url, json={'name': '  To Do  '}, headers=auth(world.member))
    assert res1.status_code == 201
    d1 = res1.get_json()['data']
    assert d1['name'] == 'To Do' and d1['order'] == 1024.0 and d1['is_done'] is False
    assert set(d1) == {
        'id', 'board_id', 'name', 'order', 'is_done', 'created_at', 'updated_at',
    }

    res2 = client.post(
        url, json={'name': 'x' * 100, 'is_done': True}, headers=auth(world.admin)
    )
    assert res2.status_code == 201
    d2 = res2.get_json()['data']
    assert d2['order'] == 2048.0 and d2['is_done'] is True


@pytest.mark.parametrize('body', [
    {},
    {'name': ''},
    {'name': '   '},
    {'name': 'x' * 101},
    {'name': 'Valid', 'is_done': 'not-a-bool'},
    {'name': 'Valid', 'is_done': None},
    {'name': 'Valid', 'extra': 1},
])
def test_create_column_returns_400_for_invalid_body(client, world, auth, body):
    res = client.post(
        f'/api/boards/{world.board.id}/columns', json=body, headers=auth(world.admin)
    )
    _error(res, 400)
    assert db.session.query(BoardColumnEntity).count() == 0


def test_create_column_returns_400_401_403_404(client, world, auth):
    url = f'/api/boards/{world.board.id}/columns'
    _error(client.post('/api/boards/not-a-uuid/columns', json={'name': 'A'},
                       headers=auth(world.admin)), 400)
    _error(client.post(url, json={'name': 'A'}), 401)
    _error(client.post(url, json={'name': 'A'}, headers=auth(world.outsider)), 403, GENERIC)
    _error(client.post(f'/api/boards/{uuid.uuid4()}/columns', json={'name': 'A'},
                       headers=auth(world.outsider)), 404, GENERIC)


# ---- update column -------------------------------------------------------------------------

def test_update_column_returns_200_and_toggles_is_done(client, world, auth, factory):
    col = factory.column(world.board, name='Work', is_done=False)
    card = factory.card(col, world.member)
    factory.session.commit()

    url = f'/api/columns/{col.id}'
    res = client.patch(url, json={'name': '  Done  ', 'is_done': True}, headers=auth(world.admin))
    assert res.status_code == 200
    data = res.get_json()['data']
    assert data['name'] == 'Done' and data['is_done'] is True
    assert db.session.get(CardEntity, card.id).completed_at is not None

    res2 = client.patch(url, json={'is_done': False}, headers=auth(world.admin))
    assert res2.status_code == 200 and res2.get_json()['data']['is_done'] is False
    assert db.session.get(CardEntity, card.id).completed_at is None


@pytest.mark.parametrize('body', [
    {}, {'name': ''}, {'name': '   '}, {'name': 'x' * 101},
    {'is_done': 'bad'}, {'name': 'Ok', 'extra': 1},
])
def test_update_column_returns_400_for_invalid_body(client, world, auth, factory, body):
    col = factory.column(world.board, name='Keep')
    factory.session.commit()
    _error(client.patch(f'/api/columns/{col.id}', json=body, headers=auth(world.admin)), 400)
    assert db.session.get(BoardColumnEntity, col.id).name == 'Keep'


def test_update_column_returns_400_401_403_404(client, world, auth, factory):
    col = factory.column(world.board)
    factory.session.commit()
    url = f'/api/columns/{col.id}'
    _error(client.patch('/api/columns/not-a-uuid', json={'name': 'X'},
                        headers=auth(world.admin)), 400)
    _error(client.patch(url, json={'name': 'X'}), 401)
    _error(client.patch(url, json={'name': 'X'}, headers=auth(world.member)),
           403, 'Admin access required')
    _error(client.patch(url, json={'is_done': True}, headers=auth(world.member)),
           403, 'Admin access required')
    _error(client.patch(url, json={'name': 'X'}, headers=auth(world.outsider)), 403, GENERIC)
    _error(client.patch(f'/api/columns/{uuid.uuid4()}', json={'name': 'X'},
                        headers=auth(world.outsider)), 404, GENERIC)


# ---- delete column -------------------------------------------------------------------------

def test_delete_column_returns_200_and_cascades(client, world, auth, factory):
    c1 = factory.column(world.board, order=1024.0)
    c2 = factory.column(world.board, order=2048.0)
    card = factory.card(c1, world.member)
    factory.comment(card, world.member)
    factory.session.commit()

    res = client.delete(f'/api/columns/{c1.id}', headers=auth(world.admin))
    assert res.status_code == 200 and res.get_json() == {'data': {'id': str(c1.id)}}
    assert db.session.get(BoardColumnEntity, c1.id) is None
    assert db.session.query(CardEntity).count() == 0
    assert db.session.query(CardCommentEntity).count() == 0
    assert db.session.get(BoardColumnEntity, c2.id).order == 2048.0


def test_delete_column_returns_400_401_403_404(client, world, auth, factory):
    col = factory.column(world.board)
    factory.session.commit()
    url = f'/api/columns/{col.id}'
    _error(client.delete('/api/columns/not-a-uuid', headers=auth(world.admin)), 400)
    _error(client.delete(url), 401)
    _error(client.delete(url, headers=auth(world.member)), 403, 'Admin access required')
    _error(client.delete(url, headers=auth(world.outsider)), 403, GENERIC)
    _error(client.delete(f'/api/columns/{uuid.uuid4()}', headers=auth(world.outsider)),
           404, GENERIC)
    assert db.session.get(BoardColumnEntity, col.id) is not None


# ---- reorder column ------------------------------------------------------------------------

def test_reorder_column_returns_200_and_updates_board_order(client, world, auth, factory):
    c1 = factory.column(world.board, name='A', order=1024.0)
    c2 = factory.column(world.board, name='B', order=2048.0)
    factory.session.commit()

    url = f'/api/boards/{world.board.id}/columns/reorder'
    res = client.patch(url, json={'column_id': str(c2.id), 'order': 512.0},
                       headers=auth(world.admin))
    assert res.status_code == 200
    data = res.get_json()['data']
    assert set(data) == {'column', 'rebalanced'}
    assert data['rebalanced'] is False and data['column']['order'] == 512.0

    board_res = client.get(f'/api/boards/{world.board.id}', headers=auth(world.member))
    assert [c['id'] for c in board_res.get_json()['data']['columns']] == [str(c2.id), str(c1.id)]


def test_reorder_column_rebalances_when_gap_below_min_gap(client, world, auth, factory):
    c1 = factory.column(world.board, name='A', order=1024.0)
    c2 = factory.column(world.board, name='B', order=2048.0)
    factory.session.commit()

    res = client.patch(
        f'/api/boards/{world.board.id}/columns/reorder',
        json={'column_id': str(c2.id), 'order': 1024.0 + MIN_GAP / 2},
        headers=auth(world.admin),
    )
    assert res.status_code == 200
    data = res.get_json()['data']
    assert data['rebalanced'] is True
    assert data['column']['order'] == 2048.0
    assert db.session.get(BoardColumnEntity, c1.id).order == 1024.0


def test_reorder_column_returns_409_envelope_only_on_equal_order(client, world, auth, factory):
    factory.column(world.board, name='A', order=1024.0)
    c2 = factory.column(world.board, name='B', order=2048.0)
    factory.session.commit()

    res = client.patch(
        f'/api/boards/{world.board.id}/columns/reorder',
        json={'column_id': str(c2.id), 'order': 1024.0},
        headers=auth(world.admin),
    )
    _error(res, 409)
    assert db.session.get(BoardColumnEntity, c2.id).order == 2048.0


@pytest.mark.parametrize('body', [
    {},
    {'column_id': 'not-a-uuid', 'order': 512.0},
    {'column_id': str(uuid.uuid4()), 'order': 0},
    {'column_id': str(uuid.uuid4()), 'order': -1},
    {'column_id': str(uuid.uuid4()), 'order': 'bad'},
    {'column_id': str(uuid.uuid4()), 'order': 512.0, 'extra': 1},
])
def test_reorder_column_returns_400_for_invalid_body(client, world, auth, body):
    res = client.patch(
        f'/api/boards/{world.board.id}/columns/reorder',
        json=body, headers=auth(world.admin),
    )
    _error(res, 400)


def test_reorder_column_returns_400_for_unknown_or_foreign_column(client, world, auth, factory):
    foreign = factory.column(world.board_b, order=1024.0)
    factory.session.commit()
    url = f'/api/boards/{world.board.id}/columns/reorder'
    _error(client.patch(url, json={'column_id': str(uuid.uuid4()), 'order': 512.0},
                        headers=auth(world.admin)), 400)
    _error(client.patch(url, json={'column_id': str(foreign.id), 'order': 512.0},
                        headers=auth(world.admin)), 400)


def test_reorder_column_returns_400_401_403_404(client, world, auth, factory):
    col = factory.column(world.board, order=1024.0)
    factory.session.commit()
    url = f'/api/boards/{world.board.id}/columns/reorder'
    payload = {'column_id': str(col.id), 'order': 512.0}
    _error(client.patch('/api/boards/not-a-uuid/columns/reorder', json=payload,
                        headers=auth(world.admin)), 400)
    _error(client.patch(url, json=payload), 401)
    _error(client.patch(url, json=payload, headers=auth(world.member)),
           403, 'Admin access required')
    _error(client.patch(url, json=payload, headers=auth(world.outsider)), 403, GENERIC)
    _error(client.patch(f'/api/boards/{uuid.uuid4()}/columns/reorder', json=payload,
                        headers=auth(world.outsider)), 404, GENERIC)


# ---- permission matrix cells for columns (-k permission) -----------------------------------

@pytest.mark.parametrize('action,role,expected', [
    ('create', 'admin', 201),
    ('create', 'member', 201),
    ('create', 'guest', 401),
    ('create', 'guest_jwt', 403),
    ('create', 'non_member', 403),
    ('rename', 'admin', 200),
    ('rename', 'member', 403),
    ('rename', 'guest', 401),
    ('rename', 'guest_jwt', 403),
    ('rename', 'non_member', 403),
    ('reorder', 'admin', 200),
    ('reorder', 'member', 403),
    ('reorder', 'guest', 401),
    ('reorder', 'guest_jwt', 403),
    ('reorder', 'non_member', 403),
    ('delete', 'admin', 200),
    ('delete', 'member', 403),
    ('delete', 'guest', 401),
    ('delete', 'guest_jwt', 403),
    ('delete', 'non_member', 403),
])
def test_permission_columns_matrix(client, world, auth, factory, action, role, expected):
    col = factory.column(world.board, name='Orig', order=1024.0)
    factory.session.commit()
    token = client.post(
        f'/api/boards/{world.board.id}/invite-links', headers=auth(world.admin)
    ).get_json()['data']['token']
    headers_map = {
        'admin': auth(world.admin),
        'member': auth(world.member),
        'guest': {'X-Invite-Token': token},
        'guest_jwt': {**auth(world.outsider), 'X-Invite-Token': token},
        'non_member': auth(world.outsider),
    }
    specs = {
        'create': ('post', f'/api/boards/{world.board.id}/columns', {'name': 'New'}),
        'rename': ('patch', f'/api/columns/{col.id}', {'name': 'Renamed'}),
        'reorder': ('patch', f'/api/boards/{world.board.id}/columns/reorder',
                    {'column_id': str(col.id), 'order': 512.0}),
        'delete': ('delete', f'/api/columns/{col.id}', None),
    }
    method, path, body = specs[action]
    kwargs = {'headers': headers_map[role]}
    if body is not None:
        kwargs['json'] = body
    res = getattr(client, method)(path, **kwargs)
    assert res.status_code == expected
    if expected in (401, 403):
        refreshed = db.session.get(BoardColumnEntity, col.id)
        assert refreshed is not None and refreshed.name == 'Orig' and refreshed.order == 1024.0
