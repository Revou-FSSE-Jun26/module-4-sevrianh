"""Table-driven tests for every Access Resolution Table step of BE-08 (T-11).

A test-only Flask app registers one `@token_required` route and two Guest read routes
(Board and Card). The real routes arrive in later tasks.
"""
import secrets
import uuid
from datetime import timedelta

import pytest
from flask import Blueprint
from flask_jwt_extended import create_access_token

from app import create_app
from app.models import InviteLinkEntity
from app.utils.auth import (
    INVITE_TOKEN_HEADER, board_access_required, hash_invite_token, token_required,
)
from app.utils.responses import success
from app.utils.time import utc_now

GENERIC = 'Not found or access denied'
AUTH = 'Authentication required'


@pytest.fixture(scope='module')
def guard_app():
    """Fresh app (routes cannot be added to the session app after its first request)."""
    flask_app = create_app()
    flask_app.config.update(TESTING=True)
    bp = Blueprint('guard_test', __name__, url_prefix='/api/_t')

    @bp.route('/protected', methods=['GET'])
    @token_required
    def protected_route(current_user):
        return success({'user_id': str(current_user.id)})

    @bp.route('/boards/<board_id>', methods=['GET'])
    @board_access_required(allow_guest_read=True)
    def board_route(access, board_id):
        return success({'role': access.role, 'has_user': access.user is not None})

    @bp.route('/cards/<card_id>/comments', methods=['GET'])
    @board_access_required(allow_guest_read=True)
    def card_comments_route(access, card_id):
        return success({'role': access.role})

    @bp.route('/boards/<board_id>', methods=['POST'])
    @board_access_required()
    def board_write_route(access, board_id):
        return success({'role': access.role})

    flask_app.register_blueprint(bp)
    return flask_app


@pytest.fixture()
def http(guard_app, db_session):
    return guard_app.test_client()


@pytest.fixture()
def world(factory, db_session):
    """Two Teams, their Boards and Cards, memberships, and invite links (committed)."""
    admin, member, outsider = factory.user(), factory.user(), factory.user()
    team = factory.team(owner=admin)
    factory.membership(team, admin, 'admin')
    factory.membership(team, member, 'member')
    board_a = factory.board(team)
    board_b = factory.board(factory.team())
    column_a = factory.column(board_a)
    card_a = factory.card(column_a, created_by=admin, order=1024.0)
    deleted_card = factory.card(column_a, created_by=admin, order=2048.0, deleted_at=utc_now())
    deleted_board = factory.board(team, deleted_at=utc_now())

    def link(board, revoked=False):
        raw = secrets.token_urlsafe(32)
        factory.session.add(InviteLinkEntity(
            board_id=board.id, created_by_id=admin.id, token_hash=hash_invite_token(raw),
            revoked_at=utc_now() if revoked else None))
        return raw

    data = {
        'admin': admin, 'member': member, 'outsider': outsider, 'board_a': board_a,
        'board_b': board_b, 'card_a': card_a, 'deleted_card': deleted_card,
        'deleted_board': deleted_board,
        'token_a': link(board_a), 'token_b': link(board_b),
        'token_revoked': link(board_a, revoked=True),
    }
    db_session.commit()
    return data


def _jwt(guard_app, user, **kw):
    with guard_app.app_context():
        return create_access_token(identity=str(user.id), **kw)


def _headers(guard_app, w, jwt='none', token=None):
    """jwt: none | member | admin | outsider | expired | malformed | ghost."""
    headers = {}
    if jwt in ('member', 'admin', 'outsider'):
        headers['Authorization'] = f'Bearer {_jwt(guard_app, w[jwt])}'
    elif jwt == 'expired':
        headers['Authorization'] = 'Bearer ' + _jwt(
            guard_app, w['member'], expires_delta=timedelta(seconds=-30))
    elif jwt == 'malformed':
        headers['Authorization'] = 'Bearer not.a.jwt'
    elif jwt == 'ghost':
        with guard_app.app_context():
            headers['Authorization'] = 'Bearer ' + create_access_token(identity=str(uuid.uuid4()))
    if token is not None:
        headers[INVITE_TOKEN_HEADER] = w[token] if token in w else token
    return headers


