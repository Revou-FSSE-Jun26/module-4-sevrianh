"""Boards service tests: one success and one failure per service function (R28.1)."""
import uuid

import pytest
from sqlalchemy import event

from app.blueprints.boards import service as svc
from app.blueprints.boards.schema import BoardDetailSchema
from app.exceptions import (
    AdminAccessRequiredError, BoardNotFoundException, InviteLinkNotFoundException,
    LastAdminError, MemberAlreadyExistsError, MemberNotFoundException,
    TeamAccessDeniedError, UserNotFoundException,
)
from app.extensions import db
from app.models import (
    BoardColumnEntity, BoardEntity, CardEntity, InviteLinkEntity, TeamMembershipEntity,
)
from app.utils.auth import Access, hash_invite_token
from app.utils.time import utc_now


def test_require_team_member_service_returns_board_for_member(world):
    assert svc.require_team_member_service(world.board.id, world.member.id).id == world.board.id


def test_require_team_member_service_404_before_403(world):
    with pytest.raises(BoardNotFoundException):
        svc.require_team_member_service(uuid.uuid4(), world.outsider.id)
    with pytest.raises(TeamAccessDeniedError):
        svc.require_team_member_service(world.board.id, world.outsider.id)


def test_require_team_admin_service_distinguishes_member_and_non_member(world):
    assert svc.require_team_admin_service(world.board.id, world.admin.id).id == world.board.id
    with pytest.raises(AdminAccessRequiredError):
        svc.require_team_admin_service(world.board.id, world.member.id)
    with pytest.raises(TeamAccessDeniedError):
        svc.require_team_admin_service(world.board.id, world.outsider.id)


def test_create_board_service_uses_personal_team_when_team_id_omitted(world):
    board = svc.create_board_service(world.admin.id, {'name': 'New'})
    assert board.team_id == world.team.id and board.name == 'New'


def test_create_board_service_uses_given_team_for_admin(world):
    board = svc.create_board_service(world.admin_b.id, {'name': 'B2', 'team_id': world.team_b.id})
    assert board.team_id == world.team_b.id


def test_create_board_service_rejects_member_unknown_and_foreign_team(world):
    with pytest.raises(TeamAccessDeniedError):
        svc.create_board_service(world.member.id, {'name': 'x', 'team_id': world.team.id})
    with pytest.raises(TeamAccessDeniedError):
        svc.create_board_service(world.admin.id, {'name': 'x', 'team_id': uuid.uuid4()})
    with pytest.raises(TeamAccessDeniedError):
        svc.create_board_service(world.admin.id, {'name': 'x', 'team_id': world.team_b.id})


def test_create_board_service_without_personal_team_is_denied(factory):
    user = factory.user()
    factory.session.commit()
    with pytest.raises(TeamAccessDeniedError):
        svc.create_board_service(user.id, {'name': 'x'})


def test_list_boards_service_returns_own_team_boards_newest_first(world, factory):
    newer = factory.board(world.team, name='Newer')
    factory.session.commit()
    ids = [b.id for b in svc.list_boards_service(world.member.id)]
    assert ids == [newer.id, world.board.id]
    assert svc.list_boards_service(world.outsider.id) == []


def test_get_board_service_returns_columns_and_cards_in_order(world, factory):
    c2 = factory.column(world.board, order=2048.0)
    c1 = factory.column(world.board, order=1024.0)
    late = factory.card(c1, world.admin, order=2048.0)
    early = factory.card(c1, world.admin, order=1024.0)
    factory.card(c1, world.admin, deleted_at=utc_now())
    factory.session.commit()
    board = svc.get_board_service(world.board.id, Access(user=world.member, role='member'))
    assert [c.id for c in board.columns] == [c1.id, c2.id]
    assert [c.id for c in board.columns[0].cards] == [early.id, late.id]
    assert board.columns[1].cards == []


def test_get_board_service_rejects_missing_board(world):
    with pytest.raises(BoardNotFoundException):
        svc.get_board_service(uuid.uuid4(), Access(user=world.member, role='member'))


def _count_statements(fn):
    statements = []

    def before(conn, cursor, statement, *args):
        statements.append(statement)

    event.listen(db.engine, 'before_cursor_execute', before)
    try:
        fn()
    finally:
        event.remove(db.engine, 'before_cursor_execute', before)
    return statements


def _seed_columns_and_cards(factory, world, columns, cards_per_column):
    start = db.session.query(BoardColumnEntity).filter_by(board_id=world.board.id).count()
    for c in range(columns):
        col = factory.column(world.board, order=1024.0 * (start + c + 1))
        for n in range(cards_per_column):
            factory.card(col, world.admin, order=1024.0 * (n + 1),
                         assignee_id=world.member.id)
    factory.session.commit()


