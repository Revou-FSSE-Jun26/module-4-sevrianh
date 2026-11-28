"""Shared fixtures for cards tests: Team A (admin, member, member2), outsider, Team B."""
from types import SimpleNamespace

import pytest

from app.utils.auth import issue_access_token


@pytest.fixture()
def world(factory):
    """Team A (admin, member, member2) with Board A (todo, done), outsider, Team B."""
    admin = factory.user(email='card_admin@example.com')
    member = factory.user(email='card_member@example.com')
    member2 = factory.user(email='card_member2@example.com')
    outsider = factory.user(email='card_outsider@example.com')

    team = factory.team(owner=admin, is_personal=True)
    factory.membership(team, admin, 'admin')
    factory.membership(team, member, 'member')
    factory.membership(team, member2, 'member')

    board = factory.board(team, name='Board Alpha')
    todo = factory.column(board, name='To Do', order=1024.0, is_done=False)
    done = factory.column(board, name='Done', order=2048.0, is_done=True)

    admin_b = factory.user(email='card_adminb@example.com')
    team_b = factory.team(owner=admin_b, is_personal=True)
    factory.membership(team_b, admin_b, 'admin')
    board_b = factory.board(team_b, name='Board Beta')
    col_b = factory.column(board_b, name='Backlog', order=1024.0, is_done=False)

    factory.session.commit()
    return SimpleNamespace(
        admin=admin, member=member, member2=member2, outsider=outsider,
        team=team, board=board, todo=todo, done=done,
        admin_b=admin_b, team_b=team_b, board_b=board_b, col_b=col_b,
    )


@pytest.fixture()
def auth(app):
    """Return `auth(user)` -> Authorization header for that user."""

    def _auth(user):
        with app.app_context():
            return {'Authorization': f'Bearer {issue_access_token(str(user.id))}'}

    return _auth
