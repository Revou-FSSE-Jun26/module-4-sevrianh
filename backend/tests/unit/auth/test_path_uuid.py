"""UUID path parameter validation across all ID routes (T-50)."""
import re

import pytest

from app.utils.auth import issue_access_token
from tests.unit.auth.test_route_inventory import ROUTES

ID_ROUTES = sorted(
    (method, rule) for method, rule in ROUTES if '<' in rule
)


def _bad_path(rule: str) -> str:
    return re.sub(r'<[^>]+>', 'not-a-uuid', rule)


@pytest.mark.parametrize('method,rule', ID_ROUTES)
def test_non_uuid_path_id_returns_400(client, factory, method, rule):
    user = factory.user()
    headers = {'Authorization': f'Bearer {issue_access_token(str(user.id))}'}
    resp = client.open(_bad_path(rule), method=method, headers=headers, json={})
    assert resp.status_code == 400
    body = resp.get_json()
    assert set(body.keys()) == {'error'}
    assert isinstance(body['error'], str) and body['error']