def test_get_board_service_query_budget_is_at_most_three_and_does_not_scale(world, factory):
    access = Access(user=world.member, role='member')

    def load():
        db.session.expire_all()
        board = svc.get_board_service(world.board.id, access)
        BoardDetailSchema().dump(board)

    _seed_columns_and_cards(factory, world, 1, 1)
    small = len(_count_statements(load))
    _seed_columns_and_cards(factory, world, 4, 10)  # now 5 Columns and 41 Cards
    col = db.session.query(BoardColumnEntity).order_by(BoardColumnEntity.order).first()
    for n in range(9):
        factory.card(col, world.admin, order=1024.0 * (n + 10), assignee_id=world.admin.id)
    factory.session.commit()
    assert db.session.query(BoardColumnEntity).count() == 5
    assert db.session.query(CardEntity).count() == 50
    large = len(_count_statements(load))
    assert large <= 3
    assert large == small


def test_update_board_service_renames_for_admin(world):
    assert svc.update_board_service(world.board.id, world.admin.id, {'name': 'Renamed'}).name \
        == 'Renamed'


def test_update_board_service_rejects_member_and_missing(world):
    with pytest.raises(AdminAccessRequiredError):
        svc.update_board_service(world.board.id, world.member.id, {'name': 'x'})
    with pytest.raises(BoardNotFoundException):
        svc.update_board_service(uuid.uuid4(), world.admin.id, {'name': 'x'})


def test_delete_board_service_removes_board_and_contents(world, factory):
    col = factory.column(world.board)
    factory.card(col, world.admin)
    factory.session.commit()
    board_id = world.board.id
    assert svc.delete_board_service(board_id, world.admin.id) == {'id': str(board_id)}
    assert db.session.get(BoardEntity, board_id) is None
    assert db.session.query(BoardColumnEntity).count() == 0
    assert db.session.query(CardEntity).count() == 0


def test_delete_board_service_rejects_member_and_keeps_board(world):
    with pytest.raises(AdminAccessRequiredError):
        svc.delete_board_service(world.board.id, world.member.id)
    assert db.session.get(BoardEntity, world.board.id) is not None


def test_add_team_member_service_adds_with_default_role(world):
    result = svc.add_team_member_service(
        world.board.id, world.admin.id, {'email': 'OUTSIDER@example.com'})
    assert result['user_id'] == world.outsider.id and result['role'] == 'member'


def test_add_team_member_service_admin_check_precedes_email_lookup(world):
    with pytest.raises(AdminAccessRequiredError):
        svc.add_team_member_service(world.board.id, world.member.id, {'email': 'no@x.com'})
    with pytest.raises(TeamAccessDeniedError):
        svc.add_team_member_service(world.board.id, world.outsider.id, {'email': 'no@x.com'})


def test_add_team_member_service_rejects_unknown_email_and_duplicate(world):
    with pytest.raises(UserNotFoundException):
        svc.add_team_member_service(world.board.id, world.admin.id, {'email': 'no@x.com'})
    with pytest.raises(MemberAlreadyExistsError):
        svc.add_team_member_service(world.board.id, world.admin.id, {'email': world.member.email})


def test_list_team_members_service_lists_members_for_member(world):
    rows = svc.list_team_members_service(world.board.id, world.member.id)
    assert {r['user_id'] for r in rows} == {
        world.admin.id, world.member.id, world.other_member.id}
    assert set(rows[0]) == {'user_id', 'name', 'username', 'role'}


def test_list_team_members_service_rejects_non_member(world):
    with pytest.raises(TeamAccessDeniedError):
        svc.list_team_members_service(world.board.id, world.outsider.id)


def test_update_team_member_role_service_promotes_member(world):
    result = svc.update_team_member_role_service(
        world.board.id, world.admin.id, world.member.id, {'role': 'admin'})
    assert result['role'] == 'admin'


def test_update_team_member_role_service_blocks_last_admin_demotion(world):
    with pytest.raises(LastAdminError):
        svc.update_team_member_role_service(
            world.board.id, world.admin.id, world.admin.id, {'role': 'member'})
    assert svc.require_team_admin_service(world.board.id, world.admin.id)


def test_update_team_member_role_service_allows_demotion_with_second_admin(world):
    svc.update_team_member_role_service(
        world.board.id, world.admin.id, world.member.id, {'role': 'admin'})
    result = svc.update_team_member_role_service(
        world.board.id, world.member.id, world.admin.id, {'role': 'member'})
    assert result['role'] == 'member'


def test_update_team_member_role_service_rejects_unknown_target_and_member_actor(world):
    with pytest.raises(MemberNotFoundException):
        svc.update_team_member_role_service(
            world.board.id, world.admin.id, world.outsider.id, {'role': 'admin'})
    with pytest.raises(AdminAccessRequiredError):
        svc.update_team_member_role_service(
            world.board.id, world.member.id, world.other_member.id, {'role': 'admin'})


