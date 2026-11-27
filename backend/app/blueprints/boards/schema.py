"""Boards input and output schemas (BE-05, BE-06)."""
from marshmallow import RAISE, Schema, fields, pre_load, validate


class _NameSchema(Schema):
    class Meta:
        unknown = RAISE

    @pre_load
    def trim_name(self, data, **kwargs):
        if isinstance(data, dict) and isinstance(data.get('name'), str):
            data = {**data, 'name': data['name'].strip()}
        return data


class BoardCreateSchema(_NameSchema):
    """POST /api/boards body: `name` 1-100 after trimming, optional `team_id` (R4.1-R4.3)."""

    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    team_id = fields.UUID()


class BoardUpdateSchema(_NameSchema):
    """PATCH /api/boards/<id> body: `name` is the only field (R4.7, R4.8)."""

    name = fields.String(required=True, validate=validate.Length(min=1, max=100))


class MemberAddSchema(Schema):
    """POST /api/boards/<id>/members body (R12.1)."""

    class Meta:
        unknown = RAISE

    email = fields.Email(required=True, validate=validate.Length(max=255))
    role = fields.String(load_default='member', validate=validate.OneOf(['member', 'admin']))


class MemberRoleUpdateSchema(Schema):
    """PATCH /api/boards/<id>/members/<user_id> body (R12.4)."""

    class Meta:
        unknown = RAISE

    role = fields.String(required=True, validate=validate.OneOf(['member', 'admin']))


class InviteLinkCreateSchema(Schema):
    """POST /api/boards/<id>/invite-links body: empty or `{}`, any field rejected (R3.1)."""

    class Meta:
        unknown = RAISE


class InviteLinkSchema(Schema):
    """Create response: the raw token is returned once only (R3.1)."""

    id = fields.UUID()
    board_id = fields.UUID()
    token = fields.String()
    created_at = fields.DateTime()


class MemberSchema(Schema):
    user_id = fields.UUID()
    name = fields.String()
    username = fields.String()
    role = fields.String()


class AssigneeSchema(Schema):
    id = fields.UUID()
    name = fields.String()
    username = fields.String()


class CardSchema(Schema):
    """Card nested in a Board (BE-06)."""

    id = fields.UUID()
    title = fields.String()
    description = fields.String(allow_none=True)
    order = fields.Float()
    column_id = fields.UUID()
    assignee_id = fields.UUID(allow_none=True)
    assignee = fields.Nested(AssigneeSchema, allow_none=True)
    created_by_id = fields.UUID()
    completed_at = fields.DateTime(allow_none=True)
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class ColumnSchema(Schema):
    id = fields.UUID()
    name = fields.String()
    order = fields.Float()
    is_done = fields.Boolean()
    cards = fields.Nested(CardSchema, many=True)


class BoardSchema(Schema):
    """Board summary used by create, list and update."""

    id = fields.UUID()
    name = fields.String()
    team_id = fields.UUID()
    created_at = fields.DateTime()


class BoardDetailSchema(BoardSchema):
    columns = fields.Nested(ColumnSchema, many=True)
