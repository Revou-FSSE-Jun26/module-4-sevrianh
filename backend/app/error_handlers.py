"""Global error handling and JWT error callbacks (BE-11, BE-13)."""
from flask import Flask
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException

from app.exceptions import AppException
from app.extensions import jwt
from app.logging_config import log_handled_error
from app.utils.responses import error, format_validation_error

INTERNAL_ERROR_MESSAGE = 'Internal server error'


def _handle_app_exception(exc: AppException):
    log_handled_error(type(exc).__name__, exc.status_code)
    return error(exc.message, exc.status_code)


def _handle_validation_error(exc: ValidationError):
    log_handled_error(type(exc).__name__, 400)
    return error(format_validation_error(exc.messages), 400)


def _handle_http_exception(exc: HTTPException):
    status = exc.code or 500
    log_handled_error(type(exc).__name__, status)
    message = 'Not found' if status == 404 else exc.name
    return error(message, status)


def _handle_unexpected(exc: Exception):
    log_handled_error(type(exc).__name__, 500)
    return error(INTERNAL_ERROR_MESSAGE, 500)


def _register_jwt_callbacks() -> None:
    """All Flask-JWT-Extended failures answer 401 in the envelope, never 422."""

    @jwt.unauthorized_loader
    def _missing(_reason: str):
        log_handled_error('MissingToken', 401)
        return error('Authentication required', 401)

    @jwt.invalid_token_loader
    def _invalid(_reason: str):
        log_handled_error('InvalidToken', 401)
        return error('Invalid token', 401)

    @jwt.expired_token_loader
    def _expired(_header: dict, _payload: dict):
        log_handled_error('ExpiredToken', 401)
        return error('Token has expired', 401)

    @jwt.token_verification_failed_loader
    def _verification_failed(_header: dict, _payload: dict):
        log_handled_error('TokenVerificationFailed', 401)
        return error('Invalid token', 401)


def register_error_handlers(app: Flask) -> None:
    app.register_error_handler(AppException, _handle_app_exception)
    app.register_error_handler(ValidationError, _handle_validation_error)
    app.register_error_handler(HTTPException, _handle_http_exception)
    app.register_error_handler(Exception, _handle_unexpected)
    _register_jwt_callbacks()
