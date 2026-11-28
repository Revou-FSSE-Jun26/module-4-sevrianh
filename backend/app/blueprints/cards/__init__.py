"""Cards Blueprint (R6, R7, R10, R18, R24)."""
from flask import Blueprint

cards_bp = Blueprint('cards', __name__, url_prefix='/api')

from app.blueprints.cards import routes  # noqa: E402,F401
