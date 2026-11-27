from flask import request

from app.blueprints.columns import columns_bp
from app.blueprints.columns.schema import (
    ColumnCreateSchema,
    ColumnReorderResultSchema,
    ColumnReorderSchema,
    ColumnSchema,
    ColumnUpdateSchema,
)
from app.blueprints.columns.service import (
    create_column_service,
    delete_column_service,
    reorder_column_service,
    update_column_service,
)
from app.utils.auth import token_required
from app.utils.responses import success


@columns_bp.route('/boards/<board_id>/columns', methods=['POST'])
@token_required
def create_column_route(current_user, board_id: str):
    data = ColumnCreateSchema().load(request.get_json(silent=True) or {})
    column = create_column_service(board_id, data, current_user.id)
    return success(ColumnSchema().dump(column), 201)


@columns_bp.route('/columns/<column_id>', methods=['PATCH'])
@token_required
def update_column_route(current_user, column_id: str):
    data = ColumnUpdateSchema().load(request.get_json(silent=True) or {})
    column = update_column_service(column_id, data, current_user.id)
    return success(ColumnSchema().dump(column))


@columns_bp.route('/columns/<column_id>', methods=['DELETE'])
@token_required
def delete_column_route(current_user, column_id: str):
    return success(delete_column_service(column_id, current_user.id))


@columns_bp.route('/boards/<board_id>/columns/reorder', methods=['PATCH'])
@token_required
def reorder_column_route(current_user, board_id: str):
    data = ColumnReorderSchema().load(request.get_json(silent=True) or {})
    result = reorder_column_service(board_id, data, current_user.id)
    return success(ColumnReorderResultSchema().dump(result))
