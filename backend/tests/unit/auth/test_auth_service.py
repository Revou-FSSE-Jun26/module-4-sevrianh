"""Auth service tests (R13.1 to R13.7, R13.10, R13.11, R28.1)."""
import pytest
from flask_jwt_extended import decode_token
from werkzeug.security import check_password_hash

from app.blueprints.auth import service
from app.blueprints.auth.service import login_service, register_service
from app.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    UsernameAlreadyTakenError,
)
from app.models import TeamEntity, TeamMembershipEntity, UserEntity

DATA = {'name': 'Ann', 'username': 'ann_1', 'email': 'ann@example.com', 'password': 'password123'}


def _counts(session):
    return (
        session.query(UserEntity).count(),
        session.query(TeamEntity).count(),
        session.query(TeamMembershipEntity).count(),
    )


def test_register_service_creates_user_personal_team_and_admin_membership(db_session):
    user = register_service(dict(DATA))
    team = db_session.query(TeamEntity).one()
    membership = db_session.query(TeamMembershipEntity).one()
    assert team.is_personal is True and team.owner_id == user.id
    assert membership.team_id == team.id and membership.user_id == user.id
    assert membership.role == 'admin'


def test_register_service_stores_hash_not_password(db_session):
    user = register_service(dict(DATA))
    assert user.password_hash != DATA['password']
    assert check_password_hash(user.password_hash, DATA['password'])


def test_register_service_rejects_duplicate_email_case_insensitively(db_session):
    register_service(dict(DATA))
    with pytest.raises(EmailAlreadyRegisteredError):
        register_service({**DATA, 'username': 'other', 'email': 'ANN@Example.com'})
    assert _counts(db_session) == (1, 1, 1)


def test_register_service_rejects_duplicate_username_case_insensitively(db_session):
    register_service(dict(DATA))
    with pytest.raises(UsernameAlreadyTakenError):
        register_service({**DATA, 'username': 'ANN_1', 'email': 'other@example.com'})
    assert _counts(db_session) == (1, 1, 1)


def test_register_service_atomic_when_membership_creation_fails(db_session, monkeypatch):
    def boom(**kwargs):
        raise RuntimeError('forced failure after the user insert')

    monkeypatch.setattr(service, 'TeamMembershipEntity', boom)
    with pytest.raises(RuntimeError):
        register_service(dict(DATA))
    assert _counts(db_session) == (0, 0, 0)


def test_login_service_returns_token_payload(db_session):
    user = register_service(dict(DATA))
    result = login_service({'email': 'ANN@example.com', 'password': DATA['password']})
    assert result['token_type'] == 'Bearer'
    assert result['expires_in'] == 3600
    assert result['user']['id'] == str(user.id)
    assert not any(k.startswith('password') for k in result['user'])
    claims = decode_token(result['access_token'])
    assert claims['sub'] == str(user.id)
    assert claims['exp'] - claims['iat'] == 3600


def test_login_service_rejects_wrong_password(db_session):
    register_service(dict(DATA))
    with pytest.raises(InvalidCredentialsError) as wrong:
        login_service({'email': DATA['email'], 'password': 'wrong-password'})
    with pytest.raises(InvalidCredentialsError) as unknown:
        login_service({'email': 'nobody@example.com', 'password': 'whatever1'})
    assert wrong.value.message == unknown.value.message == 'Invalid credentials'
