"""Boards route tests: 200/201/400/401/403/404/409 for board, member and invite endpoints."""
import uuid

import pytest

from app.extensions import db
from app.models import BoardEntity, InviteLinkEntity, TeamMembershipEntity

GENERIC = 'Not found or access denied'


def _error(res, status, message=None):
    assert res.status_code == status
    body = res.get_json()
    assert set(body) == {'error'} and isinstance(body['error'], str) and body['error']
    if message is not None:
        assert body['error'] == message


# ---- boards --------------------------------------------------------------------------------

def test_create_board_returns_201_in_personal_team(client, world, auth):
    res = client.post('/api/boards', json={'name': '  Roadmap  '}, headers=auth(world.admin))
    assert res.status_code == 201
    data = res.get_json()['data']
    assert data['name'] == 'Roadmap' and data['team_id'] == str(world.team.id)
    assert set(data) == {'id', 'name', 'team_id', 'created_at'}


@pytest.mark.parametrize('body', [
    {}, {'name': ''}, {'name': '   '}, {'name': 'x' * 101}, {'name': 'ok', 'extra': 1},
    {'name': 'ok', 'team_id': 'not-a-uuid'},
])
def test_create_board_returns_400_for_invalid_body(client, world, auth, body):
    res = client.post('/api/boards', json=body, headers=auth(world.admin))
    assert res.status_code == 400 and isinstance(res.get_json()['error'], str)
    assert db.session.query(BoardEntity).count() == 2


def test_create_board_returns_401_without_token(client, world):
    _error(client.post('/api/boards', json={'name': 'x'}), 401)


def test_create_board_returns_403_for_member_unknown_and_foreign_team(client, world, auth):
    for team_id in (world.team.id, uuid.uuid4(), world.team_b.id):
        res = client.post('/api/boards', json={'name': 'x', 'team_id': str(team_id)},
                          headers=auth(world.member if team_id == world.team.id
                                       else world.admin))
        _error(res, 403, GENERIC)
    assert db.session.query(BoardEntity).count() == 2


def test_list_boards_returns_200_with_only_own_team_boards(client, world, auth):
    res = client.get('/api/boards', headers=auth(world.member))
    assert res.status_code == 200
    assert [b['id'] for b in res.get_json()['data']] == [str(world.board.id)]
    assert client.get('/api/boards', headers=auth(world.outsider)).get_json() == {'data': []}


def test_list_boards_returns_401_without_token(client, world):
    _error(client.get('/api/boards'), 401)


def test_get_board_returns_200_with_columns_and_cards(client, world, auth, factory):
    col = factory.column(world.board)
    factory.card(col, world.admin, assignee_id=world.member.id)
    factory.session.commit()
    res = client.get(f'/api/boards/{world.board.id}', headers=auth(world.member))
    assert res.status_code == 200
    data = res.get_json()['data']
    assert set(data) == {'id', 'name', 'team_id', 'created_at', 'columns'}
    card = data['columns'][0]['cards'][0]
    assert card['assignee']['id'] == str(world.member.id)
    assert set(data['columns'][0]) == {'id', 'name', 'order', 'is_done', 'cards'}


def test_get_board_returns_401_404_403_and_400(client, world, auth):
    _error(client.get(f'/api/boards/{world.board.id}'), 401)
    _error(client.get(f'/api/boards/{uuid.uuid4()}', headers=auth(world.member)), 404, GENERIC)
    _error(client.get(f'/api/boards/{world.board.id}', headers=auth(world.outsider)), 403, GENERIC)
    assert client.get('/api/boards/not-a-uuid', headers=auth(world.member)).status_code == 400


def test_update_board_returns_200_and_persists(client, world, auth):
    res = client.patch(f'/api/boards/{world.board.id}', json={'name': 'Renamed'},
                       headers=auth(world.admin))
    assert res.status_code == 200 and res.get_json()['data']['name'] == 'Renamed'
    assert db.session.get(BoardEntity, world.board.id).name == 'Renamed'


