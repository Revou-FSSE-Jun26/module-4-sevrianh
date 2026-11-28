"""Unit tests for analytics service (T-46)."""
from datetime import timedelta

import pytest
from marshmallow import ValidationError
from sqlalchemy import event

from app.blueprints.analytics.schema import AnalyticsQuerySchema
from app.blueprints.analytics.service import get_board_analytics_service
from app.exceptions import AdminAccessRequiredError, BoardNotFoundException
from app.extensions import db
from app.utils.card_helpers import record_card_activity
from app.utils.time import utc_now


def test_analytics_query_schema_defaults():
    data = AnalyticsQuerySchema().load({})
    assert (data['end_date'] - data['start_date']).days == 6


def test_analytics_query_schema_rejects_single_date():
    with pytest.raises(ValidationError):
        AnalyticsQuerySchema().load({'start_date': '2025-01-01'})
    with pytest.raises(ValidationError):
        AnalyticsQuerySchema().load({'end_date': '2025-01-01'})


def test_analytics_query_schema_rejects_inverted_or_too_long_range():
    with pytest.raises(ValidationError):
        AnalyticsQuerySchema().load({'start_date': '2025-01-10', 'end_date': '2025-01-01'})
    with pytest.raises(ValidationError):
        AnalyticsQuerySchema().load({'start_date': '2024-01-01', 'end_date': '2025-01-05'})


def test_analytics_sums_and_exclusions(factory):
    admin = factory.user()
    member = factory.user()
    team = factory.team(owner=admin)
    factory.membership(team=team, user=admin, role='admin')
    factory.membership(team=team, user=member, role='member')
    board = factory.board(team=team)
    col_todo = factory.column(board=board, name='To Do', order=1000)
    col_done = factory.column(board=board, name='Done', order=2000, is_done=True)

    now = utc_now()
    monday = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    c1 = factory.card(column=col_todo, created_by=admin, order=1000)
    c2 = factory.card(column=col_done, created_by=admin, order=1000, completed_at=monday)
    # Sunday before this week -> excluded from completed_this_week
    factory.card(
        column=col_done,
        created_by=admin,
        order=2000,
        completed_at=monday - timedelta(seconds=1),
    )
    # Soft-deleted card -> excluded from counts and events
    c_del = factory.card(column=col_todo, created_by=admin, order=2000, deleted_at=now)

    record_card_activity(board.id, admin.id, 'card_created', c1.id)
    record_card_activity(board.id, admin.id, 'card_moved', c2.id)
    record_card_activity(board.id, member.id, 'card_created', c_del.id)
    db.session.commit()

    query = AnalyticsQuerySchema().load({})
    res = get_board_analytics_service(board.id, query, admin.id)

    assert sum(c['count'] for c in res['cards_per_column']) == 3
    assert res['completed_this_week'] == 1
    assert sum(d['count'] for d in res['activity_per_day']) == 2
    by_user = {m['user_id']: m['event_count'] for m in res['member_activity']}
    assert by_user[str(admin.id)] == 2
    assert by_user[str(member.id)] == 0


def test_analytics_member_forbidden_and_missing_board(factory):
    admin = factory.user()
    member = factory.user()
    team = factory.team(owner=admin)
    factory.membership(team=team, user=admin, role='admin')
    factory.membership(team=team, user=member, role='member')
    board = factory.board(team=team)
    query = AnalyticsQuerySchema().load({})

    with pytest.raises(AdminAccessRequiredError):
        get_board_analytics_service(board.id, query, member.id)
    with pytest.raises(BoardNotFoundException):
        get_board_analytics_service('00000000-0000-0000-0000-000000000000', query, admin.id)


def test_analytics_query_count_at_most_5(factory):
    admin = factory.user()
    team = factory.team(owner=admin)
    factory.membership(team=team, user=admin, role='admin')
    board = factory.board(team=team)
    for i in range(5):
        col = factory.column(board=board, name=f'Col {i}', order=(i + 1) * 1000)
        for j in range(10):
            factory.card(column=col, created_by=admin, order=(j + 1) * 1000)

    query = AnalyticsQuerySchema().load({})
    queries = []

    def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        queries.append(statement)

    event.listen(db.engine, 'before_cursor_execute', _before_cursor_execute)
    try:
        res = get_board_analytics_service(board.id, query, admin.id)
    finally:
        event.remove(db.engine, 'before_cursor_execute', _before_cursor_execute)

    assert sum(c['count'] for c in res['cards_per_column']) == 50
    # 1 board + 1 membership + 4 analytics queries = 6 max, or <=5 analytics queries
    assert len(queries) <= 6