# (id, jwt state, invite token, expected status, expected error, expected role)
GUEST_TABLE = [
    ('step1-expired-jwt-valid-token', 'expired', 'token_a', 401, AUTH, None),
    ('step1-malformed-jwt-valid-token', 'malformed', 'token_a', 401, AUTH, None),
    ('step1-deleted-user-jwt-valid-token', 'ghost', 'token_a', 401, AUTH, None),
    ('step1-expired-jwt-no-token', 'expired', None, 401, AUTH, None),
    ('step2-no-jwt-no-token', 'none', None, 401, AUTH, None),
    ('step4-member-no-token', 'member', None, 200, None, 'member'),
    ('step4-admin-no-token', 'admin', None, 200, None, 'admin'),
    ('step4-member-invalid-token', 'member', 'garbage', 200, None, 'member'),
    ('step4-member-empty-token', 'member', '', 200, None, 'member'),
    ('step4-member-foreign-token', 'member', 'token_b', 200, None, 'member'),
    ('step4-member-revoked-token', 'member', 'token_revoked', 200, None, 'member'),
    ('step5-outsider-no-token', 'outsider', None, 403, GENERIC, None),
    ('step6-invalid-token', 'none', 'garbage', 404, 'Not found', None),
    ('step6-revoked-token', 'none', 'token_revoked', 404, 'Not found', None),
    ('step6-empty-token', 'none', '', 404, 'Not found', None),
    ('step6-outsider-invalid-token', 'outsider', 'garbage', 404, 'Not found', None),
    ('step6-outsider-empty-token', 'outsider', '', 404, 'Not found', None),
    ('step7-guest-token', 'none', 'token_a', 200, None, 'guest'),
    ('step7-outsider-valid-token', 'outsider', 'token_a', 200, None, 'guest'),
    ('step8-token-of-other-board', 'none', 'token_b', 403, GENERIC, None),
    ('step8-outsider-token-of-other-board', 'outsider', 'token_b', 403, GENERIC, None),
]


def _check(resp, status, message, role):
    body = resp.get_json()
    assert resp.status_code == status
    if status == 200:
        assert 'error' not in body and body['data']['role'] == role
    else:
        assert body == {'error': message}


@pytest.mark.parametrize(
    'jwt,token,status,message,role', [c[1:] for c in GUEST_TABLE], ids=[c[0] for c in GUEST_TABLE])
def test_board_guest_route_follows_access_table(http, guard_app, world, jwt, token, status,
                                                message, role):
    resp = http.get(f'/api/_t/boards/{world["board_a"].id}',
                    headers=_headers(guard_app, world, jwt, token))
    _check(resp, status, message, role)


@pytest.mark.parametrize(
    'jwt,token,status,message,role', [c[1:] for c in GUEST_TABLE], ids=[c[0] for c in GUEST_TABLE])
def test_card_guest_route_resolves_through_card_board(http, guard_app, world, jwt, token, status,
                                                      message, role):
    resp = http.get(f'/api/_t/cards/{world["card_a"].id}/comments',
                    headers=_headers(guard_app, world, jwt, token))
    _check(resp, status, message, role)


def test_guest_gets_no_user_object(http, guard_app, world):
    resp = http.get(f'/api/_t/boards/{world["board_a"].id}',
                    headers=_headers(guard_app, world, 'none', 'token_a'))
    assert resp.get_json()['data'] == {'role': 'guest', 'has_user': False}


@pytest.mark.parametrize('jwt,token', [
    ('none', None), ('none', 'token_a'), ('member', None), ('outsider', 'token_a'),
    ('expired', 'token_a'), ('none', 'garbage'),
], ids=['no-auth', 'guest-token', 'member', 'outsider-token', 'expired', 'bad-token'])
@pytest.mark.parametrize('target', ['missing-board', 'deleted-board', 'missing-card',
                                    'deleted-card'])