def test_remove_team_member_service_clears_assignee_and_keeps_authored_card(world, factory):
    col = factory.column(world.board)
    authored = factory.card(col, world.member, assignee_id=world.member.id)
    factory.session.commit()
    result = svc.remove_team_member_service(world.board.id, world.admin.id, world.member.id)
    assert result == {'id': str(world.member.id)}
    card = db.session.get(CardEntity, authored.id)
    assert card.assignee_id is None and card.created_by_id == world.member.id
    assert svc.list_team_members_service(world.board.id, world.admin.id).__len__() == 2


def test_remove_team_member_service_rejects_last_admin_unknown_and_member_actor(world):
    with pytest.raises(LastAdminError):
        svc.remove_team_member_service(world.board.id, world.admin.id, world.admin.id)
    with pytest.raises(MemberNotFoundException):
        svc.remove_team_member_service(world.board.id, world.admin.id, world.outsider.id)
    with pytest.raises(AdminAccessRequiredError):
        svc.remove_team_member_service(world.board.id, world.member.id, world.other_member.id)
    assert db.session.query(TeamMembershipEntity).filter_by(team_id=world.team.id).count() == 3


def test_create_invite_link_service_stores_only_the_hash(world):
    result = svc.create_invite_link_service(world.board.id, world.admin.id)
    assert set(result) == {'id', 'board_id', 'token', 'created_at'}
    assert len(result['token']) >= 43  # token_urlsafe(32)
    link = db.session.get(InviteLinkEntity, result['id'])
    assert link.token_hash == hash_invite_token(result['token'])
    assert link.token_hash != result['token']


def test_create_invite_link_service_rejects_member(world):
    with pytest.raises(AdminAccessRequiredError):
        svc.create_invite_link_service(world.board.id, world.member.id)
    assert db.session.query(InviteLinkEntity).count() == 0


def test_revoke_invite_link_service_sets_revoked_at_and_keeps_row(world):
    created = svc.create_invite_link_service(world.board.id, world.admin.id)
    result = svc.revoke_invite_link_service(world.board.id, world.admin.id, created['id'])
    assert result == {'id': str(created['id'])}
    link = db.session.get(InviteLinkEntity, created['id'])
    assert link is not None and link.revoked_at is not None


def test_revoke_invite_link_service_404_before_admin_check(world):
    created = svc.create_invite_link_service(world.board.id, world.admin.id)
    with pytest.raises(InviteLinkNotFoundException):
        svc.revoke_invite_link_service(world.board.id, world.member.id, uuid.uuid4())
    with pytest.raises(InviteLinkNotFoundException):
        svc.revoke_invite_link_service(world.board.id, world.member.id, 'not-a-uuid')
    with pytest.raises(InviteLinkNotFoundException):  # link of Board A on Board B
        svc.revoke_invite_link_service(world.board_b.id, world.admin_b.id, created['id'])
    with pytest.raises(AdminAccessRequiredError):
        svc.revoke_invite_link_service(world.board.id, world.member.id, created['id'])


# ---- failed commits roll back and re-raise ---------------------------------------------------

def _fail_commit(monkeypatch):
    def boom():
        raise RuntimeError('commit failed')

    monkeypatch.setattr(db.session, 'commit', boom)


def test_create_board_service_rolls_back_when_commit_fails(world, monkeypatch):
    _fail_commit(monkeypatch)
    with pytest.raises(RuntimeError):
        svc.create_board_service(world.admin.id, {'name': 'Lost'})
    monkeypatch.undo()
    assert db.session.query(BoardEntity).filter_by(name='Lost').count() == 0


def test_update_board_service_rolls_back_when_commit_fails(world, monkeypatch):
    _fail_commit(monkeypatch)
    with pytest.raises(RuntimeError):
        svc.update_board_service(world.board.id, world.admin.id, {'name': 'Lost'})
    monkeypatch.undo()
    assert db.session.get(BoardEntity, world.board.id).name != 'Lost'


def test_add_team_member_service_reraises_other_commit_errors(world, monkeypatch):
    _fail_commit(monkeypatch)
    with pytest.raises(RuntimeError):
        svc.add_team_member_service(world.board.id, world.admin.id, {'email': world.outsider.email})
    monkeypatch.undo()
    assert db.session.query(TeamMembershipEntity).filter_by(team_id=world.team.id).count() == 3


def test_add_team_member_service_maps_unique_violation_to_409(world, monkeypatch):
    from sqlalchemy.exc import IntegrityError

    def race():
        raise IntegrityError('insert', {}, Exception('uq_team_memberships'))

    monkeypatch.setattr(db.session, 'commit', race)
    with pytest.raises(MemberAlreadyExistsError):
        svc.add_team_member_service(world.board.id, world.admin.id, {'email': world.outsider.email})


def test_remove_team_member_service_rolls_back_when_commit_fails(world, monkeypatch):
    _fail_commit(monkeypatch)
    with pytest.raises(RuntimeError):
        svc.remove_team_member_service(world.board.id, world.admin.id, world.member.id)
    monkeypatch.undo()
    assert db.session.query(TeamMembershipEntity).filter_by(team_id=world.team.id).count() == 3
