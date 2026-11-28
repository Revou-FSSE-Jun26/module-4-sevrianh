"""Cards input and output schemas (BE-05, BE-06)."""
from marshmallow import RAISE, Schema, ValidationError, fields, pre_load, validate, validates_schema


class _TrimmedTitleSchema(Schema):
    class Meta:
        unknown = RAISE

    @pre_load
    def trim_title(self, data, **kwargs):
        if isinstance(data, dict) and isinstance(data.get('title'), str):
            data = {**data, 'title': data['title'].strip()}
        return data


class CardCreateSchema(_TrimmedTitleSchema):
    """POST /api/columns/<id>/cards body (R6.1, R6.3)."""

    title = fields.String(required=True, validate=validate.Length(min=1, max=200))
    description = fields.String(
        allow_none=True, load_default=None, validate=validate.Length(max=5000)
    )
    assignee_id = fields.UUID(allow_none=True, load_default=None)


class CardUpdateSchema(_TrimmedTitleSchema):
    """PATCH /api/cards/<id> body: title, description, and/or assignee_id (R6.4, R6.5)."""

    title = fields.String(validate=validate.Length(min=1, max=200))
    description = fields.String(allow_none=True, validate=validate.Length(max=5000))
    assignee_id = fields.UUID(allow_none=True)

    @validates_schema
    def require_one_field(self, data: dict, **kwargs) -> None:
        if not data:
            raise ValidationError(
                'At least one of title, description, or assignee_id is required.'
            )


class CardPositionSchema(Schema):
    """PATCH /api/cards/<id>/position body (R7.1, R7.2)."""

    class Meta:
        unknown = RAISE

    column_id = fields.UUID(required=True)
    order = fields.Float(
        required=True,
        validate=validate.Range(min=0, min_inclusive=False),
    )


class CardListQuerySchema(Schema):
    """GET /api/cards query parameters: `q`, `assignee=me`, optional `board_id` (R10, R18)."""

    class Meta:
        unknown = RAISE

    @pre_load
    def trim_query(self, data, **kwargs):
        if isinstance(data, dict) and isinstance(data.get('q'), str):
            data = {**data, 'q': data['q'].strip()}
        return data

    q = fields.String(validate=validate.Length(min=1, max=100))
    assignee = fields.String(validate=validate.OneOf(['me']))
    board_id = fields.UUID()

    @validates_schema
    def require_q_or_assignee(self, data: dict, **kwargs) -> None:
        if 'q' not in data and 'assignee' not in data:
            raise ValidationError('At least one of q or assignee is required.')


class _AssigneeSchema(Schema):
    """Nested assignee shape in card output."""

    id = fields.UUID()
    name = fields.String()
    username = fields.String()


class CardSchema(Schema):
    """Card output payload (R4 Validation Rules, R6)."""

    id = fields.UUID()
    title = fields.String()
    description = fields.String(allow_none=True)
    order = fields.Float()
    column_id = fields.UUID()
    assignee_id = fields.UUID(allow_none=True)
    assignee = fields.Nested(_AssigneeSchema, allow_none=True)
    created_by_id = fields.UUID()
    completed_at = fields.DateTime(allow_none=True)
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class CardListItemSchema(Schema):
    """Card list item shape for search and My Tasks (R10, R18)."""

    id = fields.UUID()
    title = fields.String()
    order = fields.Float()
    column_id = fields.UUID()
    column_name = fields.String()
    board_id = fields.UUID()
    board_name = fields.String()
    assignee_id = fields.UUID(allow_none=True)
    assignee = fields.Nested(_AssigneeSchema, allow_none=True)


class CardMoveResultSchema(Schema):
    """PATCH /api/cards/<id>/position response (R7.1)."""

    card = fields.Nested(CardSchema)
    rebalanced = fields.Boolean()
