"""Table-driven permission tests for the boards cells of the Requirement 2 table (`-k permission`).

Roles: admin, member, guest (valid Invite Link token, no JWT) and non-member (JWT of a user
outside the Team). Cells that belong to Columns, Cards, Comments and analytics are covered by the
tests of those blueprints. A Guest request without a JWT is answered 401 (R2.2, R3.14).
"""
import uuid

import pytest

from app.extensions import db
from app.models import BoardEntity, InviteLinkEntity, TeamMembershipEntity
from app.utils.auth import issue_access_token

ACTIONS = {
    'view_board': ('get', '/api/boards/{board}', None),
    'create_board': ('post', '/api/boards', {'name': 'Matrix board'}),
    'rename_board': ('patch', '/api/boards/{board}', {'name': 'Renamed'}),
    'delete_board': ('delete', '/api/boards/{board}', None),
    'add_member': ('post', '/api/boards/{board}/members', {'email': 'outsider@example.com'}),
    'list_members': ('get', '/api/boards/{board}/members', None),
    'change_role': ('patch', '/api/boards/{board}/members/{other}', {'role': 'admin'}),
    'remove_member': ('delete', '/api/boards/{board}/members/{other}', None),
    'create_link': ('post', '/api/boards/{board}/invite-links', None),
    'revoke_link': ('delete', '/api/boards/{board}/invite-links/{link}', None),
}

# (action, role) -> expected status
MATRIX = {
    ('view_board', 'admin'): 200, ('view_board', 'member'): 200,
    ('view_board', 'guest'): 200, ('view_board', 'non_member'): 403,
    ('create_board', 'admin'): 201, ('create_board', 'member'): 403,
    ('create_board', 'non_member'): 403,
    ('rename_board', 'admin'): 200, ('rename_board', 'member'): 403,
    ('rename_board', 'guest'): 401, ('rename_board', 'non_member'): 403,
    ('delete_board', 'admin'): 200, ('delete_board', 'member'): 403,
    ('delete_board', 'guest'): 401, ('delete_board', 'non_member'): 403,
    ('add_member', 'admin'): 201, ('add_member', 'member'): 403,
    ('add_member', 'guest'): 401, ('add_member', 'non_member'): 403,
    ('list_members', 'admin'): 200, ('list_members', 'member'): 200,
    ('list_members', 'guest'): 401, ('list_members', 'non_member'): 403,
    ('change_role', 'admin'): 200, ('change_role', 'member'): 403,
    ('change_role', 'guest'): 401, ('change_role', 'non_member'): 403,
    ('remove_member', 'admin'): 200, ('remove_member', 'member'): 403,
    ('remove_member', 'guest'): 401, ('remove_member', 'non_member'): 403,
    ('create_link', 'admin'): 201, ('create_link', 'member'): 403,
    ('create_link', 'guest'): 401, ('create_link', 'non_member'): 403,
    ('revoke_link', 'admin'): 200, ('revoke_link', 'member'): 403,
    ('revoke_link', 'guest'): 401, ('revoke_link', 'non_member'): 403,
}


@pytest.fixture()
def matrix_env(client, world, auth):
    """Return `call(action, role)`; the Invite Link exists before the request."""
    created = client.post(f'/api/boards/{world.board.id}/invite-links',
                          headers=auth(world.admin)).get_json()['data']
    ids = {'board': world.board.id, 'other': world.other_member.id, 'link': created['id']}
    headers = {
        'admin': auth(world.admin), 'member': auth(world.member),
        'non_member': auth(world.outsider), 'guest': {'X-Invite-Token': created['token']},
    }

    def call(action, role):
        method, path, body = ACTIONS[action]
        kwargs = {'headers': headers[role]}
        if body is not None:
            kwargs['json'] = body
        return getattr(client, method)(path.format(**ids), **kwargs)

    return call


@pytest.mark.parametrize('action,role', sorted(MATRIX))
def test_permission_matrix_cell(matrix_env, action, role):
    assert matrix_env(action, role).status_code == MATRIX[(action, role)]


def _snapshot():
    db.session.expire_all()
    return (
        sorted((str(b.id), b.name) for b in db.session.query(BoardEntity).all()),
        sorted((str(m.user_id), m.role) for m in db.session.query(TeamMembershipEntity).all()),
        sorted((str(k.id), k.revoked_at) for k in db.session.query(InviteLinkEntity).all()),
    )


@pytest.mark.parametrize('action,role', sorted(
    (a, r) for (a, r), status in MATRIX.items() if status in (401, 403)))
def test_permission_denied_requests_change_no_data(matrix_env, action, role):
    before = _snapshot()
    assert matrix_env(action, role).status_code in (401, 403)
    assert _snapshot() == before


