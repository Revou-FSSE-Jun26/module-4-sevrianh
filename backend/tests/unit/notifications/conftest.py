"""Shared fixtures for notifications tests: Team A (alice admin, bob, carol), outsider, Card."""
from types import SimpleNamespace

import pytest

from app.utils.auth import issue_access_token


@pytest.fixture()
def world(factory):
    alice = factory.user(name='Alice', username='alice', email='nt_alice@example.com')
    bob = factory.user(name='Bob', username='bob', email='nt_bob@example.com')
    carol = factory.user(name='Carol', username='carol', email='nt_carol@example.com')
    outsider = factory.user(name='Out', username='outsider', email='nt_out@example.com')

    team = factory.team(owner=alice, is_personal=True)
    factory.membership(team, alice, 'admin')
    factory.membership(team, bob, 'member')
    factory.membership(team, carol, 'member')

    board = factory.board(team, name='Board Alpha')
    column = factory.column(board, name='To Do')
    card = factory.card(column, created_by=alice, title='Deploy to Railway')
    factory.session.commit()
    return SimpleNamespace(
        alice=alice, bob=bob, carol=carol, outsider=outsider,
        team=team, board=board, column=column, card=card,
    )


@pytest.fixture()
def auth(app):
    def _auth(user):
        with app.app_context():
            return {'Authorization': f'Bearer {issue_access_token(str(user.id))}'}

    return _auth
