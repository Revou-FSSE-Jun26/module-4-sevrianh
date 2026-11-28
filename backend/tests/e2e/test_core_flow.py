"""API-level end-to-end core flow test (T-51)."""


def _data(resp, expected_status: int):
    assert resp.status_code == expected_status, resp.get_json()
    body = resp.get_json()
    assert set(body.keys()) == {'data'}
    return body['data']


def test_core_api_flow(client):
    # 1. Register two users (admin and teammate) and login
    _data(client.post('/api/auth/register', json={
        'name': 'Admin User',
        'username': 'e2e_admin',
        'email': 'e2e_admin@example.com',
        'password': 'password123',
    }), 201)
    _data(client.post('/api/auth/register', json={
        'name': 'Mate User',
        'username': 'e2e_mate',
        'email': 'e2e_mate@example.com',
        'password': 'password123',
    }), 201)

    admin_login = _data(client.post('/api/auth/login', json={
        'email': 'e2e_admin@example.com',
        'password': 'password123',
    }), 200)
    mate_login = _data(client.post('/api/auth/login', json={
        'email': 'e2e_mate@example.com',
        'password': 'password123',
    }), 200)

    admin_h = {'Authorization': f"Bearer {admin_login['access_token']}"}
    mate_h = {'Authorization': f"Bearer {mate_login['access_token']}"}

    # 2. Create board & invite teammate
    board = _data(client.post('/api/boards', json={'name': 'E2E Board'}, headers=admin_h), 201)
    board_id = board['id']
    _data(client.post(f'/api/boards/{board_id}/members', json={
        'email': 'e2e_mate@example.com',
        'role': 'member',
    }, headers=admin_h), 201)

    # 3. Add "To Do" and "Done" columns
    todo_col = _data(client.post(f'/api/boards/{board_id}/columns', json={
        'name': 'To Do', 'is_done': False,
    }, headers=admin_h), 201)
    done_col = _data(client.post(f'/api/boards/{board_id}/columns', json={
        'name': 'Done', 'is_done': True,
    }, headers=admin_h), 201)

    # 4. Create card in "To Do" and move to "Done"
    card = _data(client.post(f"/api/columns/{todo_col['id']}/cards", json={
        'title': 'Ship V1',
        'assignee_id': mate_login['user']['id'],
    }, headers=admin_h), 201)
    assert card['completed_at'] is None

    moved = _data(client.patch(f"/api/cards/{card['id']}/position", json={
        'column_id': done_col['id'],
        'order': 1000,
    }, headers=admin_h), 200)
    assert moved['card']['completed_at'] is not None

    # 5. Comment with @mention and read notification as teammate
    _data(client.post(f"/api/cards/{card['id']}/comments", json={
        'content': 'Great job @e2e_mate!',
    }, headers=admin_h), 201)

    notes = _data(client.get('/api/notifications', headers=mate_h), 200)
    assert notes['unread_count'] == 1
    note_id = notes['items'][0]['id']
    read_note = _data(client.patch(f'/api/notifications/{note_id}/read', headers=mate_h), 200)
    assert read_note['is_read'] is True

    # 6. Soft delete card and check analytics as Admin
    _data(client.delete(f"/api/cards/{card['id']}", headers=admin_h), 200)
    analytics = _data(client.get(f'/api/boards/{board_id}/analytics', headers=admin_h), 200)
    assert analytics['completed_this_week'] == 0
    assert sum(c['count'] for c in analytics['cards_per_column']) == 0
