"""API-level core flow (task 14.3)."""


def test_register_login_board_column_card_move_comment_notification_delete_analytics(client):
    suffix = 'core-flow'
    register = client.post('/api/auth/register', json={
        'name': 'Core User', 'username': 'core_user',
        'email': f'{suffix}@example.com', 'password': 'password123',
    })
    assert register.status_code == 201

    login = client.post('/api/auth/login', json={
        'email': f'{suffix}@example.com', 'password': 'password123',
    })
    assert login.status_code == 200
    token = login.get_json()['data']['access_token']
    auth = {'Authorization': f'Bearer {token}'}

    board = client.post('/api/boards', json={'name': 'Core Board'}, headers=auth)
    assert board.status_code == 201
    board_id = board.get_json()['data']['id']

    todo = client.post(f'/api/boards/{board_id}/columns', json={'name': 'To Do'}, headers=auth)
    done = client.post(f'/api/boards/{board_id}/columns', json={'name': 'Done', 'is_done': True}, headers=auth)
    assert todo.status_code == 201 and done.status_code == 201
    todo_id = todo.get_json()['data']['id']
    done_id = done.get_json()['data']['id']

    card = client.post(f'/api/columns/{todo_id}/cards', json={'title': 'Core Card'}, headers=auth)
    assert card.status_code == 201
    card_id = card.get_json()['data']['id']

    moved = client.patch(
        f'/api/cards/{card_id}/position',
        json={'column_id': done_id, 'order': 1024.0}, headers=auth,
    )
    assert moved.status_code == 200
    assert moved.get_json()['data']['card']['completed_at'] is not None

    comment = client.post(
        f'/api/cards/{card_id}/comments', json={'content': 'Flow comment'}, headers=auth,
    )
    assert comment.status_code == 201

    notifications = client.get('/api/notifications', headers=auth)
    assert notifications.status_code == 200

    deleted = client.delete(f'/api/cards/{card_id}', headers=auth)
    assert deleted.status_code == 200

    analytics = client.get(f'/api/boards/{board_id}/analytics', headers=auth)
    assert analytics.status_code == 200