@pytest.mark.parametrize('action', sorted(a for a in ACTIONS if a not in ('create_board',)))
def test_permission_cross_team_admin_is_denied_with_generic_body(
        client, world, auth, matrix_env, action):
    method, path, body = ACTIONS[action]
    created = db.session.query(InviteLinkEntity).one()
    url = path.format(board=world.board.id, other=world.other_member.id, link=created.id)
    kwargs = {'headers': auth(world.admin_b)}
    if body is not None:
        kwargs['json'] = body
    res = getattr(client, method)(url, **kwargs)
    if action == 'revoke_link':
        assert res.status_code == 403 and res.get_json() == {'error': 'Not found or access denied'}
    else:
        assert res.status_code == 403
        assert res.get_json() == {'error': 'Not found or access denied'}


@pytest.mark.parametrize('action', sorted(a for a in ACTIONS if a != 'create_board'))
@pytest.mark.parametrize('role', ['admin', 'member', 'non_member'])
def test_permission_missing_board_is_404_before_403(client, world, auth, action, role):
    method, path, body = ACTIONS[action]
    user = {'admin': world.admin, 'member': world.member, 'non_member': world.outsider}[role]
    missing = uuid.uuid4()
    url = path.format(board=missing, other=world.other_member.id, link=uuid.uuid4())
    kwargs = {'headers': auth(user)}
    if body is not None:
        kwargs['json'] = body
    res = getattr(client, method)(url, **kwargs)
    if action == 'revoke_link':
        # revoke checks the Board, then the link, both before the Admin check
        assert res.status_code == 404
    else:
        assert res.status_code == 404
        assert res.get_json() == {'error': 'Not found or access denied'}


@pytest.mark.parametrize('role', ['member', 'non_member'])
@pytest.mark.parametrize('email', ['ghost@example.com', 'member@example.com', 'bad-email'])
def test_permission_member_management_is_403_before_email_lookup(
        client, world, auth, role, email):
    user = world.member if role == 'member' else world.outsider
    res = client.post(f'/api/boards/{world.board.id}/members', json={'email': email},
                      headers=auth(user))
    assert res.status_code == 403 or (email == 'bad-email' and res.status_code == 400)
    if email != 'bad-email':
        assert res.get_json()['error'] != 'User not found'


def test_permission_member_role_change_is_403_before_role_evaluation(client, world, auth):
    res = client.patch(f'/api/boards/{world.board.id}/members/{world.admin.id}',
                       json={'role': 'member'}, headers=auth(world.member))
    assert res.status_code == 403  # not 409 last-admin


def test_permission_link_of_board_a_gives_nothing_on_board_b(client, world, auth):
    token = client.post(f'/api/boards/{world.board.id}/invite-links',
                        headers=auth(world.admin)).get_json()['data']['token']
    guest = {'X-Invite-Token': token}
    assert client.get(f'/api/boards/{world.board.id}', headers=guest).status_code == 200
    res = client.get(f'/api/boards/{world.board_b.id}', headers=guest)
    assert res.status_code == 403 and res.get_json() == {'error': 'Not found or access denied'}


def test_permission_revoked_link_read_is_404(client, world, auth):
    created = client.post(f'/api/boards/{world.board.id}/invite-links',
                          headers=auth(world.admin)).get_json()['data']
    client.delete(f'/api/boards/{world.board.id}/invite-links/{created["id"]}',
                  headers=auth(world.admin))
    res = client.get(f'/api/boards/{world.board.id}',
                     headers={'X-Invite-Token': created['token']})
    assert res.status_code == 404 and res.get_json() == {'error': 'Not found'}


def test_permission_member_jwt_ignores_invalid_invite_token(client, world, auth):
    headers = {**auth(world.member), 'X-Invite-Token': 'garbage'}
    assert client.get(f'/api/boards/{world.board.id}', headers=headers).status_code == 200


def test_permission_guest_with_non_member_jwt_cannot_write(client, world, auth):
    token = client.post(f'/api/boards/{world.board.id}/invite-links',
                        headers=auth(world.admin)).get_json()['data']['token']
    headers = {**auth(world.outsider), 'X-Invite-Token': token}
    before = _snapshot()
    for method, path, body in (
            ('patch', f'/api/boards/{world.board.id}', {'name': 'x'}),
            ('delete', f'/api/boards/{world.board.id}', None),
            ('post', f'/api/boards/{world.board.id}/members', {'email': 'a@b.co'})):
        kwargs = {'json': body} if body is not None else {}
        assert getattr(client, method)(path, headers=headers, **kwargs).status_code == 403
    assert _snapshot() == before
    assert client.get(f'/api/boards/{world.board.id}', headers=headers).status_code == 200


def test_permission_invalid_jwt_with_valid_invite_token_is_401(client, world, auth, app):
    token = client.post(f'/api/boards/{world.board.id}/invite-links',
                        headers=auth(world.admin)).get_json()['data']['token']
    res = client.get(f'/api/boards/{world.board.id}',
                     headers={'Authorization': 'Bearer garbage', 'X-Invite-Token': token})
    assert res.status_code == 401
    with app.app_context():
        assert issue_access_token(str(world.admin.id))  # token issuance still works
