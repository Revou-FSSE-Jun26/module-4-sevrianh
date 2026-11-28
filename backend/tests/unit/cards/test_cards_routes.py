"""Cards route tests: 201/200/400/401/403/404/409, soft-deleted 404, search & My Tasks."""
import uuid

from app.blueprints.boards.service import create_invite_link_service
from app.extensions import db
from app.models import CardEntity
from app.utils.time import utc_now

GENERIC = 'Not found or access denied'


def _error(res, status, message=None):
    assert res.status_code == status
    body = res.get_json()
    assert set(body) == {'error'} and isinstance(body['error'], str) and body['error']
    if message is not None:
        assert body['error'] == message


# ---- POST /api/columns/<id>/cards ----------------------------------------------------------

def test_create_card_route_201_and_errors(client, world, auth):
    url = f'/api/columns/{world.todo.id}/cards'
    res = client.post(
        url,
        json={'title': '  Task 1  ', 'description': 'Body', 'assignee_id': str(world.member.id)},
        headers=auth(world.member),
    )
    assert res.status_code == 201
    data = res.get_json()['data']
    assert data['title'] == 'Task 1' and data['order'] == 1024.0
    assert data['assignee']['username'] == world.member.username

    _error(client.post(url, json={'title': 'A'}), 401)
    _error(client.post(url, json={'title': 'A'}, headers=auth(world.outsider)), 403, GENERIC)
    _error(client.post(f'/api/columns/{uuid.uuid4()}/cards', json={'title': 'A'},
                       headers=auth(world.admin)), 404, GENERIC)
    _error(client.post(url, json={'title': '   '}, headers=auth(world.admin)), 400)
    _error(client.post(url, json={'title': 'A', 'extra': 1}, headers=auth(world.admin)), 400)
    _error(client.post(url, json={'title': 'A', 'assignee_id': str(world.outsider.id)},
                       headers=auth(world.admin)), 400, 'Assignee must be a Team member')


# ---- PATCH & DELETE /api/cards/<id> --------------------------------------------------------

def test_update_and_delete_card_routes(client, world, auth, factory):
    card = factory.card(world.todo, world.member, title='Init')
    factory.session.commit()
    url = f'/api/cards/{card.id}'

    res = client.patch(url, json={'title': '  Updated  '}, headers=auth(world.member2))
    assert res.status_code == 200 and res.get_json()['data']['title'] == 'Updated'

    for bad_body in [{}, {'title': '  '}, {'column_id': str(world.done.id)},
                     {'order': 512.0}, {'deleted_at': '2026-01-01'}, {'completed_at': None}]:
        _error(client.patch(url, json=bad_body, headers=auth(world.admin)), 400)

    _error(client.delete(url, headers=auth(world.member2)), 403, 'Admin access required')
    del_res = client.delete(url, headers=auth(world.member))
    assert del_res.status_code == 200 and del_res.get_json()['data'] == {'id': str(card.id)}

    # Soft-deleted card returns 404 generic on every Card-ID route, even for outsider
    _error(client.patch(url, json={'title': 'X'}, headers=auth(world.outsider)), 404, GENERIC)
    _error(client.delete(url, headers=auth(world.outsider)), 404, GENERIC)
    _error(client.patch(f'{url}/position',
                        json={'column_id': str(world.done.id), 'order': 1024.0},
                        headers=auth(world.outsider)), 404, GENERIC)


# ---- PATCH /api/cards/<id>/position --------------------------------------------------------

def test_move_card_route_200_400_409(client, world, auth, factory):
    c1 = factory.card(world.todo, world.member, order=1024.0)
    c2 = factory.card(world.todo, world.member, order=2048.0)
    factory.session.commit()

    url = f'/api/cards/{c1.id}/position'
    _error(client.patch(url, json={'column_id': str(world.todo.id), 'order': 2048.0},
                        headers=auth(world.member)), 409)
    _error(client.patch(url, json={'column_id': str(world.col_b.id), 'order': 512.0},
                        headers=auth(world.member)), 400)
    _error(client.patch(url, json={'column_id': str(world.done.id), 'order': 0},
                        headers=auth(world.member)), 400)

    res = client.patch(url, json={'column_id': str(world.done.id), 'order': 1024.0},
                       headers=auth(world.member))
    assert res.status_code == 200
    body = res.get_json()['data']
    assert body['rebalanced'] is False and body['card']['completed_at'] is not None
    assert db.session.get(CardEntity, c2.id).order == 2048.0


# ---- GET /api/cards ------------------------------------------------------------------------

def test_list_cards_route_search_my_tasks_and_guest_401(client, world, auth, factory):
    c1 = factory.card(world.todo, world.member, title='Alpha Task', assignee=world.member)
    factory.card(world.todo, world.member, title='Deleted Alpha',
                 assignee=world.member, order=2048.0, deleted_at=utc_now())
    factory.session.commit()
    link = create_invite_link_service(world.board.id, world.admin.id)

    # Guest with invite token only gets 401 on GET /api/cards
    _error(client.get('/api/cards?q=alpha', headers={'X-Invite-Token': link['token']}), 401)

    for bad_qs in ['', '?q=%20%20', f'?q={"a" * 101}', '?assignee=other', '?extra=1']:
        _error(client.get(f'/api/cards{bad_qs}', headers=auth(world.member)), 400)

    res_q = client.get('/api/cards?q=ALPHA', headers=auth(world.member))
    assert res_q.status_code == 200
    assert [item['id'] for item in res_q.get_json()['data']] == [str(c1.id)]

    res_me = client.get('/api/cards?assignee=me', headers=auth(world.member))
    assert res_me.status_code == 200
    assert [item['id'] for item in res_me.get_json()['data']] == [str(c1.id)]

    _error(client.get(f'/api/cards?q=a&board_id={uuid.uuid4()}',
                      headers=auth(world.member)), 404, GENERIC)
    _error(client.get(f'/api/cards?q=a&board_id={world.board_b.id}',
                      headers=auth(world.member)), 403, GENERIC)
