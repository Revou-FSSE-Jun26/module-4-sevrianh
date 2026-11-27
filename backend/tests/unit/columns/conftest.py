"""Shared fixtures for the columns tests: Team A (admin, member), outsider, Team B."""
from types import SimpleNamespace

import pytest

from app.utils.auth import issue_access_token


@pytest.fixture()
def world(factory, app):
    """Team A (admin, member), Board A, outsider, Team B with Board B."""
    admin = factory.user(email='col_admin@example.com')
    member = factory.user(email='col_member@example.com')
    outsider = factory.user(email='col_outsider@example.com')
    team = factory.team(owner=admin, is_personal=True)
    factory.membership(team, admin, 'admin')
    factory.membership(team, member, 'member')
    board = factory.board(team, name='Board A')

    admin_b = factory.user(email='col_adminb@example.com')
    team_b = factory.team(owner=admin_b, is_personal=True)
    factory.membership(team_b, admin_b, 'admin')
    board_b = factory.board(team_b, name='Board B')
    factory.session.commit()
    return SimpleNamespace(
        admin=admin, member=member, outsider=outsider,
        team=team, board=board, admin_b=admin_b, team_b=team_b, board_b=board_b,
    )


@pytest.fixture()
def auth(app):
    """Return `auth(user)` -> Authorization header for that user."""

    def _auth(user):
        with app.app_context():
            return {'Authorization': f'Bearer {issue_access_token(str(user.id))}'}

    return _auth
