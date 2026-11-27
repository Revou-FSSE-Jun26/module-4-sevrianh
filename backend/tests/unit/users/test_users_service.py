"""Users service tests (R19.1, R19.2, R19.5)."""
import pytest

from app.blueprints.users.service import (
    get_current_user_service, update_current_user_service,
)
from app.exceptions import EmailAlreadyRegisteredError


def test_get_current_user_service_returns_same_user(factory):
    user = factory.user()
    assert get_current_user_service(user) is user


def test_update_current_user_service_updates_name_and_email(factory, db_session):
    user = factory.user()
    result = update_current_user_service(user, {'name': 'New Name', 'email': 'new@example.com'})
    db_session.refresh(result)
    assert (result.name, result.email) == ('New Name', 'new@example.com')


def test_update_current_user_service_updates_only_given_field(factory):
    user = factory.user(name='Keep', email='keep@example.com')
    update_current_user_service(user, {'name': 'Changed'})
    assert (user.name, user.email) == ('Changed', 'keep@example.com')


def test_update_current_user_service_allows_own_email_in_other_case(factory):
    user = factory.user(email='me@example.com')
    update_current_user_service(user, {'email': 'ME@example.com'})
    assert user.email == 'ME@example.com'


def test_update_current_user_service_rejects_duplicate_email_case_insensitively(factory):
    factory.user(email='taken@example.com')
    user = factory.user(email='mine@example.com')
    with pytest.raises(EmailAlreadyRegisteredError):
        update_current_user_service(user, {'email': 'TAKEN@Example.com'})
    assert user.email == 'mine@example.com'
