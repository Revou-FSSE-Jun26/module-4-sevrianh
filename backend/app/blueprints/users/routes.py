from flask import request

from app.blueprints.users import users_bp
from app.blueprints.users.schema import UserSchema, UserUpdateSchema
from app.blueprints.users.service import get_current_user_service, update_current_user_service
from app.models import UserEntity
from app.utils.auth import token_required
from app.utils.responses import success


@users_bp.get('/users/me')
@token_required
def get_current_user_route(current_user: UserEntity):
    return success(UserSchema().dump(get_current_user_service(current_user)))


@users_bp.patch('/users/me')
@token_required
def update_current_user_route(current_user: UserEntity):
    data = UserUpdateSchema().load(request.get_json(silent=True))
    user = update_current_user_service(current_user, data)
    return success(UserSchema().dump(user))
