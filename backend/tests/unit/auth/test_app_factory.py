"""App factory integration checks (task 14.1)."""


def test_app_factory_registers_health_and_eight_blueprints(app):
    assert 'health.health_route' in app.view_functions
    for blueprint in (
        'analytics', 'auth', 'boards', 'cards', 'columns',
        'comments', 'notifications', 'users',
    ):
        assert any(view.startswith(f'{blueprint}.') for view in app.view_functions)


def test_health_has_server_duration_header(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.get_json() == {'data': {'status': 'ok'}}
    assert float(response.headers['X-Server-Duration-Ms']) >= 0
