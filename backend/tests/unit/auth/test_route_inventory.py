"""Authoritative route inventory and CORS checks (task 14.2)."""

ROUTES = {
    ('POST', '/api/auth/register'), ('POST', '/api/auth/login'),
    ('POST', '/api/boards'), ('GET', '/api/boards'),
    ('GET', '/api/boards/<board_id>'), ('PATCH', '/api/boards/<board_id>'),
    ('DELETE', '/api/boards/<board_id>'),
    ('POST', '/api/boards/<board_id>/columns'),
    ('PATCH', '/api/columns/<column_id>'), ('DELETE', '/api/columns/<column_id>'),
    ('PATCH', '/api/boards/<board_id>/columns/reorder'),
    ('POST', '/api/columns/<column_id>/cards'),
    ('PATCH', '/api/cards/<card_id>'), ('DELETE', '/api/cards/<card_id>'),
    ('PATCH', '/api/cards/<card_id>/position'),
    ('POST', '/api/cards/<card_id>/comments'), ('GET', '/api/cards/<card_id>/comments'),
    ('PATCH', '/api/comments/<comment_id>'), ('DELETE', '/api/comments/<comment_id>'),
    ('GET', '/api/notifications'), ('PATCH', '/api/notifications/<notification_id>/read'),
    ('GET', '/api/boards/<board_id>/analytics'), ('GET', '/api/users/me'),
    ('PATCH', '/api/users/me'), ('GET', '/api/health'), ('GET', '/api/cards'),
    ('POST', '/api/boards/<board_id>/members'),
    ('DELETE', '/api/boards/<board_id>/members/<user_id>'),
    ('GET', '/api/boards/<board_id>/members'),
    ('PATCH', '/api/boards/<board_id>/members/<user_id>'),
    ('POST', '/api/boards/<board_id>/invite-links'),
    ('DELETE', '/api/boards/<board_id>/invite-links/<invite_id>'),
}


def test_route_inventory_matches_appendix_a(app):
    actual = set()
    for rule in app.url_map.iter_rules():
        if not rule.rule.startswith('/api/'):
            continue
        path = rule.rule
        for method in rule.methods - {'HEAD', 'OPTIONS'}:
            actual.add((method, path))
    assert actual == ROUTES


def test_foreign_origin_is_not_allowed(client):
    response = client.get('/api/health', headers={'Origin': 'https://evil.example'})
    assert 'Access-Control-Allow-Origin' not in response.headers
