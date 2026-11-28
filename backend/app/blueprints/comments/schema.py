"""Marshmallow schemas for comments."""
from marshmallow import Schema, ValidationError, fields, validates


def _not_blank(value: str) -> None:
    if not value.strip():
        raise ValidationError('Content cannot be blank.')


class CommentCreateSchema(Schema):
    content = fields.String(required=True, validate=_not_blank)
    parent_id = fields.UUID(allow_none=True, load_default=None)

    @validates('content')
    def validate_length(self, value: str, **kwargs) -> None:
        if len(value) > 2000:
            raise ValidationError('Content must be 2000 characters or fewer.')


class CommentUpdateSchema(Schema):
    content = fields.String(required=True, validate=_not_blank)

    @validates('content')
    def validate_length(self, value: str, **kwargs) -> None:
        if len(value) > 2000:
            raise ValidationError('Content must be 2000 characters or fewer.')


class CommentSchema(Schema):
    id = fields.UUID(dump_only=True)
    card_id = fields.UUID(dump_only=True)
    parent_id = fields.UUID(attribute='parent_comment_id', allow_none=True, dump_only=True)
    author_id = fields.UUID(dump_only=True)
    content = fields.Method('get_content', dump_only=True)
    is_deleted = fields.Method('get_is_deleted', dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    def get_is_deleted(self, obj) -> bool:
        return obj.deleted_at is not None

    def get_content(self, obj) -> str:
        return '' if obj.deleted_at is not None else obj.content
