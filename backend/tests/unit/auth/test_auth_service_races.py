"""Concurrent-registration and rollback branches of register_service (R13.2, R13.3)."""
import pytest

from app.blueprints.auth import service as auth_service
from app.blueprints.auth.service import register_service
from app.exceptions import EmailAlreadyRegisteredError, UsernameAlreadyTakenError
from app.models import TeamEntity, UserEntity


def _data(**overrides):
    base = {
        'name': 'Race User', 'username': 'race_user',
        'email': 'race@example.com', 'password': 'Passw0rd!x',
    }
    return {**base, **overrides}


@pytest.fixture()
def skip_precheck(monkeypatch):
    """Simulate two requests that both passed the duplicate pre-check."""
    monkeypatch.setattr(auth_service, '_check_duplicates', lambda data: None)


def test_register_service_maps_email_unique_violation_to_conflict(db_session, skip_precheck):
    register_service(_data())
    with pytest.raises(EmailAlreadyRegisteredError):
        register_service(_data(username='other_name', email='RACE@example.com'))
    assert db_session.query(UserEntity).count() == 1


def test_register_service_maps_username_unique_violation_to_conflict(db_session, skip_precheck):
    register_service(_data())
    with pytest.raises(UsernameAlreadyTakenError):
        register_service(_data(email='different@example.com'))
    assert db_session.query(UserEntity).count() == 1
    assert db_session.query(TeamEntity).count() == 1


def test_register_service_rolls_back_and_reraises_unexpected_error(db_session, monkeypatch):
    def boom(data):
        raise RuntimeError('db down')

    monkeypatch.setattr(auth_service, '_create_user_with_personal_team', boom)
    with pytest.raises(RuntimeError):
        register_service(_data())
    assert db_session.query(UserEntity).count() == 0