def test_update_board_returns_400_401_403_404(client, world, auth):
    url = f'/api/boards/{world.board.id}'
    assert client.patch(url, json={'name': 'x', 'team_id': str(world.team_b.id)},
                        headers=auth(world.admin)).status_code == 400
    assert client.patch(url, json={'name': ' '}, headers=auth(world.admin)).status_code == 400
    _error(client.patch(url, json={'name': 'x'}), 401)
    _error(client.patch(url, json={'name': 'x'}, headers=auth(world.member)), 403,
           'Admin access required')
    _error(client.patch(url, json={'name': 'x'}, headers=auth(world.outsider)), 403, GENERIC)
    _error(client.patch(f'/api/boards/{uuid.uuid4()}', json={'name': 'x'},
                        headers=auth(world.admin)), 404, GENERIC)
    assert db.session.get(BoardEntity, world.board.id).name != 'x'


def test_delete_board_returns_200_with_id(client, world, auth):
    res = client.delete(f'/api/boards/{world.board.id}', headers=auth(world.admin))
    assert res.status_code == 200 and res.get_json() == {'data': {'id': str(world.board.id)}}
    assert db.session.get(BoardEntity, world.board.id) is None


def test_delete_board_returns_401_403_404(client, world, auth):
    url = f'/api/boards/{world.board.id}'
    _error(client.delete(url), 401)
    _error(client.delete(url, headers=auth(world.member)), 403, 'Admin access required')
    _error(client.delete(url, headers=auth(world.admin_b)), 403, GENERIC)
    _error(client.delete(f'/api/boards/{uuid.uuid4()}', headers=auth(world.admin)), 404, GENERIC)
    assert db.session.get(BoardEntity, world.board.id) is not None


# ---- members -------------------------------------------------------------------------------

def _members(world):
    return f'/api/boards/{world.board.id}/members'


def test_add_member_returns_201(client, world, auth):
    res = client.post(_members(world), json={'email': world.outsider.email, 'role': 'admin'},
                      headers=auth(world.admin))
    assert res.status_code == 201
    assert res.get_json()['data'] == {
        'user_id': str(world.outsider.id), 'name': world.outsider.name,
        'username': world.outsider.username, 'role': 'admin'}


def test_add_member_returns_400_for_invalid_body(client, world, auth):
    for body in ({}, {'email': 'not-an-email'}, {'email': 'a@b.co', 'role': 'owner'},
                 {'email': 'a@b.co', 'x': 1}):
        assert client.post(_members(world), json=body,
                           headers=auth(world.admin)).status_code == 400


def test_add_member_returns_404_unknown_email_and_409_duplicate(client, world, auth):
    _error(client.post(_members(world), json={'email': 'ghost@example.com'},
                       headers=auth(world.admin)), 404, 'User not found')
    _error(client.post(_members(world), json={'email': world.member.email},
                       headers=auth(world.admin)), 409)


def test_add_member_returns_401_and_403(client, world, auth):
    _error(client.post(_members(world), json={'email': world.outsider.email}), 401)
    _error(client.post(_members(world), json={'email': world.outsider.email},
                       headers=auth(world.member)), 403, 'Admin access required')
    _error(client.post(_members(world), json={'email': world.outsider.email},
                       headers=auth(world.outsider)), 403, GENERIC)
    _error(client.post(f'/api/boards/{uuid.uuid4()}/members', json={'email': 'a@b.co'},
                       headers=auth(world.admin)), 404, GENERIC)


def test_list_members_returns_200_for_member_and_403_for_outsider(client, world, auth):
    res = client.get(_members(world), headers=auth(world.member))
    assert res.status_code == 200 and len(res.get_json()['data']) == 3
    _error(client.get(_members(world), headers=auth(world.outsider)), 403, GENERIC)
    _error(client.get(_members(world)), 401)


def test_update_member_role_returns_200_400_404_409(client, world, auth):
    url = f'{_members(world)}/{world.member.id}'
    res = client.patch(url, json={'role': 'admin'}, headers=auth(world.admin))
    assert res.status_code == 200 and res.get_json()['data']['role'] == 'admin'
    assert client.patch(url, json={'role': 'owner'}, headers=auth(world.admin)).status_code == 400
    assert client.patch(url, json={}, headers=auth(world.admin)).status_code == 400
    _error(client.patch(f'{_members(world)}/{world.outsider.id}', json={'role': 'member'},
                        headers=auth(world.admin)), 404, 'Member not found')
    solo = f'/api/boards/{world.board_b.id}/members/{world.admin_b.id}'
    _error(client.patch(solo, json={'role': 'member'}, headers=auth(world.admin_b)), 409)


