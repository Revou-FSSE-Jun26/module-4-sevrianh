"""Board analytics service. No flask imports (BE-03)."""
from datetime import datetime, time, timedelta, timezone
from typing import Any

from sqlalchemy import and_, func, or_

from app.blueprints.boards.service import require_team_admin_service
from app.exceptions import BoardNotFoundException
from app.extensions import db
from app.models import (
    ActivityEventEntity,
    BoardColumnEntity,
    BoardEntity,
    CardEntity,
    TeamMembershipEntity,
    UserEntity,
)
from app.utils.card_helpers import to_uuid
from app.utils.time import utc_now


def _load_board(board_id: Any) -> BoardEntity:
    board = db.session.get(BoardEntity, to_uuid(board_id))
    if board is None or board.deleted_at is not None:
        raise BoardNotFoundException()
    return board


def _iso_week_monday_utc() -> datetime:
    now = utc_now()
    monday = now - timedelta(days=now.weekday())
    return monday.replace(hour=0, minute=0, second=0, microsecond=0)


def get_board_analytics_service(
    board_id: Any, query: dict[str, Any], user_id: Any
) -> dict[str, Any]:
    board = _load_board(board_id)
    require_team_admin_service(board.id, to_uuid(user_id))

    start_date = query['start_date']
    end_date = query['end_date']
    start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    end_dt_excl = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=timezone.utc)

    col_rows = (
        db.session.query(
            BoardColumnEntity.id,
            BoardColumnEntity.name,
            func.count(CardEntity.id),
        )
        .outerjoin(
            CardEntity,
            and_(
                CardEntity.column_id == BoardColumnEntity.id,
                CardEntity.deleted_at.is_(None),
            ),
        )
        .filter(
            BoardColumnEntity.board_id == board.id,
            BoardColumnEntity.deleted_at.is_(None),
        )
        .group_by(BoardColumnEntity.id, BoardColumnEntity.name, BoardColumnEntity.order)
        .order_by(BoardColumnEntity.order.asc(), BoardColumnEntity.id.asc())
        .all()
    )
    cards_per_column = [
        {'column_id': str(cid), 'column_name': cname, 'count': int(cnt)}
        for cid, cname, cnt in col_rows
    ]

    monday = _iso_week_monday_utc()
    completed_this_week = (
        db.session.query(func.count(CardEntity.id))
        .join(BoardColumnEntity, BoardColumnEntity.id == CardEntity.column_id)
        .filter(
            BoardColumnEntity.board_id == board.id,
            BoardColumnEntity.deleted_at.is_(None),
            CardEntity.deleted_at.is_(None),
            CardEntity.completed_at.is_not(None),
            CardEntity.completed_at >= monday,
        )
        .scalar() or 0
    )

    event_filter = and_(
        ActivityEventEntity.actor_id == UserEntity.id,
        ActivityEventEntity.board_id == board.id,
        ActivityEventEntity.created_at >= start_dt,
        ActivityEventEntity.created_at < end_dt_excl,
        or_(
            ActivityEventEntity.entity_id.is_(None),
            ~ActivityEventEntity.entity_id.in_(
                db.session.query(CardEntity.id).filter(CardEntity.deleted_at.is_not(None))
            ),
        ),
    )
    member_rows = (
        db.session.query(
            UserEntity.id,
            UserEntity.name,
            UserEntity.username,
            func.count(ActivityEventEntity.id),
        )
        .join(TeamMembershipEntity, TeamMembershipEntity.user_id == UserEntity.id)
        .outerjoin(ActivityEventEntity, event_filter)
        .filter(
            TeamMembershipEntity.team_id == board.team_id,
            TeamMembershipEntity.deleted_at.is_(None),
            UserEntity.deleted_at.is_(None),
        )
        .group_by(UserEntity.id, UserEntity.name, UserEntity.username)
        .order_by(UserEntity.name.asc())
        .all()
    )
    member_activity = [
        {
            'user_id': str(uid),
            'name': uname,
            'username': username,
            'event_count': int(cnt),
        }
        for uid, uname, username, cnt in member_rows
    ]

    day_rows = (
        db.session.query(
            func.date(ActivityEventEntity.created_at),
            func.count(ActivityEventEntity.id),
        )
        .outerjoin(CardEntity, CardEntity.id == ActivityEventEntity.entity_id)
        .filter(
            ActivityEventEntity.board_id == board.id,
            ActivityEventEntity.created_at >= start_dt,
            ActivityEventEntity.created_at < end_dt_excl,
            or_(ActivityEventEntity.entity_id.is_(None), CardEntity.deleted_at.is_(None)),
        )
        .group_by(func.date(ActivityEventEntity.created_at))
        .all()
    )
    day_counts = {str(d): int(cnt) for d, cnt in day_rows}
    activity_per_day = []
    cur = start_date
    while cur <= end_date:
        key = cur.isoformat()
        activity_per_day.append({'date': key, 'count': day_counts.get(key, 0)})
        cur += timedelta(days=1)

    return {
        'cards_per_column': cards_per_column,
        'completed_this_week': int(completed_this_week),
        'member_activity': member_activity,
        'activity_per_day': activity_per_day,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
    }
