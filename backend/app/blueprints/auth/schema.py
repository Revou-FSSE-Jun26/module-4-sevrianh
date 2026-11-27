"""Auth input and output schemas (BE-05, BE-06)."""
from marshmallow import RAISE, Schema, fields, post_load, validate


class RegisterSchema(Schema):
    class Meta:
        unknown = RAISE

    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    username = fields.String(
        required=True,
        validate=[
            validate.Length(min=3, max=30),
            validate.Regexp(r'^[A-Za-z0-9_]+$', error='Only letters, digits and underscore.'),
        ],
    )
    email = fields.String(
        required=True, validate=[validate.Length(max=254), validate.Email()])
    password = fields.String(
        required=True, load_only=True, validate=validate.Length(min=8, max=128))

    @post_load
    def normalize_username(self, data: dict, **kwargs) -> dict:
        data['username'] = data['username'].lower()
        return data


class LoginSchema(Schema):
    class Meta:
        unknown = RAISE

    email = fields.Email(required=True)
    password = fields.String(
        required=True, load_only=True, validate=validate.Length(min=1))


class UserSchema(Schema):
    """Safe user payload; never references the password hash."""

    id = fields.UUID()
    name = fields.String()
    username = fields.String()
    email = fields.String()
    created_at = fields.DateTime()
