"""Notifications input and output schemas (BE-05, BE-06)."""
import re

from marshmallow import RAISE, Schema, ValidationError, fields, pre_load, validate

_INT_PATTERN = re.compile(r'[0-9]+$')


def _require_int(value):
    """Accept an int or a digit string; reject bools, floats, and other text (R9.8)."""
    if isinstance(value, str) and _INT_PATTERN.fullmatch(value):
        return int(value)
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    raise ValidationError('Not a valid integer.')


class NotificationQuerySchema(Schema):
    """GET /api/notifications query: page >= 1 (default 1), per_page 1-50 (default 10)."""

    class Meta:
        unknown = RAISE

    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(load_default=10, validate=validate.Range(min=1, max=50))

    @pre_load
    def parse_integers(self, data, **kwargs):
        if not isinstance(data, dict):
            return data
        parsed = dict(data)
        for key in ('page', 'per_page'):
            if key in parsed:
                parsed[key] = _require_int(parsed[key])
        return parsed


class NotificationSchema(Schema):
    """One notification. `card_id` and `board_id` are derived, never stored (OD-19)."""

    id = fields.UUID()
    type = fields.String()
    message = fields.String()
    is_read = fields.Boolean()
    created_at = fields.DateTime()
    comment_id = fields.UUID()
    card_id = fields.UUID()
    board_id = fields.UUID()


class NotificationListSchema(Schema):
    """GET /api/notifications payload (BE-07)."""

    items = fields.Nested(NotificationSchema, many=True)
    page = fields.Integer()
    per_page = fields.Integer()
    total = fields.Integer()
    total_pages = fields.Integer()
    unread_count = fields.Integer()
