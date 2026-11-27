from flask import request

from app.blueprints.auth import auth_bp
from app.blueprints.auth.schema import LoginSchema, RegisterSchema, UserSchema
from app.blueprints.auth.service import login_service, register_service
from app.utils.responses import success


@auth_bp.post('/auth/register')
def register_route():
    data = RegisterSchema().load(request.get_json(silent=True))
    user = register_service(data)
    return success(UserSchema().dump(user), 201)


@auth_bp.post('/auth/login')
def login_route():
    data = LoginSchema().load(request.get_json(silent=True))
    return success(login_service(data))
