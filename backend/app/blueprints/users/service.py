"""Users business rules (R19). No flask imports (ST-03)."""
from typing import Any

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.exceptions import EmailAlreadyRegisteredError
from app.extensions import db
from app.models import UserEntity


def get_current_user_service(user: UserEntity) -> UserEntity:
    """Return the authenticated user (R19.1)."""
    return user


def _email_used_by_other(email: str, user: UserEntity) -> bool:
    return db.session.query(UserEntity.id).filter(
        func.lower(UserEntity.email) == email.lower(),
        UserEntity.id != user.id,
    ).first() is not None


def update_current_user_service(user: UserEntity, data: dict[str, Any]) -> UserEntity:
    """Update name and/or email; a case-insensitive duplicate email is a 409 (R19.2, R19.5)."""
    if 'email' in data and _email_used_by_other(data['email'], user):
        raise EmailAlreadyRegisteredError()
    try:
        for field in ('name', 'email'):
            if field in data:
                setattr(user, field, data[field])
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise EmailAlreadyRegisteredError() from exc
    except Exception:
        db.session.rollback()
        raise
    return user
