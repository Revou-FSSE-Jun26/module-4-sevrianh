"""Users route tests: GET/PATCH /api/users/me (R19.1 to R19.6)."""
import pytest

from app.utils.auth import issue_access_token

SAFE_KEYS = {'id', 'name', 'username', 'email', 'created_at'}


def _headers(app, user):
    with app.app_context():
        return {'Authorization': f'Bearer {issue_access_token(str(user.id))}'}


@pytest.fixture()
def me(factory):
    user = factory.user(name='Alice', email='alice@example.com')
    factory.session.commit()
    return user


def test_get_me_returns_200_with_exactly_safe_fields(app, client, me):
    response = client.get('/api/users/me', headers=_headers(app, me))
    assert response.status_code == 200
    data = response.get_json()['data']
    assert set(data) == SAFE_KEYS
    assert data['email'] == 'alice@example.com'


def test_get_me_without_token_returns_401(client):
    response = client.get('/api/users/me')
    assert response.status_code == 401
    assert response.get_json()['error']


def test_patch_me_without_token_returns_401(client):
    assert client.patch('/api/users/me', json={'name': 'X'}).status_code == 401


def test_patch_me_updates_name_and_email_returns_200(app, client, me):
    response = client.patch('/api/users/me', headers=_headers(app, me),
                            json={'name': '  Alicia  ', 'email': 'alicia@example.com'})
    assert response.status_code == 200
    data = response.get_json()['data']
    assert set(data) == SAFE_KEYS
    assert (data['name'], data['email']) == ('Alicia', 'alicia@example.com')
    again = client.get('/api/users/me', headers=_headers(app, me)).get_json()['data']
    assert again['name'] == 'Alicia'


@pytest.mark.parametrize('body', [
    None, {},
    {'password': 'x'}, {'password_hash': 'x'}, {'username': 'other'},
    {'name': 'Ok', 'role': 'admin'},
    {'email': 'not-an-email'}, {'email': 'a' * 250 + '@example.com'},
    {'name': ''}, {'name': '   '}, {'name': 'n' * 101},
])
def test_patch_me_invalid_body_returns_400_and_keeps_data(app, client, me, body):
    response = client.patch('/api/users/me', headers=_headers(app, me), json=body)
    assert response.status_code == 400
    assert isinstance(response.get_json()['error'], str)
    data = client.get('/api/users/me', headers=_headers(app, me)).get_json()['data']
    assert (data['name'], data['email'], data['username']) == (
        'Alice', 'alice@example.com', me.username)


def test_patch_me_duplicate_email_returns_409(app, client, me, factory):
    factory.user(email='bob@example.com')
    factory.session.commit()
    response = client.patch('/api/users/me', headers=_headers(app, me),
                            json={'email': 'BOB@example.com'})
    assert response.status_code == 409
    assert response.get_json()['error']


def test_responses_contain_no_password_data(app, client, me):
    body = client.get('/api/users/me', headers=_headers(app, me)).get_data(as_text=True)
    assert 'password' not in body
