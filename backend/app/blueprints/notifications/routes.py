"""Notifications routes – handler bodies ≤5 lines, no logic (BE-02)."""
from flask import request

from app.blueprints.notifications import notifications_bp
from app.blueprints.notifications.schema import (
    NotificationListSchema,
    NotificationQuerySchema,
    NotificationSchema,
)
from app.blueprints.notifications.service import (
    list_notifications_service,
    mark_notification_read_service,
)
from app.utils.auth import token_required
from app.utils.responses import success


@notifications_bp.route('/notifications', methods=['GET'])
@token_required
def list_notifications_route(current_user):
    query = NotificationQuerySchema().load(request.args.to_dict())
    page = list_notifications_service(current_user.id, query)
    return success(NotificationListSchema().dump(page))


@notifications_bp.route('/notifications/<notification_id>/read', methods=['PATCH'])
@token_required
def mark_notification_read_route(current_user, notification_id: str):
    notification = mark_notification_read_service(notification_id, current_user.id)
    return success(NotificationSchema().dump(notification))
