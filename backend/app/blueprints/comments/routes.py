"""Comments routes – handler bodies ≤5 lines, no logic (BE-02)."""
from flask import request

from app.blueprints.comments import comments_bp
from app.blueprints.comments.schema import (
    CommentCreateSchema,
    CommentSchema,
    CommentUpdateSchema,
)
from app.blueprints.comments.service import (
    create_comment_service,
    delete_comment_service,
    list_comments_service,
    update_comment_service,
)
from app.utils.auth import board_access_required, token_required
from app.utils.responses import success


@comments_bp.route('/cards/<card_id>/comments', methods=['POST'])
@token_required
def create_comment_route(current_user, card_id: str):
    data = CommentCreateSchema().load(request.get_json(silent=True) or {})
    comment = create_comment_service(card_id, data, current_user.id)
    return success(CommentSchema().dump(comment), 201)


@comments_bp.route('/cards/<card_id>/comments', methods=['GET'])
@board_access_required(allow_guest_read=True)
def list_comments_route(access, card_id: str):
    comments = list_comments_service(card_id)
    return success(CommentSchema(many=True).dump(comments))


@comments_bp.route('/comments/<comment_id>', methods=['PATCH'])
@token_required
def update_comment_route(current_user, comment_id: str):
    data = CommentUpdateSchema().load(request.get_json(silent=True) or {})
    comment = update_comment_service(comment_id, data, current_user.id)
    return success(CommentSchema().dump(comment))


@comments_bp.route('/comments/<comment_id>', methods=['DELETE'])
@token_required
def delete_comment_route(current_user, comment_id: str):
    return success(delete_comment_service(comment_id, current_user.id))
