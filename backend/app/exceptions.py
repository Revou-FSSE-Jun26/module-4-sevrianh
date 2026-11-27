"""Typed application exceptions (BE-10)."""

ACCESS_OR_NOT_FOUND_MESSAGE = 'Not found or access denied'


class AppException(Exception):
    """Base class: carries `status_code` and a default `message`."""

    status_code = 500
    message = 'Internal server error'

    def __init__(self, message: str | None = None) -> None:
        self.message = message if message is not None else type(self).message
        super().__init__(self.message)


class InvalidCredentialsError(AppException):
    status_code = 401
    message = 'Invalid credentials'


class AuthenticationRequiredError(AppException):
    status_code = 401
    message = 'Authentication required'


class EmailAlreadyRegisteredError(AppException):
    status_code = 409
    message = 'Email already registered'


class UsernameAlreadyTakenError(AppException):
    status_code = 409
    message = 'Username already taken'


class UserNotFoundException(AppException):
    status_code = 404
    message = 'User not found'


class BoardNotFoundException(AppException):
    status_code = 404
    message = ACCESS_OR_NOT_FOUND_MESSAGE


class ColumnNotFoundException(AppException):
    status_code = 404
    message = ACCESS_OR_NOT_FOUND_MESSAGE


class CardNotFoundException(AppException):
    status_code = 404
    message = ACCESS_OR_NOT_FOUND_MESSAGE


class CommentNotFoundException(AppException):
    status_code = 404
    message = ACCESS_OR_NOT_FOUND_MESSAGE


class TeamAccessDeniedError(AppException):
    status_code = 403
    message = ACCESS_OR_NOT_FOUND_MESSAGE


class AdminAccessRequiredError(AppException):
    status_code = 403
    message = 'Admin access required'


class CommentOwnershipError(AppException):
    status_code = 403
    message = 'Only the author can modify this comment'


class MemberAlreadyExistsError(AppException):
    status_code = 409
    message = 'User is already a member of the Team'


class MemberNotFoundException(AppException):
    status_code = 404
    message = 'Member not found'


class LastAdminError(AppException):
    status_code = 409
    message = 'A Team must keep at least one Admin'


class InviteLinkNotFoundException(AppException):
    status_code = 404
    message = 'Not found'


class NotificationNotFoundException(AppException):
    status_code = 404
    message = 'Not found'


class InvalidAssigneeError(AppException):
    status_code = 400
    message = 'Assignee must be a Team member'


class InvalidParentCommentError(AppException):
    status_code = 400
    message = 'Invalid parent comment'


class InvalidTargetColumnError(AppException):
    status_code = 400
    message = 'Invalid target column'


class OrderConflictError(AppException):
    status_code = 409
    message = 'Order conflict'
