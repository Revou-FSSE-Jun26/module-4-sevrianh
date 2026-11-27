"""Columns input and output schemas (BE-05, BE-06)."""
from marshmallow import RAISE, Schema, ValidationError, fields, pre_load, validate, validates_schema


class _TrimmedNameSchema(Schema):
    class Meta:
        unknown = RAISE

    @pre_load
    def trim_name(self, data, **kwargs):
        if isinstance(data, dict) and isinstance(data.get('name'), str):
            data = {**data, 'name': data['name'].strip()}
        return data


class ColumnCreateSchema(_TrimmedNameSchema):
    """POST /api/boards/<id>/columns body (R5.1, R5.4)."""

    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    is_done = fields.Boolean(load_default=False)


class ColumnUpdateSchema(_TrimmedNameSchema):
    """PATCH /api/columns/<id> body: `name` and/or `is_done`, at least one (R5.5)."""

    name = fields.String(validate=validate.Length(min=1, max=100))
    is_done = fields.Boolean()

    @validates_schema
    def require_one_field(self, data: dict, **kwargs) -> None:
        if not data:
            raise ValidationError('At least one of name or is_done is required.')


class ColumnReorderSchema(Schema):
    """PATCH /api/boards/<id>/columns/reorder body (R5.6, R5.7)."""

    class Meta:
        unknown = RAISE

    column_id = fields.UUID(required=True)
    order = fields.Float(
        required=True,
        validate=validate.Range(min=0, min_inclusive=False),
    )


class ColumnSchema(Schema):
    """Column output payload (BE-06)."""

    id = fields.UUID()
    board_id = fields.UUID()
    name = fields.String()
    order = fields.Float()
    is_done = fields.Boolean()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class ColumnReorderResultSchema(Schema):
    """Reorder response payload: `{"column": {...}, "rebalanced": <bool>}` (BE-07)."""

    column = fields.Nested(ColumnSchema)
    rebalanced = fields.Boolean()
