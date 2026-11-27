"""Public health check (R20, F-12). Not a feature blueprint (ST-02)."""
from flask import Blueprint

from app.utils.responses import success

health_bp = Blueprint('health', __name__, url_prefix='/api')


@health_bp.get('/health')
def health_route():
    return success({'status': 'ok'})
