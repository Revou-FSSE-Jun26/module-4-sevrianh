"""Auth route tests (R13.1 to R13.7, R13.11)."""
import pytest

from app.models import TeamEntity, TeamMembershipEntity, UserEntity

PAYLOAD = {'name': 'Ann', 'username': 'Ann_1', 'email': 'ann@example.com',
           'password': 'password123'}


def _register(client, **overrides):
    return client.post('/api/auth/register', json={**PAYLOAD, **overrides})


def _no_password_keys(value) -> bool:
    if isinstance(value, dict):
        return all(not k.startswith('password') and _no_password_keys(v)
                   for k, v in value.items())
    if isinstance(value, list):
        return all(_no_password_keys(v) for v in value)
    return True


def test_register_returns_201_with_safe_payload(client, db_session):
    res = _register(client)
    assert res.status_code == 201
    data = res.get_json()['data']
    assert set(data) == {'id', 'name', 'username', 'email', 'created_at'}
    assert data['username'] == 'ann_1'
    assert db_session.query(TeamMembershipEntity).filter_by(role='admin').count() == 1
    assert db_session.query(TeamEntity).filter_by(is_personal=True).count() == 1


@pytest.mark.parametrize('overrides', [
    {'name': ''}, {'username': 'ab'}, {'username': 'bad name!'}, {'email': 'not-an-email'},
    {'password': 'short'},
])
def test_register_returns_400_for_invalid_field(client, db_session, overrides):
    res = _register(client, **overrides)
    assert res.status_code == 400
    assert isinstance(res.get_json()['error'], str) and res.get_json()['error']
    assert db_session.query(UserEntity).count() == 0


def test_register_returns_400_for_missing_field(client):
    body = {k: v for k, v in PAYLOAD.items() if k != 'email'}
    assert client.post('/api/auth/register', json=body).status_code == 400


def test_register_returns_400_for_unknown_field(client):
    assert _register(client, role='admin').status_code == 400


def test_register_returns_400_for_missing_body(client):
    assert client.post('/api/auth/register').status_code == 400


def test_register_returns_409_for_duplicate_email_any_case(client):
    assert _register(client).status_code == 201
    res = _register(client, username='other', email='ANN@EXAMPLE.COM')
    assert res.status_code == 409
    assert res.get_json() == {'error': 'Email already registered'}


def test_register_returns_409_for_duplicate_username_any_case(client):
    assert _register(client).status_code == 201
    res = _register(client, username='ANN_1', email='other@example.com')
    assert res.status_code == 409
    assert res.get_json() == {'error': 'Username already taken'}


def test_login_returns_200_with_token_payload(client):
    _register(client)
    res = client.post('/api/auth/login',
                      json={'email': 'ann@example.com', 'password': PAYLOAD['password']})
    assert res.status_code == 200
    data = res.get_json()['data']
    assert set(data) == {'access_token', 'token_type', 'expires_in', 'user'}
    assert data['token_type'] == 'Bearer' and data['expires_in'] == 3600
    assert set(data['user']) == {'id', 'name', 'username', 'email', 'created_at'}


def test_login_token_expires_after_3600_seconds(client, app):
    from flask_jwt_extended import decode_token
    _register(client)
    res = client.post('/api/auth/login',
                      json={'email': 'ann@example.com', 'password': PAYLOAD['password']})
    claims = decode_token(res.get_json()['data']['access_token'])
    assert claims['exp'] - claims['iat'] == 3600


def test_login_returns_identical_401_for_unknown_email_and_wrong_password(client):
    _register(client)
    wrong = client.post('/api/auth/login',
                        json={'email': 'ann@example.com', 'password': 'wrong-password'})
    unknown = client.post('/api/auth/login',
                          json={'email': 'nobody@example.com', 'password': 'password123'})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.get_json() == unknown.get_json() == {'error': 'Invalid credentials'}


def test_login_returns_400_for_unknown_field_and_missing_password(client):
    assert client.post('/api/auth/login', json={
        'email': 'ann@example.com', 'password': 'x', 'extra': 1}).status_code == 400
    assert client.post('/api/auth/login',
                       json={'email': 'ann@example.com'}).status_code == 400


def test_no_response_contains_password_keys(client):
    responses = [
        _register(client),
        _register(client),
        _register(client, username='x'),
        client.post('/api/auth/login',
                    json={'email': 'ann@example.com', 'password': PAYLOAD['password']}),
        client.post('/api/auth/login', json={'email': 'ann@example.com', 'password': 'nope'}),
    ]
    for res in responses:
        assert _no_password_keys(res.get_json())
        assert 'password_hash' not in res.get_data(as_text=True)
