"""PostgreSQL rebalance and concurrency tests for Cards (BE-14, R7.8, R7.14, R15.3-4)."""
from concurrent.futures import ThreadPoolExecutor

from app.blueprints.cards import service as svc
from app.exceptions import OrderConflictError
from app.extensions import db
from app.models import CardEntity
from app.utils.ordering import MIN_GAP, ORDER_STEP, has_small_gap


def test_move_card_rebalances_50_siblings_on_postgres(world, factory):
    cards = [
        factory.card(world.todo, world.member, title=f'C{i}', order=ORDER_STEP * (i + 1))
        for i in range(50)
    ]
    factory.session.commit()

    # Move last card into a sub-MIN_GAP slot just after cards[0] (1024.0)
    mover = cards[-1]
    res = svc.move_card_service(
        mover.id,
        {'column_id': world.todo.id, 'order': 1024.0 + MIN_GAP / 2},
        world.member.id,
    )
    assert res['rebalanced'] is True
    assert res['card'].order == 2048.0

    active = (
        db.session.query(CardEntity)
        .filter(CardEntity.column_id == world.todo.id, CardEntity.deleted_at.is_(None))
        .order_by(CardEntity.order.asc())
        .all()
    )
    expected_ids = [cards[0].id, mover.id] + [c.id for c in cards[1:-1]]
    orders = [c.order for c in active]
    assert [c.id for c in active] == expected_ids
    assert orders == [ORDER_STEP * (i + 1) for i in range(50)]
    assert not has_small_gap(orders)


def test_concurrent_moves_and_edits_serialize_cleanly(app, world, factory):
    c1 = factory.card(world.todo, world.member, title='C1', order=1024.0)
    c2 = factory.card(world.todo, world.member, title='C2', order=2048.0)
    factory.session.commit()

    def _move(card_id, target_order):
        with app.app_context():
            try:
                svc.move_card_service(
                    card_id,
                    {'column_id': world.done.id, 'order': target_order},
                    world.member.id,
                )
                return 'ok'
            except OrderConflictError:
                return 'conflict'

    with ThreadPoolExecutor(max_workers=2) as pool:
        f1 = pool.submit(_move, c1.id, 1024.0)
        f2 = pool.submit(_move, c2.id, 1024.0)
        outcomes = sorted([f1.result(), f2.result()])
    assert outcomes == ['conflict', 'ok']

    def _edit(new_title):
        with app.app_context():
            svc.update_card_service(c1.id, {'title': new_title}, world.member.id)

    with ThreadPoolExecutor(max_workers=2) as pool:
        e1 = pool.submit(_edit, 'Version A')
        e2 = pool.submit(_edit, 'Version B')
        e1.result()
        e2.result()

    db.session.expire_all()
    assert db.session.get(CardEntity, c1.id).title in ('Version A', 'Version B')
