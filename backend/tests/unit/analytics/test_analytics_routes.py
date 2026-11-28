"""Unit tests for analytics routes (T-46)."""
from app.blueprints.boards.service import create_invite_link_service
from app.utils.auth import issue_access_token


def _headers(user):
    return {'Authorization': f'Bearer {issue_access_token(str(user.id))}'}


def test_analytics_route_admin_success(client, factory):
    admin = factory.user()
    team = factory.team(owner=admin)
    factory.membership(team=team, user=admin, role='admin')
    board = factory.board(team=team)
    factory.column(board=board, name='Todo', order=1000)

    resp = client.get(f'/api/boards/{board.id}/analytics', headers=_headers(admin))
    assert resp.status_code == 200
    data = resp.get_json()['data']
    assert 'cards_per_column' in data
    assert 'completed_this_week' in data
    assert 'member_activity' in data
    assert 'activity_per_day' in data


def test_analytics_route_member_and_guest_forbidden(client, factory):
    admin = factory.user()
    member = factory.user()
    team = factory.team(owner=admin)
    factory.membership(team=team, user=admin, role='admin')
    factory.membership(team=team, user=member, role='member')
    board = factory.board(team=team)
    invite = create_invite_link_service(board.id, admin.id)

    resp_member = client.get(f'/api/boards/{board.id}/analytics', headers=_headers(member))
    assert resp_member.status_code == 403

    resp_guest = client.get(
        f'/api/boards/{board.id}/analytics',
        headers={'X-Invite-Token': invite['token']},
    )
    assert resp_guest.status_code == 403


def test_analytics_route_invalid_dates_400(client, factory):
    admin = factory.user()
    team = factory.team(owner=admin)
    factory.membership(team=team, user=admin, role='admin')
    board = factory.board(team=team)

    resp = client.get(
        f'/api/boards/{board.id}/analytics?start_date=2025-01-01',
        headers=_headers(admin),
    )
    assert resp.status_code == 400

    resp2 = client.get(
        f'/api/boards/{board.id}/analytics?start_date=not-a-date&end_date=2025-01-01',
        headers=_headers(admin),
    )
    assert resp2.status_code == 400