def test_missing_resources_are_404_generic_for_authenticated_requests(
        http, guard_app, world, target, jwt, token):
    urls = {
        'missing-board': f'/api/_t/boards/{uuid.uuid4()}',
        'deleted-board': f'/api/_t/boards/{world["deleted_board"].id}',
        'missing-card': f'/api/_t/cards/{uuid.uuid4()}/comments',
        'deleted-card': f'/api/_t/cards/{world["deleted_card"].id}/comments',
    }
    resp = http.get(urls[target], headers=_headers(guard_app, world, jwt, token))
    if jwt == 'expired':
        assert resp.status_code == 401  # step 1 precedes step 3
    elif jwt == 'none' and token is None:
        assert resp.status_code == 401  # step 2 precedes step 3
    else:
        assert resp.status_code == 404
        assert resp.get_json() == {'error': GENERIC}


def test_invalid_path_uuid_is_400_after_authentication(http, guard_app, world):
    resp = http.get('/api/_t/boards/not-a-uuid', headers=_headers(guard_app, world, 'member'))
    assert resp.status_code == 400
    assert resp.get_json() == {'error': 'board_id: Not a valid UUID.'}
    unauth = http.get('/api/_t/boards/not-a-uuid')
    assert unauth.status_code == 401


def test_guest_cannot_reach_write_route_guarded_without_guest_read(http, guard_app, world):
    url = f'/api/_t/boards/{world["board_a"].id}'
    guest = http.post(url, headers=_headers(guard_app, world, 'none', 'token_a'))
    assert guest.status_code == 403 and guest.get_json() == {'error': GENERIC}
    outsider_guest = http.post(url, headers=_headers(guard_app, world, 'outsider', 'token_a'))
    assert outsider_guest.status_code == 403
    anonymous = http.post(url)
    assert anonymous.status_code == 401
    member = http.post(url, headers=_headers(guard_app, world, 'member', 'garbage'))
    assert member.status_code == 200 and member.get_json()['data']['role'] == 'member'


# ---- @token_required: the invite token is ignored, JWT failures are always 401 ----

@pytest.mark.parametrize('jwt,token', [
    ('none', None), ('none', 'token_a'), ('none', 'garbage'), ('none', ''),
    ('malformed', None), ('malformed', 'token_a'), ('expired', None), ('expired', 'token_a'),
    ('ghost', None),
], ids=['missing', 'token-only', 'invalid-token-only', 'empty-token-only', 'malformed',
        'malformed-with-token', 'expired', 'expired-with-token', 'deleted-user'])
def test_token_required_rejects_with_401_never_422(http, guard_app, world, jwt, token):
    resp = http.get('/api/_t/protected', headers=_headers(guard_app, world, jwt, token))
    assert resp.status_code == 401
    assert resp.get_json() == {'error': 'Authentication required'}


def test_token_required_passes_current_user_and_ignores_invite_token(http, guard_app, world):
    for token in (None, 'token_a', 'garbage'):
        resp = http.get('/api/_t/protected', headers=_headers(guard_app, world, 'member', token))
        assert resp.status_code == 200
        assert resp.get_json()['data']['user_id'] == str(world['member'].id)


def test_token_required_rejects_wrong_scheme_and_blank_bearer(http, world):
    for value in ('Basic abc', 'Bearer ', 'Bearer'):
        resp = http.get('/api/_t/protected', headers={'Authorization': value})
        assert resp.status_code == 401


def test_soft_deleted_user_jwt_is_401(http, guard_app, world, db_session):
    world['member'].deleted_at = utc_now()
    db_session.commit()
    resp = http.get('/api/_t/protected', headers=_headers(guard_app, world, 'member'))
    assert resp.status_code == 401


def test_hash_invite_token_is_sha256_hex():
    digest = hash_invite_token('abc')
    assert len(digest) == 64
    assert digest == ('ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')


def test_revoking_a_link_changes_access_from_200_to_404(http, guard_app, world, db_session):
    url = f'/api/_t/boards/{world["board_a"].id}'
    headers = _headers(guard_app, world, 'none', 'token_a')
    assert http.get(url, headers=headers).status_code == 200
    link = db_session.query(InviteLinkEntity).filter_by(
        token_hash=hash_invite_token(world['token_a'])).one()
    link.revoked_at = utc_now()
    db_session.commit()
    assert http.get(url, headers=headers).status_code == 404
