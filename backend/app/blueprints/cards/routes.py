"""Cards routes – handler bodies ≤5 lines, no logic (BE-02)."""
from flask import request

from app.blueprints.cards import cards_bp
from app.blueprints.cards.schema import (
    CardCreateSchema,
    CardListItemSchema,
    CardListQuerySchema,
    CardMoveResultSchema,
    CardPositionSchema,
    CardSchema,
    CardUpdateSchema,
)
from app.blueprints.cards.service import (
    create_card_service,
    delete_card_service,
    list_cards_service,
    move_card_service,
    update_card_service,
)
from app.utils.auth import token_required
from app.utils.responses import success


@cards_bp.route('/columns/<column_id>/cards', methods=['POST'])
@token_required
def create_card_route(current_user, column_id: str):
    data = CardCreateSchema().load(request.get_json(silent=True) or {})
    card = create_card_service(column_id, data, current_user.id)
    return success(CardSchema().dump(card), 201)


@cards_bp.route('/cards/<card_id>', methods=['PATCH'])
@token_required
def update_card_route(current_user, card_id: str):
    data = CardUpdateSchema().load(request.get_json(silent=True) or {})
    card = update_card_service(card_id, data, current_user.id)
    return success(CardSchema().dump(card))


@cards_bp.route('/cards/<card_id>', methods=['DELETE'])
@token_required
def delete_card_route(current_user, card_id: str):
    return success(delete_card_service(card_id, current_user.id))


@cards_bp.route('/cards/<card_id>/position', methods=['PATCH'])
@token_required
def move_card_route(current_user, card_id: str):
    data = CardPositionSchema().load(request.get_json(silent=True) or {})
    result = move_card_service(card_id, data, current_user.id)
    return success(CardMoveResultSchema().dump(result))


@cards_bp.route('/cards', methods=['GET'])
@token_required
def list_cards_route(current_user):
    query = CardListQuerySchema().load(request.args.to_dict())
    cards = list_cards_service(current_user.id, query)
    return success(CardListItemSchema(many=True).dump(cards))
