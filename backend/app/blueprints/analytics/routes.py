"""Analytics routes – handler bodies ≤5 lines, no logic (BE-02)."""
from flask import request

from app.blueprints.analytics import analytics_bp
from app.blueprints.analytics.schema import AnalyticsQuerySchema
from app.blueprints.analytics.service import get_board_analytics_service
from app.utils.auth import board_access_required
from app.utils.responses import success


@analytics_bp.route('/boards/<board_id>/analytics', methods=['GET'])
@board_access_required(allow_guest_read=False)
def get_board_analytics_route(access, board_id: str):
    query = AnalyticsQuerySchema().load(request.args.to_dict())
    return success(get_board_analytics_service(board_id, query, access.user.id))
