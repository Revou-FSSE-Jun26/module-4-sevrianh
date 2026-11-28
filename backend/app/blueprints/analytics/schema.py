"""Marshmallow schemas for board analytics."""
from datetime import timedelta

from marshmallow import Schema, ValidationError, fields, validates_schema

from app.utils.time import utc_now

MAX_RANGE_DAYS = 366


class AnalyticsQuerySchema(Schema):
    start_date = fields.Date(format='%Y-%m-%d', load_default=None)
    end_date = fields.Date(format='%Y-%m-%d', load_default=None)

    @validates_schema
    def validate_dates(self, data: dict, **kwargs) -> None:
        start = data.get('start_date')
        end = data.get('end_date')
        if (start is None) != (end is None):
            raise ValidationError('Both start_date and end_date must be provided together.')
        if start is None and end is None:
            today = utc_now().date()
            data['end_date'] = today
            data['start_date'] = today - timedelta(days=6)
            return
        if end < start:
            raise ValidationError('end_date cannot be before start_date.')
        if (end - start).days > MAX_RANGE_DAYS:
            raise ValidationError('Date range cannot exceed 366 days.')
