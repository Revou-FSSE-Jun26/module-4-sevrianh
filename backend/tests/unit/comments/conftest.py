"""Shared fixtures for comments tests: Team A (admin, member, member2), outsider, Card."""
from types import SimpleNamespace

import pytest

from app.utils.auth import issue_access_token


@pytest.fixture()
def world(factory):
    admin = factory.user(email='cm_admin@example.com', username='cm_admin')
    member = factory.user(email='cm_member@example.com', username='cm_member')
    member2 = factory.user(email='cm_member2@example.com', username='cm_member2')
    outsider = factory.user(email='cm_outsider@example.com', username='cm_outsider')

    team = factory.team(owner=admin, is_personal=True)
    factory.membership(team, admin, 'admin')
    factory.membership(team, member, 'member')
    factory.membership(team, member2, 'member')

    board = factory.board(team, name='Board Alpha')
    column = factory.column(board, name='To Do')
    card = factory.card(column, created_by=admin, title='Deploy')
    factory.session.commit()
    return SimpleNamespace(
        admin=admin, member=member, member2=member2, outsider=outsider,
        team=team, board=board, card=card,
    )


@pytest.fixture()
def auth(app):
    def _auth(user):
        with app.app_context():
            return {'Authorization': f'Bearer {issue_access_token(str(user.id))}'}

    return _auth
