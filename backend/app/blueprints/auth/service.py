"""Auth business rules (BE-13, BE-15). No flask imports (ST-03)."""
from typing import Any

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app.blueprints.auth.schema import UserSchema
from app.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    UsernameAlreadyTakenError,
)
from app.extensions import db
from app.models import TeamEntity, TeamMembershipEntity, UserEntity
from app.utils.auth import issue_access_token

TOKEN_TYPE = 'Bearer'
EXPIRES_IN_SECONDS = 3600


def _email_taken(email: str) -> bool:
    return db.session.query(UserEntity.id).filter(
        func.lower(UserEntity.email) == email.lower()).first() is not None


def _username_taken(username: str) -> bool:
    return db.session.query(UserEntity.id).filter(
        func.lower(UserEntity.username) == username.lower()).first() is not None


def _check_duplicates(data: dict[str, Any]) -> None:
    if _username_taken(data['username']):
        raise UsernameAlreadyTakenError()
    if _email_taken(data['email']):
        raise EmailAlreadyRegisteredError()


def _raise_for_unique_violation(exc: IntegrityError, data: dict[str, Any]) -> None:
    """Map a concurrent unique violation to the matching 409 (BE-13)."""
    constraint = getattr(getattr(exc.orig, 'diag', None), 'constraint_name', None)
    if constraint == 'uq_users_email_lower' or (
            constraint != 'uq_users_username' and _email_taken(data['email'])):
        raise EmailAlreadyRegisteredError() from exc
    if constraint == 'uq_users_username' or _username_taken(data['username']):
        raise UsernameAlreadyTakenError() from exc
    raise exc


def _create_user_with_personal_team(data: dict[str, Any]) -> UserEntity:
    user = UserEntity(
        name=data['name'],
        username=data['username'],
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
    )
    db.session.add(user)
    db.session.flush()
    team = TeamEntity(name=f"{user.name}'s Team", is_personal=True, owner_id=user.id)
    db.session.add(team)
    db.session.flush()
    db.session.add(TeamMembershipEntity(team_id=team.id, user_id=user.id, role='admin'))
    return user


def register_service(data: dict[str, Any]) -> UserEntity:
    """Create user, personal Team and Admin membership in one transaction (R13.2)."""
    _check_duplicates(data)
    try:
        user = _create_user_with_personal_team(data)
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        _raise_for_unique_violation(exc, data)
    except Exception:
        db.session.rollback()
        raise
    return user


def login_service(data: dict[str, Any]) -> dict[str, Any]:
    """Return the token payload; unknown email and wrong password are identical 401s."""
    user = (
        db.session.query(UserEntity)
        .filter(func.lower(UserEntity.email) == data['email'].lower())
        .filter(UserEntity.deleted_at.is_(None))
        .first()
    )
    if user is None or not check_password_hash(user.password_hash, data['password']):
        raise InvalidCredentialsError()
    return {
        'access_token': issue_access_token(str(user.id)),
        'token_type': TOKEN_TYPE,
        'expires_in': EXPIRES_IN_SECONDS,
        'user': UserSchema().dump(user),
    }
