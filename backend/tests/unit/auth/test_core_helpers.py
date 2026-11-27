"""Unit tests for utils/time, utils/responses and exceptions (T-03)."""
import pytest
from flask import Flask

from app import exceptions as exc
from app.utils.responses import error, format_validation_error, success
from app.utils.time import utc_now


@pytest.fixture
def app_ctx():
    app = Flask(__name__)
    with app.app_context():
        yield app


def test_utc_now_is_timezone_aware_utc():
    now = utc_now()
    assert now.tzinfo is not None
    assert now.utcoffset().total_seconds() == 0


def test_success_wraps_data_with_default_and_custom_status(app_ctx):
    resp, status = success({'id': 'x'})
    assert status == 200 and resp.get_json() == {'data': {'id': 'x'}}
    _, status = success([], 201)
    assert status == 201


def test_error_wraps_single_string(app_ctx):
    resp, status = error('Not found', 404)
    assert status == 404
    assert resp.get_json() == {'error': 'Not found'}


def test_format_validation_error_exact_normalized_string():
    payload = {
        'title': ['Missing data for required field.', 'Too short.'],
        'column_id': ['Not a valid UUID.'],
        'extra': ['Unknown field.'],
    }
    assert format_validation_error(payload) == (
        'column_id: Not a valid UUID. | extra: Unknown field. | '
        'title: Missing data for required field., Too short.'
    )


def test_format_validation_error_flattens_nested_messages():
    assert format_validation_error({'a': {'b': ['bad']}}) == 'a.b: bad'


EXPECTED = {
    'InvalidCredentialsError': (401, 'Invalid credentials'),
    'AuthenticationRequiredError': (401, None),
    'EmailAlreadyRegisteredError': (409, None),
    'UsernameAlreadyTakenError': (409, None),
    'UserNotFoundException': (404, 'User not found'),
    'BoardNotFoundException': (404, exc.ACCESS_OR_NOT_FOUND_MESSAGE),
    'ColumnNotFoundException': (404, exc.ACCESS_OR_NOT_FOUND_MESSAGE),
    'CardNotFoundException': (404, exc.ACCESS_OR_NOT_FOUND_MESSAGE),
    'CommentNotFoundException': (404, exc.ACCESS_OR_NOT_FOUND_MESSAGE),
    'TeamAccessDeniedError': (403, exc.ACCESS_OR_NOT_FOUND_MESSAGE),
    'AdminAccessRequiredError': (403, 'Admin access required'),
    'CommentOwnershipError': (403, None),
    'MemberAlreadyExistsError': (409, None),
    'MemberNotFoundException': (404, None),
    'LastAdminError': (409, None),
    'InviteLinkNotFoundException': (404, 'Not found'),
    'NotificationNotFoundException': (404, 'Not found'),
    'InvalidAssigneeError': (400, 'Assignee must be a Team member'),
    'InvalidParentCommentError': (400, None),
    'InvalidTargetColumnError': (400, None),
    'OrderConflictError': (409, None),
}


@pytest.mark.parametrize('name', sorted(EXPECTED))
def test_exception_status_code_and_default_message(name):
    cls = getattr(exc, name)
    status, message = EXPECTED[name]
    assert issubclass(cls, exc.AppException)
    assert cls.status_code == status
    instance = cls()
    assert instance.message and isinstance(instance.message, str)
    if message is not None:
        assert instance.message == message


def test_exception_custom_message_overrides_default():
    assert exc.OrderConflictError('custom').message == 'custom'


def test_access_or_not_found_message_value():
    assert exc.ACCESS_OR_NOT_FOUND_MESSAGE == 'Not found or access denied'
