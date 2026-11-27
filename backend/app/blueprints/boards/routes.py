from flask import request

from app.blueprints.boards import boards_bp
from app.blueprints.boards.schema import (
    BoardCreateSchema,
    BoardDetailSchema,
    BoardSchema,
    BoardUpdateSchema,
    InviteLinkCreateSchema,
    InviteLinkSchema,
    MemberAddSchema,
    MemberRoleUpdateSchema,
    MemberSchema,
)
from app.blueprints.boards.service import (
    add_team_member_service,
    create_board_service,
    create_invite_link_service,
    delete_board_service,
    get_board_service,
    list_boards_service,
    list_team_members_service,
    remove_team_member_service,
    revoke_invite_link_service,
    update_board_service,
    update_team_member_role_service,
)
from app.models import UserEntity
from app.utils.auth import Access, board_access_required, token_required
from app.utils.responses import success


@boards_bp.route('/boards', methods=['POST'])
@token_required
def create_board_route(current_user: UserEntity):
    data = BoardCreateSchema().load(request.get_json(silent=True) or {})
    board = create_board_service(current_user.id, data)
    return success(BoardSchema().dump(board), 201)


@boards_bp.route('/boards', methods=['GET'])
@token_required
def list_boards_route(current_user: UserEntity):
    return success(BoardSchema(many=True).dump(list_boards_service(current_user.id)))


@boards_bp.route('/boards/<board_id>', methods=['GET'])
@board_access_required(allow_guest_read=True)
def get_board_route(access: Access, board_id: str):
    return success(BoardDetailSchema().dump(get_board_service(board_id, access)))


@boards_bp.route('/boards/<board_id>', methods=['PATCH'])
@token_required
def update_board_route(current_user: UserEntity, board_id: str):
    data = BoardUpdateSchema().load(request.get_json(silent=True) or {})
    return success(BoardSchema().dump(update_board_service(board_id, current_user.id, data)))


@boards_bp.route('/boards/<board_id>', methods=['DELETE'])
@token_required
def delete_board_route(current_user: UserEntity, board_id: str):
    return success(delete_board_service(board_id, current_user.id))


@boards_bp.route('/boards/<board_id>/invite-links', methods=['POST'])
@token_required
def create_invite_link_route(current_user: UserEntity, board_id: str):
    InviteLinkCreateSchema().load(request.get_json(silent=True) or {})
    link = create_invite_link_service(board_id, current_user.id)
    return success(InviteLinkSchema().dump(link), 201)


@boards_bp.route('/boards/<board_id>/invite-links/<invite_id>', methods=['DELETE'])
@token_required
def revoke_invite_link_route(current_user: UserEntity, board_id: str, invite_id: str):
    return success(revoke_invite_link_service(board_id, current_user.id, invite_id))


@boards_bp.route('/boards/<board_id>/members', methods=['POST'])
@token_required
def add_team_member_route(current_user: UserEntity, board_id: str):
    data = MemberAddSchema().load(request.get_json(silent=True) or {})
    member = add_team_member_service(board_id, current_user.id, data)
    return success(MemberSchema().dump(member), 201)


@boards_bp.route('/boards/<board_id>/members', methods=['GET'])
@token_required
def list_team_members_route(current_user: UserEntity, board_id: str):
    members = list_team_members_service(board_id, current_user.id)
    return success(MemberSchema(many=True).dump(members))


@boards_bp.route('/boards/<board_id>/members/<user_id>', methods=['PATCH'])
@token_required
def update_team_member_role_route(current_user: UserEntity, board_id: str, user_id: str):
    data = MemberRoleUpdateSchema().load(request.get_json(silent=True) or {})
    member = update_team_member_role_service(board_id, current_user.id, user_id, data)
    return success(MemberSchema().dump(member))


@boards_bp.route('/boards/<board_id>/members/<user_id>', methods=['DELETE'])
@token_required
def remove_team_member_route(current_user: UserEntity, board_id: str, user_id: str):
    return success(remove_team_member_service(board_id, current_user.id, user_id))