def test_update_member_role_returns_401_and_403(client, world, auth):
    url = f'{_members(world)}/{world.other_member.id}'
    _error(client.patch(url, json={'role': 'admin'}), 401)
    _error(client.patch(url, json={'role': 'admin'}, headers=auth(world.member)), 403)
    row = db.session.query(TeamMembershipEntity).filter_by(user_id=world.other_member.id).one()
    assert row.role == 'member'


def test_remove_member_returns_200_with_id_and_409_for_last_admin(client, world, auth):
    res = client.delete(f'{_members(world)}/{world.member.id}', headers=auth(world.admin))
    assert res.status_code == 200 and res.get_json() == {'data': {'id': str(world.member.id)}}
    _error(client.delete(f'{_members(world)}/{world.admin.id}', headers=auth(world.admin)), 409)
    _error(client.delete(f'{_members(world)}/{world.outsider.id}', headers=auth(world.admin)),
           404, 'Member not found')


def test_remove_member_returns_401_and_403(client, world, auth):
    url = f'{_members(world)}/{world.other_member.id}'
    _error(client.delete(url), 401)
    _error(client.delete(url, headers=auth(world.member)), 403, 'Admin access required')
    _error(client.delete(url, headers=auth(world.outsider)), 403, GENERIC)


# ---- invite links --------------------------------------------------------------------------

def _links(world):
    return f'/api/boards/{world.board.id}/invite-links'


def test_create_invite_link_returns_201_and_token_once(client, world, auth):
    for kwargs in ({}, {'json': {}}):
        res = client.post(_links(world), headers=auth(world.admin), **kwargs)
        assert res.status_code == 201
        data = res.get_json()['data']
        assert set(data) == {'id', 'board_id', 'token', 'created_at'}
        assert data['board_id'] == str(world.board.id)
    assert db.session.query(InviteLinkEntity).count() == 2


def test_create_invite_link_returns_400_401_403_404(client, world, auth):
    assert client.post(_links(world), json={'x': 1}, headers=auth(world.admin)).status_code == 400
    _error(client.post(_links(world)), 401)
    _error(client.post(_links(world), headers=auth(world.member)), 403, 'Admin access required')
    _error(client.post(_links(world), headers=auth(world.outsider)), 403, GENERIC)
    _error(client.post(f'/api/boards/{uuid.uuid4()}/invite-links', headers=auth(world.admin)),
           404, GENERIC)
    assert db.session.query(InviteLinkEntity).count() == 0


def test_revoke_invite_link_returns_200_then_404_not_found_for_guest_read(client, world, auth):
    created = client.post(_links(world), headers=auth(world.admin)).get_json()['data']
    guest = {'X-Invite-Token': created['token']}
    assert client.get(f'/api/boards/{world.board.id}', headers=guest).status_code == 200
    res = client.delete(f'{_links(world)}/{created["id"]}', headers=auth(world.admin))
    assert res.status_code == 200 and res.get_json() == {'data': {'id': created['id']}}
    _error(client.get(f'/api/boards/{world.board.id}', headers=guest), 404, 'Not found')
    assert db.session.get(InviteLinkEntity, uuid.UUID(created['id'])).revoked_at is not None


def test_revoke_invite_link_returns_401_403_404(client, world, auth):
    created = client.post(_links(world), headers=auth(world.admin)).get_json()['data']
    url = f'{_links(world)}/{created["id"]}'
    _error(client.delete(url), 401)
    _error(client.delete(url, headers=auth(world.member)), 403, 'Admin access required')
    _error(client.delete(f'{_links(world)}/{uuid.uuid4()}', headers=auth(world.member)),
           404, 'Not found')
    _error(client.delete(f'/api/boards/{world.board_b.id}/invite-links/{created["id"]}',
                         headers=auth(world.admin_b)), 404, 'Not found')
