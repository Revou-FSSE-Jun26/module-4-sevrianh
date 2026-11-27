"""Users input and output schemas (BE-05, BE-06)."""
from marshmallow import RAISE, Schema, ValidationError, fields, pre_load, validate, validates_schema


class UserUpdateSchema(Schema):
    """PATCH /api/users/me body: only `name` and `email`, at least one (R19.2 to R19.6)."""

    class Meta:
        unknown = RAISE

    name = fields.String(validate=validate.Length(min=1, max=100))
    email = fields.String(validate=[validate.Length(max=254), validate.Email()])

    @pre_load
    def trim_name(self, data, **kwargs):
        if isinstance(data, dict) and isinstance(data.get('name'), str):
            data = {**data, 'name': data['name'].strip()}
        return data

    @validates_schema
    def require_one_field(self, data: dict, **kwargs) -> None:
        if not data:
            raise ValidationError('At least one of name or email is required.')


class UserSchema(Schema):
    """Safe user payload; never references the password hash."""

    id = fields.UUID()
    name = fields.String()
    username = fields.String()
    email = fields.String()
    created_at = fields.DateTime()
