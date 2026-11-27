from flask import Blueprint

boards_bp = Blueprint('boards', __name__, url_prefix='/api')

from app.blueprints.boards import routes  # noqa: E402,F401
