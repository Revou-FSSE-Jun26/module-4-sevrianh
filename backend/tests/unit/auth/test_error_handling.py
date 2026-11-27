"""Global error handler, JWT callbacks, structured logs and health route (BE-11, BE-12, BE-13)."""
import json
import logging
from datetime import timedelta

import pytest
from flask_jwt_extended import create_access_token, jwt_required
from marshmallow import ValidationError

from app import create_app
from app.exceptions import CardNotFoundException


def _service_boom():
    raise RuntimeError('secret internals')


@pytest.fixture
def app():
    app = create_app()
    app.config.update(TESTING=True, PROPAGATE_EXCEPTIONS=False)

    @app.get('/test/protected')
    @jwt_required()
    def protected_route():
        return {'data': 'ok'}

    @app.get('/test/boom')
    def boom_route():
        _service_boom()

    @app.get('/test/not-found')
    def not_found_route():
        raise CardNotFoundException()

    @app.get('/test/invalid')
    def invalid_route():
        raise ValidationError({'title': ['Missing data for required field.']})

    return app


@pytest.fixture
def client(app):
    return app.test_client()


def _assert_envelope_error(response, status):
    assert response.status_code == status
    body = response.get_json()
    assert set(body) == {'error'}
    assert isinstance(body['error'], str) and body['error']


def test_missing_token_is_401_envelope(client):
    _assert_envelope_error(client.get('/test/protected'), 401)


def test_malformed_token_is_401_not_422(client):
    response = client.get('/test/protected', headers={'Authorization': 'Bearer not-a-jwt'})
    _assert_envelope_error(response, 401)


def test_expired_token_is_401_envelope(app, client):
    with app.app_context():
        token = create_access_token(identity='u1', expires_delta=timedelta(seconds=-10))
    response = client.get('/test/protected', headers={'Authorization': f'Bearer {token}'})
    _assert_envelope_error(response, 401)


def test_valid_token_passes(app, client):
    with app.app_context():
        token = create_access_token(identity='u1')
    response = client.get('/test/protected', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200


def test_unknown_url_is_json_404(client):
    response = client.get('/api/does-not-exist')
    assert response.is_json
    assert response.status_code == 404
    assert response.get_json() == {'error': 'Not found'}


def test_unsupported_method_is_json_405(client):
    response = client.post('/api/health')
    _assert_envelope_error(response, 405)


def test_app_exception_uses_its_status_and_message(client):
    response = client.get('/test/not-found')
    assert response.status_code == 404
    assert response.get_json() == {'error': 'Not found or access denied'}


def test_validation_error_is_400_with_normalized_string(client):
    response = client.get('/test/invalid')
    assert response.status_code == 400
    assert response.get_json() == {'error': 'title: Missing data for required field.'}


def test_unexpected_exception_is_500_without_traceback(client):
    response = client.get('/test/boom')
    assert response.status_code == 500
    assert response.get_json() == {'error': 'Internal server error'}
    assert 'Traceback' not in response.get_data(as_text=True)


def test_log_record_has_exactly_four_fields_and_levels(client, caplog):
    with caplog.at_level(logging.INFO, logger='sevy'):
        client.get('/test/not-found')
        client.get('/test/boom')
    records = [r for r in caplog.records if r.name == 'sevy']
    assert len(records) == 2
    for record in records:
        assert set(json.loads(record.getMessage())) == {
            'level', 'endpoint', 'error_type', 'user_id'}
    warning, err = (json.loads(r.getMessage()) for r in records)
    assert warning['level'] == 'WARNING'
    assert warning['error_type'] == 'CardNotFoundException'
    assert warning['endpoint'] == 'not_found_route'
    assert warning['user_id'] is None
    assert err['level'] == 'ERROR'
    assert err['error_type'] == 'RuntimeError'


def test_log_contains_user_id_for_valid_token_and_no_token_text(app, client, caplog):
    with app.app_context():
        token = create_access_token(identity='user-123')
    with caplog.at_level(logging.INFO, logger='sevy'):
        client.get('/test/not-found', headers={'Authorization': f'Bearer {token}'})
    record = next(r for r in caplog.records if r.name == 'sevy')
    assert json.loads(record.getMessage())['user_id'] == 'user-123'
    assert token not in record.getMessage()


def test_health_returns_200_ok(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.get_json() == {'data': {'status': 'ok'}}
