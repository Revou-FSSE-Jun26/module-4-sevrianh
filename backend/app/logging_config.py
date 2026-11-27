"""Structured JSON logging for handled errors (BE-12)."""
import json
import logging

from flask import request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt.exceptions import PyJWTError

LOGGER_NAME = 'sevy'
LOG_FIELDS = ('level', 'endpoint', 'error_type', 'user_id')


def configure_logging() -> logging.Logger:
    """Return the app logger; messages are already JSON, so the format is the bare message."""
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def _current_user_id() -> str | None:
    """User id from a valid JWT, or None (unauthenticated requests and Guests)."""
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
    except (JWTExtendedException, PyJWTError):
        return None
    return str(identity) if identity is not None else None


def log_handled_error(error_type: str, status_code: int) -> None:
    """Log one handled error with exactly the four BE-12 fields.

    4xx logs at WARNING, everything else at ERROR. No headers, tokens or bodies.
    """
    level = logging.WARNING if 400 <= status_code < 500 else logging.ERROR
    payload = {
        'level': logging.getLevelName(level),
        'endpoint': request.endpoint,
        'error_type': error_type,
        'user_id': _current_user_id(),
    }
    logging.getLogger(LOGGER_NAME).log(level, json.dumps(payload))
