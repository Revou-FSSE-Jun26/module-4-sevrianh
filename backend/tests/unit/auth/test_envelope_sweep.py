"""401 sweep, response envelope, and unknown-field tests (T-50)."""
import uuid

import pytest

from app.utils.auth import issue_access_token
from tests.unit.auth.test_route_inventory import ROUTES

PUBLIC_OR_GUEST_ROUTES = {
    ('POST', '/api/auth/register'),
    ('POST', '/api/auth/login'),
    ('GET', '/api/health'),
    ('GET', '/api/boards/<board_id>'),
    ('GET', '/api/cards/<card_id>/comments'),
}

PROTECTED_ROUTES = sorted(ROUTES - PUBLIC_OR_GUEST_ROUTES)


def _fill_path(rule: str) -> str:
    uid = str(uuid.uuid4())
    params = (
        '<board_id>', '<column_id>', '<card_id>', '<comment_id>',
        '<notification_id>', '<user_id>', '<invite_id>',
    )
    for param in params:
        rule = rule.replace(param, uid)
    return rule


def _assert_error_envelope(resp, expected_status: int) -> None:
    assert resp.status_code == expected_status
    body = resp.get_json()
    assert set(body.keys()) == {'error'}
    assert isinstance(body['error'], str) and body['error']


@pytest.mark.parametrize('method,rule', PROTECTED_ROUTES)
def test_protected_routes_require_authentication(client, method, rule):
    resp = client.open(_fill_path(rule), method=method)
    _assert_error_envelope(resp, 401)


def test_envelope_shapes_across_statuses(client, factory):
    admin = factory.user()
    other = factory.user()
    team = factory.team(owner=admin)
    factory.membership(team=team, user=admin, role='admin')
    board = factory.board(team=team)
    headers = {'Authorization': f'Bearer {issue_access_token(str(admin.id))}'}
    other_headers = {'Authorization': f'Bearer {issue_access_token(str(other.id))}'}

    # 200 success
    ok_resp = client.get('/api/boards', headers=headers)
    assert ok_resp.status_code == 200
    assert set(ok_resp.get_json().keys()) == {'data'}

    # 400 validation / unknown field
    bad_resp = client.post('/api/boards', json={'name': 'Valid', 'extra_field': 1}, headers=headers)
    _assert_error_envelope(bad_resp, 400)

    # 401 unauthenticated
    unauth_resp = client.get('/api/boards')
    _assert_error_envelope(unauth_resp, 401)

    # 403 forbidden (non-member)
    forbid_resp = client.get(f'/api/boards/{board.id}', headers=other_headers)
    _assert_error_envelope(forbid_resp, 403)

    # 404 not found
    missing_resp = client.get(f'/api/boards/{uuid.uuid4()}', headers=headers)
    _assert_error_envelope(missing_resp, 404)

    # 405 method not allowed
    method_resp = client.put('/api/health')
    _assert_error_envelope(method_resp, 405)
