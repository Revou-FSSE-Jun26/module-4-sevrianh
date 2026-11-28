"""Commit-failure branches of update_current_user_service (R19.2, R19.5)."""
import pytest
from sqlalchemy.exc import IntegrityError

from app.blueprints.users.service import update_current_user_service
from app.exceptions import EmailAlreadyRegisteredError
from app.extensions import db


def test_update_current_user_service_maps_unique_violation_to_conflict(
        db_session, factory, monkeypatch):
    user = factory.user(name='Before')
    db_session.commit()

    def fail_commit():
        raise IntegrityError('stmt', {}, Exception('uq_users_email_lower'))

    monkeypatch.setattr(db.session, 'commit', fail_commit)
    with pytest.raises(EmailAlreadyRegisteredError):
        update_current_user_service(user, {'email': 'new@example.com'})


def test_update_current_user_service_reraises_unexpected_commit_error(
        db_session, factory, monkeypatch):
    user = factory.user()
    db_session.commit()

    def fail_commit():
        raise RuntimeError('db down')

    monkeypatch.setattr(db.session, 'commit', fail_commit)
    with pytest.raises(RuntimeError):
        update_current_user_service(user, {'name': 'After'})
