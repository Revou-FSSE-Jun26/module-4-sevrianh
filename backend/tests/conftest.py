"""Shared pytest setup (PostgreSQL only, TC-10).

Tests run against the separate `sevy_test` database that `flask db upgrade` has already
migrated, so migration-created indexes and constraints are the ones under test. Fixtures
never call `db.create_all()`; they truncate every table before each test instead.
"""
import itertools
import os
from pathlib import Path

from dotenv import load_dotenv

# backend/.env (git-ignored) supplies the real test DATABASE_URL. It must be loaded before
# the setdefault calls below, because load_dotenv() never overrides an existing variable.
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

os.environ.setdefault(
    'DATABASE_URL', 'postgresql+psycopg2://user:password@localhost:5432/sevy_test')
os.environ.setdefault('JWT_SECRET_KEY', 'test-secret-key-with-at-least-32-characters')
os.environ.setdefault('CORS_ORIGINS', 'http://localhost:3000')

import pytest  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402

from app import create_app  # noqa: E402
from app.extensions import db as _db  # noqa: E402
from app.models import (  # noqa: E402
    BoardColumnEntity, BoardEntity, CardCommentEntity, CardEntity, TeamEntity,
    TeamMembershipEntity, UserEntity,
)

_counter = itertools.count(1)


def _assert_test_database(url: str) -> None:
    parsed = make_url(url)
    if parsed.get_backend_name() != 'postgresql':
        raise RuntimeError('Tests must run on PostgreSQL, never SQLite (TC-10).')
    if not (parsed.database or '').endswith('_test'):
        raise RuntimeError('Refusing to truncate a database whose name does not end in _test.')


@pytest.fixture(scope='session')
def app():
    """Flask app bound to the migrated sevy_test database."""
    flask_app = create_app()
    flask_app.config.update(TESTING=True)
    _assert_test_database(flask_app.config['SQLALCHEMY_DATABASE_URI'])
    with flask_app.app_context():
        with _db.engine.connect() as conn:
            if conn.execute(text("SELECT to_regclass('public.alembic_version')")).scalar() is None:
                raise RuntimeError('sevy_test is not migrated: run `flask db upgrade` first.')
        yield flask_app


def _truncate_all() -> None:
    names = ', '.join(f'"{t.name}"' for t in _db.metadata.sorted_tables)
    _db.session.execute(text(f'TRUNCATE TABLE {names} RESTART IDENTITY CASCADE'))
    _db.session.commit()


@pytest.fixture()
def db_session(app):
    """Clean database session: all tables are empty at the start and rolled back at the end."""
    _db.session.remove()
    _truncate_all()
    yield _db.session
    _db.session.rollback()
    _db.session.remove()


@pytest.fixture()
def client(app, db_session):
    return app.test_client()


class Factory:
    """Row factories. Each call flushes and returns the new entity; nothing is committed."""

    def __init__(self, session):
        self.session = session

    def _add(self, obj):
        self.session.add(obj)
        self.session.flush()
        return obj

    def user(self, **kw):
        n = next(_counter)
        kw.setdefault('name', f'User {n}')
        kw.setdefault('username', f'user_{n}')
        kw.setdefault('email', f'user{n}@example.com')
        kw.setdefault('password_hash', 'hash-placeholder')
        return self._add(UserEntity(**kw))

    def team(self, owner=None, **kw):
        owner = owner or self.user()
        kw.setdefault('name', f'Team {next(_counter)}')
        kw.setdefault('is_personal', False)
        return self._add(TeamEntity(owner_id=owner.id, **kw))

    def membership(self, team, user, role='member'):
        return self._add(TeamMembershipEntity(team_id=team.id, user_id=user.id, role=role))

    def board(self, team=None, **kw):
        team = team or self.team()
        kw.setdefault('name', f'Board {next(_counter)}')
        return self._add(BoardEntity(team_id=team.id, **kw))

    def column(self, board=None, **kw):
        board = board or self.board()
        kw.setdefault('name', f'Column {next(_counter)}')
        kw.setdefault('order', 1024.0)
        return self._add(BoardColumnEntity(board_id=board.id, **kw))

    def card(self, column=None, created_by=None, **kw):
        column = column or self.column()
        created_by = created_by or self.user()
        kw.setdefault('title', f'Card {next(_counter)}')
        kw.setdefault('order', 1024.0)
        return self._add(CardEntity(column_id=column.id, created_by_id=created_by.id, **kw))

    def comment(self, card=None, author=None, **kw):
        card = card or self.card()
        author = author or self.user()
        kw.setdefault('content', 'A comment')
        return self._add(CardCommentEntity(card_id=card.id, author_id=author.id, **kw))


@pytest.fixture()
def factory(db_session):
    return Factory(db_session)
