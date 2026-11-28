# Implementation Plan: Sevy (task-management-app)

## Overview

This plan implements Sevy from requirements.md (V9) and design.md in dependency order: backend scaffold, core utilities, database, access guards, the eight Blueprints, backend integration, then the Next.js frontend, Playwright suite and repository documents. Guideline rules are referenced by ID (`BE-nn`, `DB-nn`, `FE-nn`, `TC-nn`, `ST-nn`), not restated. No application code, migration or test exists yet, and no task in this list has been run.

## Tasks

- [x] 1. Backend project scaffold
  - [x] 1.1 Create backend skeleton, dependency pins and tool configuration (T-01)
    - Create the `backend/` tree of structure.md section 1 (empty packages for `app/`, `app/models/`, `app/utils/`, `app/blueprints/<feature>/` x8, `tests/unit/<feature>/` x8, `tests/e2e/`, `tests/load/`).
    - `requirements.txt` with exact `==` pins and only the TC-02 runtime allowlist; `requirements-dev.txt` with `pytest`, `pytest-cov`, `flake8` only (TC-01, TC-02). Pin the exact versions resolved at implementation time; no ranges.
    - `.flake8` (max-line-length 100, max-complexity 8, TC-04), `pytest.ini` / `.coveragerc` with the 85% overall and 90% per-`service.py` thresholds (TC-17), `runtime.txt` with Python 3.12.
    - Files: backend/requirements.txt, backend/requirements-dev.txt, backend/.flake8, backend/pytest.ini, backend/.coveragerc, backend/runtime.txt, backend/app/__init__.py (package markers)
    - _Requirements: 16.2, 16.3, 16.4, 28.1_
  - [x] 1.2 Add configuration, extensions, app factory, Procfile, env example and gitignore (T-02)
    - `app/config.py` reads `FLASK_APP`, `FLASK_DEBUG`, `DATABASE_URL`, `JWT_SECRET_KEY`, `CORS_ORIGINS` from the environment (TC-09); `app/extensions.py` defines `db` with the `MetaData(naming_convention=...)` of DB-03, `migrate`, `jwt`, `cors`.
    - `create_app()` in `app/__init__.py`: loads config, initialises extensions, restricts CORS to `CORS_ORIGINS` (no `*`), and leaves a clearly named place where blueprints and error handlers are registered by later tasks.
    - `backend/Procfile` with the TC-20 text: `gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --workers 2` and a `release` step `flask db upgrade`; do not add a worker class.
    - `backend/.env.example` listing every TC-09 Flask variable with placeholders (`DATABASE_URL` example includes `sslmode=require` note for hosted use); update root `.gitignore` per ST-13 (`.env`, `.env.*` with `!.env.example`, `__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `.next/`, `node_modules/`).
    - Files: backend/app/config.py, backend/app/extensions.py, backend/app/__init__.py, backend/Procfile, backend/.env.example, .gitignore
    - _Requirements: 20.10, 27.1, 27.2, 27.7, 27.8, 29.6_

- [x] 2. Backend core utilities
  - [x] 2.1 Implement time helper, response helpers and the exception catalog (T-03)
    - `app/utils/time.py` with `utc_now()` (DB-05); `app/utils/responses.py` with `success()`, `error()` and `format_validation_error()` (BE-04, BE-07).
    - `app/exceptions.py`: `AppException`, the `ACCESS_OR_NOT_FOUND_MESSAGE` constant and every class of the BE-10 catalog with its status code and default message.
    - Unit tests for the three helpers (fixed payload gives the exact normalized string of BE-04) and for the exception status codes.
    - Files: backend/app/utils/time.py, backend/app/utils/responses.py, backend/app/exceptions.py, backend/tests/unit/auth/test_core_helpers.py
    - _Requirements: 20.1, 20.4, 20.5, 20.11, 20.13_
  - [x] 2.2 Implement global error handler, structured logging and health route (T-04)
    - `app/error_handlers.py` `register_error_handlers(app)` (BE-11): `AppException`, Marshmallow `ValidationError`, Werkzeug `HTTPException` (404 `{"error": "Not found"}`, 405), any other exception to 500 `{"error": "Internal server error"}` with no traceback; call it from `create_app()`.
    - `app/logging_config.py` JSON logger with exactly the fields `level`, `endpoint`, `error_type`, `user_id` (BE-12); `app/health.py` `GET /api/health` returning `{"data": {"status": "ok"}}`, registered in `create_app()`.
    - In the same function register the four Flask-JWT-Extended callbacks (`unauthorized_loader`, `invalid_token_loader`, `expired_token_loader`, `token_verification_failed_loader`), each returning the 401 envelope built with `error()`, never the library default 422 (BE-13).
    - Tests: on a test-only JWT-protected route a malformed token, an expired token and a missing token are all 401 in the envelope (never 422); unknown URL is JSON 404, unsupported method is JSON 405, patched service raising `RuntimeError` gives the 500 envelope without `Traceback`, log record keys equal the four fields, health returns 200.
    - Files: backend/app/error_handlers.py, backend/app/logging_config.py, backend/app/health.py, backend/app/__init__.py, backend/tests/unit/auth/test_error_handling.py
    - _Requirements: 14.3, 20.1, 20.2, 20.3, 20.7, 27.3_
  - [x] 2.3 Implement FLOAT ordering constants and pure allocation helpers (T-05)
    - `app/utils/ordering.py` with `ORDER_STEP = 1024.0`, `MIN_GAP = 1e-6` and pure helpers for first, append, head and between allocation, gap detection and the sequence of rebalanced values (BE-14).
    - Unit tests: each allocation rule, head insertion 60 times keeps values positive and strictly increasing once a rebalance is applied.
    - Files: backend/app/utils/ordering.py, backend/tests/unit/cards/test_ordering_helpers.py
    - _Requirements: 5.2, 5.3, 5.9, 6.2, 6.9, 7.8_

- [x] 3. Database models, migrations and schema tests
  - [x] 3.1 Create Entity models for users, teams, memberships, boards and columns (T-06)
    - One model per file with the DB-05 required columns, DB-09 domain columns, DB-11 `ondelete` policy, named constraints and indexes (`uq_users_username`, `ck_users_username_format`, `uq_users_email_lower`, `uq_teams_owner_id_personal`, `uq_team_memberships_team_id_user_id`, `ck_team_memberships_role`, the DB-08 column order index and check) and the foreign-key indexes of design section 5.2 for these tables: `ix_team_memberships_user_id`, `ix_teams_owner_id`, `ix_boards_team_id`.
    - Relationships per the DB-12 catalog (both sides, explicit `backref`, `lazy`, `order_by`, `foreign_keys`). Columns are hard-deleted: never write `deleted_at` on `board_columns` (see U-01 in "Depends on a user decision").
    - Files: backend/app/models/user.py, backend/app/models/team.py, backend/app/models/team_membership.py, backend/app/models/board.py, backend/app/models/board_column.py, backend/app/models/__init__.py
    - _Requirements: 24.1, 26.1, 26.6, 26.7, 26.9, 26.12_
  - [x] 3.2 Create Entity models for cards, comments, notifications, activity events and invite links (T-07)
    - `CardEntity` per the DB-08 complete example (FLOAT `order`, `ck_cards_order_positive`, `ix_cards_column_id_order`, partial unique `uq_cards_column_id_order_active`), `CardCommentEntity` (`parent_comment_id`, `deleted_at` is the only tombstone marker), `NotificationEntity` (`recipient_id`, `comment_id`, no `user_id`, no `card_id`), `ActivityEventEntity` (`ck_activity_events_event_type` with the five event types), `InviteLinkEntity` (`token_hash`, `revoked_at`).
    - Foreign-key indexes of design section 5.2 for these tables: `ix_cards_assignee_id`, `ix_cards_created_by_id`, `ix_card_comments_card_id`, `ix_card_comments_author_id`, `ix_card_comments_parent_comment_id`, `ix_notifications_comment_id`, `ix_activity_events_actor_id`, `ix_invite_links_board_id`, `ix_invite_links_created_by_id`. No title-search index is created (design D-07 is not approved, see U-03).
    - Remaining DB-12 relationships and DB-11 delete behavior; register all ten models in `models/__init__.py`.
    - Files: backend/app/models/card.py, backend/app/models/card_comment.py, backend/app/models/notification.py, backend/app/models/activity_event.py, backend/app/models/invite_link.py, backend/app/models/__init__.py
    - _Requirements: 3.2, 6.8, 24.1, 26.1, 26.2, 26.6, 26.7, 26.10, 26.11_
  - [x] 3.3 Set up Flask-Migrate and create the initial migration (T-08)
    - Initialise `backend/migrations/` and generate the first revision creating all ten tables, every named CHECK constraint, the three partial unique indexes `uq_cards_column_id_order_active`, `uq_board_columns_board_id_order_active`, `uq_teams_owner_id_personal` by name (TC-10), and the 12 foreign-key indexes of design section 5.2 named `ix_<table>_<column>` (`ix_team_memberships_user_id`, `ix_teams_owner_id`, `ix_boards_team_id`, `ix_cards_assignee_id`, `ix_cards_created_by_id`, `ix_card_comments_card_id`, `ix_card_comments_author_id`, `ix_card_comments_parent_comment_id`, `ix_notifications_comment_id`, `ix_activity_events_actor_id`, `ix_invite_links_board_id`, `ix_invite_links_created_by_id`). No title-search index and no `pg_trgm` extension is created (D-07, U-03). Review the generated file by hand; `db.create_all()` is not used outside test fixtures.
    - Files: backend/migrations/ (env.py, alembic.ini, versions/<initial revision>.py)
    - _Requirements: 16.3, 26.3, 26.4, 26.7_
  - [x] 3.4 Write schema, constraint and relationship tests on PostgreSQL (T-09)
    - `tests/conftest.py` using a separate PostgreSQL database `sevy_test` (never SQLite, TC-10) with app, client and factory fixtures.
    - Implement the DB-09 and DB-08 verify bullets: expected table set, column lists, no Board-level membership table, no `is_deleted` column, no `user_id`/`card_id` on notifications, username and email constraints, partial index metadata and behavior (duplicate active order rejected, soft-deleted order does not block), every one of the 12 foreign-key indexes of design section 5.2 exists by name and no title-search index exists, personal Team uniqueness, `test_relationships_both_sides`, DB-11 delete behavior (Board delete cascades, membership delete keeps authored work).
    - Files: backend/tests/conftest.py, backend/tests/unit/boards/test_schema_models.py, backend/tests/unit/cards/test_schema_constraints.py
    - _Requirements: 6.8, 16.3, 24.1, 26.1, 26.2, 26.3, 26.4, 26.6, 26.7, 26.9, 26.10, 26.11, 26.12_

- [x] 4. Access guards
  - [x] 4.1 Implement the guard decorators and JWT error callbacks (T-10)
    - `app/utils/auth.py`: `@token_required` (passes `current_user` first) and `@board_access_required(allow_guest_read=True)` (passes the `access` object first) implementing the eight-step Access Resolution Table of BE-08 exactly, including UUID path validation after authentication (BE-04) and invite token lookup by hash.
    - Register the Flask-JWT-Extended callbacks (`unauthorized_loader`, `invalid_token_loader`, `expired_token_loader`, `token_verification_failed_loader`) in `register_error_handlers` so every token failure is the 401 envelope, never 422 (BE-13).
    - Files: backend/app/utils/auth.py, backend/app/error_handlers.py
    - _Requirements: 1.1, 1.2, 1.3, 1.6, 1.7, 2.1, 3.3, 3.4, 3.5, 3.9, 3.10, 3.11, 3.12, 3.13, 3.14, 3.15, 8.5, 13.8, 13.9, 13.12, 13.13, 13.14, 20.12_
  - [x] 4.2 Write table-driven tests for every Access Resolution Table step (T-11)
    - Use a test-only app fixture that registers one `@token_required` route and one Guest route (the real routes come later) and seeds Teams, Boards, Cards, memberships and invite links.
    - Cases (BE-08 verify): valid Guest token 200 read-only; invalid, revoked and empty token 404 `Not found`; bad or expired JWT with a valid token 401; no JWT and no token 401; non-member JWT without token 403 generic; token of another Board 403 generic; member with an invalid or foreign token 200; missing Board and soft-deleted Card 404 generic; token-only request to a protected route 401; malformed token, expired token and missing token on a protected route are all 401, never 422.
    - Files: backend/tests/unit/boards/test_access_resolution_table.py
    - _Requirements: 1.2, 1.7, 3.3, 3.4, 3.5, 3.9, 3.10, 3.11, 3.12, 3.13, 3.14, 3.15, 13.8, 13.13, 13.14, 20.12_
  - [ ]* 4.3 Write property test for Property 7: Access Resolution Table totality (T-12)
    - **Property 7: Access Resolution Table totality**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13, 3.14**
    - Enumerate every combination of Authorization state, invite token state, resource existence and membership and assert exactly one table step matches and returns its result (exhaustive, input space is finite).
    - Seeded loop (stdlib random, fixed seed, at least 100 iterations); no property-testing library (tech.md TC-02, TC-03).
    - Files: backend/tests/unit/boards/test_boards_properties.py
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13, 3.14_

- [x] 5. Auth Blueprint
  - [x] 5.1 Implement the auth Blueprint (register and login) (T-13)
    - `RegisterSchema` (username 3-30, normalised to lowercase) and `LoginSchema` with `unknown=RAISE` (BE-05); `UserSchema` output (BE-06).
    - `register_service`: user, personal Team (`is_personal` true, `owner_id` = the user) and `admin` membership in one transaction; case-insensitive duplicate username and email give 409, also on a concurrent unique violation (BE-13, BE-15). `login_service` returns `access_token`, `token_type`, `expires_in` 3600 and `user`, with the identical 401 for unknown email and wrong password.
    - Routes `POST /api/auth/register` and `POST /api/auth/login` (public, handlers at most 5 lines, BE-02) and `auth_bp` registration hook.
    - Files: backend/app/blueprints/auth/__init__.py, backend/app/blueprints/auth/schema.py, backend/app/blueprints/auth/service.py, backend/app/blueprints/auth/routes.py, backend/app/__init__.py
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.10, 13.11, 20.9, 26.5_
  - [x] 5.2 Write auth service and route tests (T-14)
    - Success and failure test per service function; routes: 201, 400, 409, 200, 401; atomicity (forced failure after the user insert leaves no user, Team or membership); `exp - iat == 3600`; no key beginning with `password` in any response; case-insensitive duplicates; unknown field 400.
    - Files: backend/tests/unit/auth/test_auth_service.py, backend/tests/unit/auth/test_auth_routes.py
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.10, 13.11, 13.12, 26.5, 28.1_
  - [ ]* 5.3 Write property test for Property 16: Username normalization uniqueness (T-15)
    - **Property 16: Username normalization uniqueness**
    - **Validates: Requirements 13.1, 13.3, 26.12**
    - Register random case variants of usernames and assert at most one succeeds and every stored username is lowercase.
    - Seeded loop (stdlib random, fixed seed, at least 100 iterations); no property-testing library (tech.md TC-02, TC-03).
    - Files: backend/tests/unit/auth/test_auth_properties.py
    - _Requirements: 13.1, 13.3, 26.12_

- [x] 6. Users Blueprint
  - [x] 6.1 Implement the users Blueprint (profile) (T-16)
    - `UserUpdateSchema` (`name` 1-100, `email` valid, at least one required; `password`, `password_hash`, `username` and any other field rejected); `get_current_user_service` and `update_current_user_service` (case-insensitive email conflict 409); routes `GET /api/users/me` and `PATCH /api/users/me`.
    - Files: backend/app/blueprints/users/__init__.py, backend/app/blueprints/users/schema.py, backend/app/blueprints/users/service.py, backend/app/blueprints/users/routes.py, backend/app/__init__.py
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 20.9_
  - [x] 6.2 Write users service and route tests (T-17)
    - Success and failure per service function; 200, 400 (empty body, forbidden fields, invalid email), 401, 409; response has exactly `id`, `name`, `username`, `email`, `created_at`.
    - Files: backend/tests/unit/users/test_users_service.py, backend/tests/unit/users/test_users_routes.py
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 28.1_

- [x] 7. Checkpoint - foundation, auth and users
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Boards Blueprint, Team members and Invite Links
  - [x] 8.1 Implement board services, Team access helpers and board routes (T-18)
    - `boards/service.py`: `require_team_member_service` and `require_team_admin_service` (BE-09), create (default personal Team, `team_id` of a Team the requester does not administer gives 403 generic, see D-01), list (filtered through memberships, newest first), get, update, delete (database cascade, returns the id).
    - `BoardCreateSchema`, `BoardUpdateSchema`, `BoardDetailSchema` nesting Columns then Cards in `order` ascending (BE-06); `GET /api/boards/<id>` uses the Guest guard and loads Board, Columns and Cards in at most 3 SQL queries; routes for the five board endpoints.
    - Files: backend/app/blueprints/boards/__init__.py, backend/app/blueprints/boards/schema.py, backend/app/blueprints/boards/service.py, backend/app/blueprints/boards/routes.py, backend/app/__init__.py
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.3, 2.6, 2.7, 3.3, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 14.2, 20.5, 26.4_
  - [x] 8.2 Implement Team member management routes and services (T-19)
    - `MemberAddSchema`, `MemberRoleUpdateSchema`; add (404 `User not found`, 409 duplicate), list, change role, remove (keeps authored Cards and Comments, sets `assignee_id` to null on that user's non-deleted Cards of the Team's Boards, returns the user id); last Admin cannot be removed or demoted (409); the Admin check runs before the email, membership or role is evaluated (BE-09).
    - API only: no Frontend screen (OD-14).
    - Files: backend/app/blueprints/boards/schema.py, backend/app/blueprints/boards/service.py, backend/app/blueprints/boards/routes.py
    - _Requirements: 1.5, 2.3, 2.6, 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8, 12.9, 12.10_
  - [ ]* 8.3 Write property test for Property 11: At-least-one-Admin invariant (T-20)
    - **Property 11: At-least-one-Admin invariant**
    - **Validates: Requirements 12.10**
    - Run random sequences of role changes and removals and assert every Team keeps at least one Admin.
    - Seeded loop (stdlib random, fixed seed, at least 100 iterations); no property-testing library (tech.md TC-02, TC-03).
    - Files: backend/tests/unit/boards/test_boards_properties.py
    - _Requirements: 12.10_
  - [x] 8.4 Implement Invite Link create and revoke (T-21)
    - `InviteLinkCreateSchema` (empty body or `{}`, any field rejected); create generates `secrets.token_urlsafe(32)`, stores only the hash, returns `id`, `board_id`, `token`, `created_at` once (201); revoke sets `revoked_at`, keeps the row, returns the id; an unknown or foreign `invite_id` gives 404 `Not found` before the Admin check. API only (OD-14).
    - Files: backend/app/blueprints/boards/schema.py, backend/app/blueprints/boards/service.py, backend/app/blueprints/boards/routes.py
    - _Requirements: 2.3, 2.6, 3.1, 3.2, 3.6, 3.7_
  - [x] 8.5 Write boards service, route and permission-matrix tests (T-22)
    - Success and failure test per service function; route tests for 200/201/400/401/403/404/409 across the board, member and invite endpoints; table-driven permission test (`-k permission`) with one case per applicable cell of the Requirement 2 table for each role, cross-Team denial for Board ids, 404 before 403, non-Admin member management 403 before the email lookup, revoked-link read 404, link of Board A gives nothing on Board B, Guest write attempts change no data.
    - Query budget (R14.2, design D-06): loading the Columns and Cards of `GET /api/boards/<id>` with 5 Columns and 50 Cards takes at most 3 queries (one for Columns, one for non-deleted Cards with the Assignee joined in the same query), and no query runs per Column or per Card; the guard's Board and membership lookups are counted separately.
    - Files: backend/tests/unit/boards/test_boards_service.py, backend/tests/unit/boards/test_boards_routes.py, backend/tests/unit/boards/test_permission_matrix.py
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.9, 3.1, 3.2, 3.6, 3.7, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8, 12.9, 12.10, 14.2, 28.1_
  - [ ]* 8.6 Write property test for Property 5: Role monotonicity and determinism (T-23)
    - **Property 5: Role monotonicity and determinism**
    - **Validates: Requirements 2.10, 2.11**
    - Evaluate every action of the Requirement 2 table for Guest, Member and Admin, assert monotonicity and that repeated evaluation gives the same decision.
    - Seeded loop (stdlib random, fixed seed, at least 100 iterations); no property-testing library (tech.md TC-02, TC-03).
    - Files: backend/tests/unit/boards/test_boards_properties.py
    - _Requirements: 2.10, 2.11_
  - [ ]* 8.7 Write property test for Property 6: Board isolation (T-24)
    - **Property 6: Board isolation**
    - **Validates: Requirements 1.4**
    - Across two Teams, assert a non-member without an invite link receives no Column, Card, Comment, activity, analytics or Notification data, including through search and My Tasks.
    - Seeded loop (stdlib random, fixed seed, at least 100 iterations); no property-testing library (tech.md TC-02, TC-03).
    - Files: backend/tests/unit/boards/test_boards_properties.py
    - _Requirements: 1.4_

- [x] 9. Columns Blueprint
  - [x] 9.1 Implement the columns Blueprint (T-25)
    - `ColumnCreateSchema`, `ColumnUpdateSchema`, `ColumnReorderSchema`; create appends (1024.0 or last + 1024.0), optional `is_done`; rename and `is_done` change are Admin only; delete (Admin only) removes the Column with its Cards and Comments via the database cascade and leaves other orders unchanged.
    - Reorder `PATCH /api/boards/<id>/columns/reorder`: store the client `order`, 409 on an equal active sibling `order`, rebalance in one transaction with `SELECT ... FOR UPDATE` and the two-phase write of BE-14; response `{"column", "rebalanced"}`.
    - Setting `is_done` true or false updates `completed_at` of the Column's Cards as in Requirement 24 criterion 6.
    - Files: backend/app/blueprints/columns/__init__.py, backend/app/blueprints/columns/schema.py, backend/app/blueprints/columns/service.py, backend/app/blueprints/columns/routes.py, backend/app/__init__.py
    - _Requirements: 2.4, 2.5, 2.6, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 5.11, 5.12, 5.13, 5.14, 24.1, 24.6, 26.7, 26.8_
  - [x] 9.2 Write columns service and route tests (T-26)
    - Success and failure per service function; 201/200/400/403/404/409 per route; Member denied rename, reorder, delete and `is_done`; rebalance on PostgreSQL (50 siblings, sequence preserved, ends at `1024.0 * k`); equal-order 409 body is exactly one non-empty `error` string; `is_done` toggle sets and clears `completed_at`.
    - Files: backend/tests/unit/columns/test_columns_service.py, backend/tests/unit/columns/test_columns_routes.py
    - _Requirements: 2.5, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 5.11, 5.12, 5.13, 5.14, 24.6, 26.8, 28.1_

- [x] 10. Cards Blueprint
  - [x] 10.1 Implement card create, update and soft delete (T-27)
    - `CardCreateSchema`, `CardUpdateSchema` (`column_id`, `order`, `deleted_at`, `completed_at` rejected), `CardSchema` output; create appends and sets `completed_at` in a done Column; assignee must be a Team member else 400 `Assignee must be a Team member`, null clears the Assignee.
    - Soft delete sets only the Card's `deleted_at`, never touches Comments, Notifications or activity rows; Admin deletes any Card, a Member only own Cards (`AdminAccessRequiredError`, see U-08); every Card-id route answers a soft-deleted Card with 404 generic before membership checks.
    - `update_card_service` loads the Card with `with_for_update` inside one transaction, applies the request and commits, so two simultaneous PATCH requests are applied one after the other (design section 9, R15.3, D-05).
    - Exactly one `card_created`, `card_updated` or `card_deleted` Activity_Event per successful request in the same transaction, none for a rejected one (BE-15).
    - Files: backend/app/blueprints/cards/__init__.py, backend/app/blueprints/cards/schema.py, backend/app/blueprints/cards/service.py, backend/app/blueprints/cards/routes.py, backend/app/__init__.py
    - _Requirements: 2.4, 2.6, 2.9, 6.1, 6.3, 6.4, 6.5, 6.6, 6.7, 6.9, 6.11, 6.13, 6.14, 6.15, 6.16, 15.3, 18.1, 18.2, 18.3, 18.4, 18.12, 24.3_
  - [ ]* 10.2 Write property test for Property 13: Soft-delete retention (T-28)
    - **Property 13: Soft-delete retention**
    - **Validates: Requirements 6.16**
    - Soft-delete random Cards with Comments, Notifications and events and assert no row is removed and the Card is absent from Board, Search, My Tasks and Analytics reads.
    - Seeded loop (stdlib random, fixed seed, at least 100 iterations); no property-testing library (tech.md TC-02, TC-03).
    - Files: backend/tests/unit/cards/test_cards_properties.py
    - _Requirements: 6.16_
  - [x] 10.3 Implement card move with two-phase rebalance (T-29)
    - `CardPositionSchema`; `move_card_service`: 400 for an unknown Column or one on another Board (`InvalidTargetColumnError`), 409 on an equal active sibling `order` with the moved row itself excluded from the comparison (repeating the same move is idempotent), store the order, rebalance when a gap is below `MIN_GAP`; response `{"card", "rebalanced"}`.
    - Lock order (BE-14, design 6.1): lock the parent Column row first, then its active siblings with `SELECT ... FOR UPDATE ORDER BY order, id`; when the Column changes, lock both parents in `id` order, then their siblings. Two-phase write in one transaction: phase 1 moves every affected active row to `max active order + ORDER_STEP * (i + 1)`, phase 2 writes `ORDER_STEP * (i + 1)`.
    - `completed_at` set, cleared or unchanged per Requirement 24 criteria 2, 4, 5; one `card_moved` event per successful move; route `PATCH /api/cards/<id>/position`.
    - Files: backend/app/blueprints/cards/schema.py, backend/app/blueprints/cards/service.py, backend/app/blueprints/cards/routes.py
    - _Requirements: 6.10, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10, 7.11, 7.12, 7.13, 7.14, 15.3, 15.4, 24.2, 24.4, 24.5, 26.8_
  - [ ]* 10.4 Write property test for Property 1: Active order stays unique, strictly increasing, and positive (T-30)
    - **Property 1: Active order stays unique, strictly increasing, and positive**
    - **Validates: Requirements 5.13, 6.10, 26.7, 26.8**
    - Run random create, move, delete and reorder sequences on Columns and Cards and assert active orders stay positive, unique and strictly increasing.
    - Seeded loop (stdlib random, fixed seed, at least 100 iterations); no property-testing library (tech.md TC-02, TC-03).
    - Files: backend/tests/unit/cards/test_cards_properties.py
    - _Requirements: 5.13, 6.10, 26.7, 26.8_
  - [ ]* 10.5 Write property test for Property 2: Move round trip (T-31)
    - **Property 2: Move round trip**
    - **Validates: Requirements 7.12**
    - Move a Card from Column X to Y and back with its original order and assert both sequences are restored.
    - Seeded loop (stdlib random, fixed seed, at least 100 iterations); no property-testing library (tech.md TC-02, TC-03).
    - Files: backend/tests/unit/cards/test_cards_properties.py
    - _Requirements: 7.12_
  - [ ]* 10.6 Write property test for Property 3: Move idempotence (T-32)
    - **Property 3: Move idempotence**
    - **Validates: Requirements 7.13**
    - Send the same valid move twice and assert the Board state equals that after one request.
    - Seeded loop (stdlib random, fixed seed, at least 100 iterations); no property-testing library (tech.md TC-02, TC-03).
    - Files: backend/tests/unit/cards/test_cards_properties.py
    - _Requirements: 7.13_
  - [ ]* 10.7 Write property test for Property 4: Card count invariant under move (T-33)
    - **Property 4: Card count invariant under move**
    - **Validates: Requirements 7.11**
    - After random valid moves assert the number of non-deleted Cards on the Board is unchanged.
    - Seeded loop (stdlib random, fixed seed, at least 100 iterations); no property-testing library (tech.md TC-02, TC-03).
    - Files: backend/tests/unit/cards/test_cards_properties.py
    - _Requirements: 7.11_
  - [x] 10.8 Implement the card list route for search and My Tasks (T-34)
    - `CardListQuerySchema` (`assignee=me`, `q` 1-100 not blank, optional `board_id`; at least one of `assignee` or `q`, else 400) and `CardListItemSchema`; `GET /api/cards` filters through the requester's memberships, excludes soft-deleted Cards, matches title only and case-insensitively, applies all given filters together.
    - The route calls exactly one service function, `list_cards_service`, which dispatches on `assignee` and `q` inside the service (design 4a, BE-02, ST-03); the handler holds no branching.
    - `board_id` the requester cannot access gives 403 generic, a non-existent one 404 generic (evaluated first); this is the only body or query id that is not a 400. No title-search index is added (R26.3 is open, see U-03).
    - Files: backend/app/blueprints/cards/schema.py, backend/app/blueprints/cards/service.py, backend/app/blueprints/cards/routes.py
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 10.9, 18.5, 18.6, 18.7, 18.8, 18.9_
  - [ ]* 10.9 Write property test for Property 9: Search soundness, completeness, and idempotence (T-35)
    - **Property 9: Search soundness, completeness, and idempotence**
    - **Validates: Requirements 10.6, 10.7, 10.8**
    - Generate random titles and substrings and assert results are exactly the accessible non-deleted Cards containing the term (any case) and repeating the search returns the same set.
    - Seeded loop (stdlib random, fixed seed, at least 100 iterations); no property-testing library (tech.md TC-02, TC-03).
    - Files: backend/tests/unit/cards/test_cards_properties.py
    - _Requirements: 10.6, 10.7, 10.8_
  - [x] 10.10 Write cards service and route tests (T-36)
    - Success and failure per service function; 201/200/400/403/404/409 per route including all five Card-id routes on a soft-deleted Card; assignee rules (Team member, non-member, unknown UUID); Member deleting another user's Card 403; completion transitions into, out of and between done Columns; equal-order 409 for a different Card at an existing `order`; repeating the same move request returns the same Board state (R7.13); a cross-Column move completes without an integrity error; rebalance on PostgreSQL; concurrent-move test on PostgreSQL (two simultaneous moves to the same slot end with unique increasing orders, one may be 409); a soft-deleted Card's `order` does not block an active Card; concurrent-edit test on PostgreSQL (two simultaneous PATCH requests are applied one after the other, no integrity error, the final Card equals the last applied request, no lost update beyond it; R15.3, D-05).
    - Body or query ids that do not exist are 400, not 404 or 403: unknown `column_id` in a move body (R7.4), a Column on another Board (R7.5), a non-member or unknown `assignee_id` (R18.2, body `Assignee must be a Team member`); the one exception is `board_id` in `GET /api/cards`, which is 404 or 403 with the generic body (R10.3).
    - Search and My Tasks: case-insensitivity, blank term 400, cross-Board isolation, soft-deleted exclusion, `assignee=me` returns only the requester's Cards.
    - Files: backend/tests/unit/cards/test_cards_service.py, backend/tests/unit/cards/test_cards_routes.py, backend/tests/unit/cards/test_cards_ordering_pg.py
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 6.11, 6.13, 6.14, 6.15, 6.16, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10, 7.14, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.9, 15.3, 15.4, 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7, 18.8, 18.9, 18.12, 24.2, 24.3, 24.4, 24.5, 26.7, 28.1_

- [x] 11. Notifications Blueprint
  - [x] 11.1 Implement the notifications Blueprint and mention service (T-37)
    - `create_mention_notifications_service` (mention `@` + 3-30 letters, digits, underscore, lowercased, matched to Team members; one unread Notification per member per Comment with `message` = `<mentioner name> mentioned you on "<card title>"` truncated to 255 characters (design D-08, needs user confirmation); none for the author or an unmatched name; an edit notifies only newly mentioned members) and cleanup helpers for a deleted Comment (BE-15).
    - `NotificationQuerySchema` (page >= 1 default 1, per_page 1-50 default 10), `NotificationSchema` with derived `card_id` and `board_id`; list returns exactly `items`, `page`, `per_page`, `total`, `total_pages`, `unread_count` (BE-07), hides Notifications of soft-deleted Cards (see U-04); mark read is idempotent and 404 `Not found` for another user's Notification; routes `GET /api/notifications` and `PATCH /api/notifications/<id>/read`.
    - Files: backend/app/blueprints/notifications/__init__.py, backend/app/blueprints/notifications/schema.py, backend/app/blueprints/notifications/service.py, backend/app/blueprints/notifications/routes.py, backend/app/__init__.py
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9, 9.10, 9.11, 9.12, 9.13_
  - [ ]* 11.2 Write property test for Property 8: Notification deduplication and no self-notification (T-38)
    - **Property 8: Notification deduplication and no self-notification**
    - **Validates: Requirements 9.1, 9.2, 9.3, 9.4**
    - Generate random Comment bodies with repeated, self and unmatched mentions and assert one Notification per mentioned member and none for the author.
    - Seeded loop (stdlib random, fixed seed, at least 100 iterations); no property-testing library (tech.md TC-02, TC-03).
    - Files: backend/tests/unit/notifications/test_notifications_properties.py
    - _Requirements: 9.1, 9.2, 9.3, 9.4_
  - [ ]* 11.3 Write property test for Property 15: Pagination arithmetic (T-39)
    - **Property 15: Pagination arithmetic**
    - **Validates: Requirements 9.7**
    - For random total and per_page (1-50) assert `total_pages == ceil(total / per_page)` and 0 when total is 0.
    - Seeded loop (stdlib random, fixed seed, at least 100 iterations); no property-testing library (tech.md TC-02, TC-03).
    - Files: backend/tests/unit/notifications/test_notifications_properties.py
    - _Requirements: 9.7_
  - [x] 11.4 Wire Notification cleanup into member removal (T-40)
    - Modify `remove_team_member_service` to call the notifications cleanup so the removed user's Notifications for the Team's Boards are deleted, keeping authored Cards and Comments (R9.13, R12.5).
    - Files: backend/app/blueprints/boards/service.py, backend/app/blueprints/notifications/service.py
    - _Requirements: 9.13, 12.5, 12.6_
  - [x] 11.5 Write notifications service and route tests (T-41)
    - Success and failure per service function; exact counts for single, repeated, self and unmatched mentions; the stored `message` equals `<mentioner name> mentioned you on "<card title>"` and is at most 255 characters (D-08); edit adds only new mentions; pagination keys, `total_pages` 0 for empty, `unread_count` beyond the page; per_page 51 and page 0 give 400; mark read idempotent, other user 404; deleting a Comment removes its Notifications; removing a member removes theirs.
    - Files: backend/tests/unit/notifications/test_notifications_service.py, backend/tests/unit/notifications/test_notifications_routes.py
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9, 9.10, 9.11, 9.12, 9.13, 28.1_

- [x] 12. Comments Blueprint
  - [x] 12.1 Implement the comments Blueprint (T-42)
    - `CommentCreateSchema` (`content` 1-2000, `parent_id` optional), `CommentUpdateSchema`, `CommentSchema` (API `parent_id` maps to `parent_comment_id`, `is_deleted` derived from `deleted_at`).
    - Create (parent must be on the same Card else 400, mention notifications via the notifications service, `comment_added` event), list with the Guest guard (flat, `created_at` ascending, tombstone with empty `content` only when a direct live reply exists, otherwise omitted; see U-05), edit and delete by the author only (also for Admins, `CommentOwnershipError`); Card-id routes answer a soft-deleted Card with 404 generic; routes for the four comment endpoints.
    - Files: backend/app/blueprints/comments/__init__.py, backend/app/blueprints/comments/schema.py, backend/app/blueprints/comments/service.py, backend/app/blueprints/comments/routes.py, backend/app/__init__.py
    - _Requirements: 2.2, 2.8, 6.14, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 8.11, 8.12, 8.18, 8.19_
  - [x] 12.2 Write comments service and route tests (T-43)
    - Success and failure per service function; routes: 201 create, 400 missing `content`, 401 unauthenticated, 403 non-owner edit or delete, 403 non-member create, 404 on missing or soft-deleted Card; tombstone with a live reply, omitted without; Guest read with a valid link, no Guest write; edited indicator data (`updated_at` later than `created_at`).
    - Files: backend/tests/unit/comments/test_comments_service.py, backend/tests/unit/comments/test_comments_routes.py
    - _Requirements: 2.2, 2.8, 6.14, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 8.11, 8.12, 8.18, 8.19, 28.1, 28.2_
  - [ ]* 12.3 Write property test for Property 12: Create/read round trip for Cards, Comments, and serialization (T-44)
    - **Property 12: Create/read round trip for Cards, Comments, and serialization**
    - **Validates: Requirements 6.12, 8.17, 16.5**
    - Create random Cards and Comments, read them back, and assert equal fields; dump then load Board, Column, Card, Comment and Notification payloads and assert equivalence.
    - Seeded loop (stdlib random, fixed seed, at least 100 iterations); no property-testing library (tech.md TC-02, TC-03).
    - Files: backend/tests/unit/comments/test_comments_properties.py
    - _Requirements: 6.12, 8.17, 16.5_

- [x] 13. Analytics Blueprint
  - [x] 13.1 Implement the analytics Blueprint (T-45)
    - `AnalyticsQuerySchema` (both dates or neither, `YYYY-MM-DD`, end not before start, at most 366 days, default last 7 days UTC); `get_board_analytics_service` computes `cards_per_column`, `completed_this_week` (Monday 00:00 UTC of the ISO week, non-deleted), `member_activity` (every current member, 0 included), `activity_per_day` (every day present) with SQLAlchemy joins and aggregates (BE-03); Admin only; route `GET /api/boards/<id>/analytics`.
    - Files: backend/app/blueprints/analytics/__init__.py, backend/app/blueprints/analytics/schema.py, backend/app/blueprints/analytics/service.py, backend/app/blueprints/analytics/routes.py, backend/app/__init__.py
    - _Requirements: 2.3, 2.6, 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.10, 24.7, 24.8_
  - [x] 13.2 Write analytics service and route tests (T-46)
    - Success and failure per service function; Member and Guest 403; invalid or single date 400; per-Column sum equals the Card total; per-day sum equals events in range; Sunday-before-week excluded; soft-deleted Cards and their events excluded; query count at most 5 for 5 Columns and 50 Cards (BE-03).
    - Files: backend/tests/unit/analytics/test_analytics_service.py, backend/tests/unit/analytics/test_analytics_routes.py
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8, 11.9, 11.10, 24.7, 24.8, 28.1_
  - [ ]* 13.3 Write property test for Property 10: Analytics sums (T-47)
    - **Property 10: Analytics sums**
    - **Validates: Requirements 11.8, 11.9**
    - Generate random Boards and events and assert both sums of the analytics response.
    - Seeded loop (stdlib random, fixed seed, at least 100 iterations); no property-testing library (tech.md TC-02, TC-03).
    - Files: backend/tests/unit/analytics/test_analytics_properties.py
    - _Requirements: 11.8, 11.9_
  - [ ]* 13.4 Write property test for Property 14: Completed-this-week window (T-48)
    - **Property 14: Completed-this-week window**
    - **Validates: Requirements 24.7, 24.8**
    - Generate random `completed_at` values across week boundaries and assert a Card counts if and only if on or after Monday 00:00 UTC and not deleted.
    - Seeded loop (stdlib random, fixed seed, at least 100 iterations); no property-testing library (tech.md TC-02, TC-03).
    - Files: backend/tests/unit/analytics/test_analytics_properties.py
    - _Requirements: 24.7, 24.8_

- [x] 14. Backend integration
  - [x] 14.1 Register all eight Blueprints and the health route in create_app (T-49)
    - Ensure `create_app()` calls `register_blueprint` exactly eight times (auth, boards, columns, cards, comments, notifications, analytics, users), registers `health` and the error handlers, and imports no blueprint `routes.py` from another blueprint (ST-02, ST-04). Add `python -c "from app import create_app; create_app()"` as a smoke test.
    - Files: backend/app/__init__.py, backend/tests/unit/auth/test_app_factory.py
    - _Requirements: 20.6, 20.8, 29.1_
  - [x] 14.2 Write the route inventory, 401 sweep, envelope and scope tests (T-50)
    - Compare the method and path pairs of `app.url_map` (excluding `static`, parameter names normalised) with the 32 routes of Appendix A (PR-02); iterate every route for 401 without a token except the three public routes and the two Guest routes (BE-08); parametrised envelope test asserting exactly one of `data` or `error` and a non-empty string `error` for success, 400, 401, 403, 404 and 405 (NFR-04); unknown field gives 400; a CORS test that a foreign `Origin` receives no `Access-Control-Allow-Origin`.
    - Scope test: no route, model or module for attachments, labels, due dates, WebSockets, password reset or OAuth exists (R17.2, R17.3).
    - UUID path rule (R1.6, BE-04): over every route that has a path id, a non-UUID id with a valid token returns 400 with a non-empty `error` string, evaluated after authentication and before the existence check (one parametrised test).
    - Files: backend/tests/unit/auth/test_route_inventory.py, backend/tests/unit/auth/test_envelope_sweep.py, backend/tests/unit/auth/test_scope_limits.py, backend/tests/unit/auth/test_path_uuid.py
    - _Requirements: 1.6, 13.8, 13.9, 16.4, 17.2, 17.3, 17.4, 20.1, 20.2, 20.3, 20.4, 20.5, 20.9, 20.10, 20.11, 20.12_
  - [x] 14.3 Write the API-level end-to-end flow test (T-51)
    - `tests/e2e/test_core_flow.py`: register, login, create board, add Column "To Do" and "Done", create Card, move Card into "Done" (`completed_at` set), comment with a mention, read the notification, soft delete, analytics as Admin; assert envelope shapes at each step (TC-17).
    - Files: backend/tests/e2e/test_core_flow.py
    - _Requirements: 17.1, 28.1_
  - [x] 14.4 Create the load-test script and the RESULTS.md template (T-52)
    - Standard-library only script `backend/tests/load/load_test.py` taking the API URL as an argument: 200 virtual users on one Board of 5 Columns and 50 Cards for a 10-minute window; P95 must be taken from durations measured at the API server (TC-23). Do not run it and add no dependency.
    - `backend/tests/load/RESULTS.md` template with every field "NOT RECORDED" and status "not measured": Date, Script name and version, Railway plan, Gunicorn worker class and worker count, Database plan, P95 (ms). Never write a value that was not measured.
    - Files: backend/tests/load/load_test.py, backend/tests/load/RESULTS.md
    - _Requirements: 14.4, 14.5, 14.6, 15.1, 15.2_

- [x] 15. Checkpoint - backend complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 16. Frontend scaffold, API client and auth state
  - [x] 16.1 Create the Next.js project, dependency pins and style tooling (T-53)
    - `frontend/` with Next.js 15 App Router, React 19, TypeScript strict, Tailwind CSS 4; `package.json` with exact versions and only the TC-03 allowlist (runtime: `next`, `react`, `react-dom`, `react-hot-toast`), `package-lock.json` committed, `.nvmrc` with Node 22.
    - `app/globals.css` with `@import "tailwindcss";` and one `@theme` block holding the FE-12 palette tokens; Prettier (single quotes, 2 spaces, semicolons, width 100, tailwind plugin), ESLint (`next/core-web-vitals`, `no-explicit-any` error), `tsconfig.json` strict with the `@/` alias, Jest and Testing Library configuration; `frontend/.env.example` with `NEXT_PUBLIC_API_BASE_URL` and `API_BASE_URL`.
    - Files: frontend/package.json, frontend/package-lock.json, frontend/.nvmrc, frontend/tsconfig.json, frontend/next.config.ts, frontend/postcss.config.mjs, frontend/.prettierrc, frontend/eslint.config.mjs, frontend/jest.config.ts, frontend/app/globals.css, frontend/.env.example
    - _Requirements: 16.1, 29.6_
  - [x] 16.2 Implement API types, error class, toast helper, ordering helper and API client (T-54)
    - `types/api.ts` (FE-25, snake_case keys, no mapping layer); `lib/errors.ts` `ApiError` with `statusCode` and `message` only; `lib/toast.ts` (only importer of `react-hot-toast` besides the `<Toaster />`); `lib/ordering.ts` `ORDER_STEP` and `computeOrder` (FE-27).
    - `lib/apiClient.ts` (`get`, `post`, `patch`, `delete`): base URL from `API_BASE_URL` or `NEXT_PUBLIC_API_BASE_URL`, Bearer token option, unwrap `data`, throw `ApiError` (status 0 when no response), Guest mode sends only `X-Invite-Token`, only on the two Guest read requests (FE-23, FE-30).
    - Jest tests: 2xx unwrap, 404 and network error mapping, Guest header rules, `computeOrder` rules and 60 head insertions.
    - Files: frontend/types/api.ts, frontend/lib/errors.ts, frontend/lib/toast.ts, frontend/lib/ordering.ts, frontend/lib/apiClient.ts, frontend/__tests__/apiClient.test.ts, frontend/__tests__/ordering.test.ts
    - _Requirements: 7.16, 21.15, 21.16, 21.17, 22.7_
  - [x] 16.3 Implement AuthContext, route middleware and the root layout (T-55)
    - `context/AuthContext.tsx` with `{ user, token, isAuthenticated, login, logout, updateUser }`: `login` writes the `sevy_token` cookie (`path=/`, `SameSite=Lax`, `max-age=3600`), `logout` clears context and cookie and redirects, `updateUser` replaces the user and keeps the token (FE-19).
    - `middleware.ts` redirects unauthenticated requests for `/`, `/boards/*`, `/my-tasks`, `/profile` to `/login` except `/boards/<id>` with a non-empty `invite` parameter (FE-22, FE-30); `app/layout.tsx` Server Component reads the `sevy_token` cookie, calls `GET /api/users/me` when it exists, passes `initialToken` and `initialUser` to `AuthProvider` (both null with no cookie or on 401, FE-22), and renders `<Toaster />`.
    - RTL tests for `AuthContext` (login, logout, updateUser) and a middleware unit test.
    - Files: frontend/context/AuthContext.tsx, frontend/middleware.ts, frontend/app/layout.tsx, frontend/__tests__/AuthContext.test.tsx, frontend/__tests__/middleware.test.ts
    - _Requirements: 19.9, 21.8, 21.10, 21.11, 21.12, 21.13, 22.1_

- [x] 17. Shared components and hooks
  - [x] 17.1 Implement BaseButton, BaseBadge and BaseModal with tests (T-56)
    - `BaseButton` variants `primary`, `secondary`, `destructive` (literal class lookups, hover, focus-visible ring, disabled; the only file with a raw button element, ST-08); `BaseBadge` colors `gray`, `green`, `yellow`, `red`, `blue` (FE-12 mapping); `BaseModal` with Escape close, focus into the modal and focus return, `aria-modal`, using `useModalBehavior` from the next task.
    - One test per variant and color; icon-only controls require `aria-label`.
    - Files: frontend/components/shared/BaseButton.tsx, frontend/components/shared/BaseBadge.tsx, frontend/components/shared/BaseModal.tsx, frontend/__tests__/BaseButton.test.tsx, frontend/__tests__/BaseBadge.test.tsx, frontend/__tests__/BaseModal.test.tsx
    - _Requirements: 25.1, 25.2, 25.3, 25.4, 25.5, 25.6, 28.3_
  - [x] 17.2 Implement useModalBehavior and useDebouncedValue with tests (T-57)
    - `hooks/useModalBehavior.ts` (Escape key, focus move and return, listener cleanup); `hooks/useDebouncedValue.ts` with fake-timer tests (299 ms no update, 300 ms update).
    - Files: frontend/hooks/useModalBehavior.ts, frontend/hooks/useDebouncedValue.ts, frontend/__tests__/useModalBehavior.test.tsx, frontend/__tests__/useDebouncedValue.test.tsx
    - _Requirements: 10.10, 25.4, 25.5, 28.3_
  - [x] 17.3 Implement useErrorHandler with tests (T-58)
    - `hooks/useErrorHandler.ts`: the FE-24 table (401 toast, logout and redirect; 403; 404; 400 and 409 server string; 500+ and status 0 generic) through `lib/toast.ts`; a test per row, and a test that a 401 from login is not routed to the session-expired branch.
    - Files: frontend/hooks/useErrorHandler.ts, frontend/__tests__/useErrorHandler.test.tsx
    - _Requirements: 22.1, 22.2, 22.3, 22.4, 22.5, 28.3_
  - [x] 17.4 Implement useNotifications with tests (T-59)
    - `hooks/useNotifications.ts`: poll every `NOTIFICATION_POLL_MS = 30_000`, clear the interval on unmount, no polling when not authenticated, `unreadCount` from `unread_count`, polling failures keep the previous page without a toast except 401 (FE-28). Fake-timer tests: 0 calls at 29 999 ms, 1 at 30 000 ms, none after unmount.
    - Files: frontend/hooks/useNotifications.ts, frontend/__tests__/useNotifications.test.tsx
    - _Requirements: 9.14, 28.3_
  - [x] 17.5 Implement useDragAndDrop with tests (T-60)
    - `hooks/useDragAndDrop.ts`: native HTML5 events only, optimistic update, `computeOrder`, call `PATCH /api/cards/<id>/position`, replace the Card with the response, `router.refresh()` when `rebalanced`, restore the original `column_id` and `order` and show the error toast on any `ApiError` (403, 409, status 0), reset state when a new `initialBoard` arrives (FE-26).
    - Tests with a mocked failing request asserting state equals the pre-drop state.
    - Files: frontend/hooks/useDragAndDrop.ts, frontend/__tests__/useDragAndDrop.test.tsx
    - _Requirements: 7.16, 7.17, 7.18, 7.19, 7.20, 28.3_
  - [x] 17.6 Implement useCardSearch with tests (T-61)
    - `hooks/useCardSearch.ts` composing `useDebouncedValue` (`SEARCH_DEBOUNCE_MS = 300`) with `GET /api/cards?q=<term>&board_id=<id>`; no request for empty or whitespace input; ignore a stale response (FE-29). Fake-timer tests: 299 ms none, 300 ms one request.
    - Files: frontend/hooks/useCardSearch.ts, frontend/__tests__/useCardSearch.test.tsx
    - _Requirements: 10.10, 10.11_

- [x] 18. Pages and feature components
  - [x] 18.1 Build the /register and /login pages with tests (T-62)
    - Controlled forms inside the page layout with client-side validation mirroring BE-05 (email, password at least 8, username 3-30 of letters, digits, underscore, non-empty name); register redirects to `/login` on 201; login calls `login()` with `access_token` and `user` and redirects to `/`; invalid credentials show "Invalid credentials" inline and no session-expired toast.
    - RTL tests for validation messages, redirects and the inline error.
    - Files: frontend/app/register/page.tsx, frontend/app/login/page.tsx, frontend/__tests__/auth-pages.test.tsx
    - _Requirements: 13.4, 21.6, 21.7, 21.8, 21.9, 22.6_
  - [x] 18.2 Build Header and NotificationBell and mount them in the layout (T-63)
    - `components/layout/Header.tsx` (brand, links to `/`, `/my-tasks`, `/profile`, logout `BaseButton`) and `components/notifications/NotificationBell.tsx` (badge with `unread_count`, hidden at 0, no fetch before the first 30-second interval (FE-28), items link to `/boards/<board_id>?card=<card_id>` and mark read, see U-10); show both on every authenticated page and only the brand in Guest mode.
    - RTL tests: badge shows `unread_count` not `items.length`, hidden at 0, the item `href` is `/boards/<board_id>?card=<card_id>`.
    - Files: frontend/components/layout/Header.tsx, frontend/components/notifications/NotificationBell.tsx, frontend/app/layout.tsx, frontend/__tests__/NotificationBell.test.tsx
    - _Requirements: 9.16, 9.17, 21.12, 21.14_
  - [x] 18.3 Build the Dashboard page with BoardCard and BoardForm (T-64)
    - `app/page.tsx` Server Component reading the cookie, fetching `GET /api/boards` and listing the Boards of all the user's Teams (R4.5), rendering `BoardCard` tiles; `BoardForm` (controlled, in `BaseModal`) posting `POST /api/boards` without `team_id`, so a Board created in the UI belongs to the personal Team (R4.2; another Team only through the API), then `router.refresh()`; empty state; page at most 120 lines (ST-05).
    - RTL tests for `BoardForm` validation and submit.
    - Files: frontend/app/page.tsx, frontend/components/board/BoardCard.tsx, frontend/components/board/BoardForm.tsx, frontend/__tests__/BoardForm.test.tsx
    - _Requirements: 4.1, 4.2, 4.5, 21.2, 21.3_
  - [x] 18.4 Build the Board Detail page and Kanban components (T-65)
    - `app/boards/[id]/page.tsx` Server Component fetching `GET /api/boards/<id>`; `KanbanBoard` (owns `useDragAndDrop` state), `BoardColumn` (only file with `onDragOver` and `onDrop`), `ColumnHeader`, `CardDragHandle` (only file with `draggable`), `CardItem`, `ColumnForm` and `CardForm` (inside `BaseModal`); the board scrolls horizontally in its own container; Columns and Cards shown in `order` ascending.
    - The page learns the signed-in user's role from `GET /api/boards/<id>/members` (the row whose `user_id` is the user's own) and passes `role` to Client Components; see 18.7 and D-04.
    - Hide Admin-only Column actions from Members (the API still enforces, R2.1). RTL tests for rendering order, forms and rollback display.
    - Files: frontend/app/boards/[id]/page.tsx, frontend/components/board/KanbanBoard.tsx, frontend/components/board/BoardColumn.tsx, frontend/components/board/ColumnHeader.tsx, frontend/components/board/CardDragHandle.tsx, frontend/components/board/ColumnForm.tsx, frontend/components/card/CardItem.tsx, frontend/components/card/CardForm.tsx, frontend/__tests__/KanbanBoard.test.tsx
    - _Requirements: 4.10, 5.1, 6.1, 7.15, 21.4_
  - [x] 18.5 Add CardSearch to the Board Detail page (T-66)
    - `components/card/CardSearch.tsx` (controlled, `maxLength` 100) using `useCardSearch`; results show `title`, `column_name` in a `BaseBadge` and a link to `/boards/<board_id>?card=<id>`; empty-result state; hidden in Guest mode.
    - Files: frontend/components/card/CardSearch.tsx, frontend/app/boards/[id]/page.tsx, frontend/__tests__/CardSearch.test.tsx
    - _Requirements: 10.10, 10.11_
  - [x] 18.6 Implement the Guest_Mode read-only Board view (T-67)
    - When `invite` is present the page makes no `GET /api/boards/<id>/members` request (role `guest`) and uses `inviteToken` only, never `Authorization`, writes no cookie and creates no session; `KanbanBoard` receives `isReadOnly` and renders no create, edit, delete, assign or drag control (no `CardDragHandle`); Comments read-only; 404 and 403 show the not-found state; no redirect to `/login` (FE-30).
    - RTL tests: read-only view has no `draggable` element and no form.
    - Files: frontend/app/boards/[id]/page.tsx, frontend/components/board/KanbanBoard.tsx, frontend/__tests__/guest-mode.test.tsx
    - _Requirements: 3.8, 21.11, 21.17_
  - [x] 18.7 Add the Admin-only analytics panel to Board Detail (T-68)
    - The Board payload has no role, so the page obtains the signed-in user's role from `GET /api/boards/<id>/members` (the row with the user's own `user_id`, open to every member, R12.7), passes `role` to Client Components, makes no members request in Guest_Mode (role `guest`, no JWT), and renders `AnalyticsPanel` and fetches `GET /api/boards/<id>/analytics` only for role `admin` (R11.11, design D-04).
    - The panel is the new file `components/board/AnalyticsPanel.tsx`, which is not listed in FE-02 or ST-07; recommendation: add it to both (not edited here, see ambiguity A-FE). No UI for member management or invite links (OD-14, FE-32).
    - Files: frontend/components/board/AnalyticsPanel.tsx, frontend/app/boards/[id]/page.tsx, frontend/__tests__/AnalyticsPanel.test.tsx
    - _Requirements: 11.11, 12.7_
  - [x] 18.8 Build Card_Detail_Modal and the Comment thread components (T-69)
    - `CardDetailModal` in `BaseModal` opened by a Card click (and by `?card=<id>`), loading `GET /api/cards/<id>/comments` into local state; `CommentList` renders replies under parents by `parent_id`, a tombstone shows "This comment was deleted" with its replies kept, an "edited" indicator when `updated_at` is later than `created_at`; `CommentItem` edit control only for the author with `aria-label`; `CommentForm` controlled, new and edited Comments appear without a reload (FE-31).
    - RTL tests for tombstone, edited indicator, create and edit.
    - Files: frontend/components/card/CardDetailModal.tsx, frontend/components/comments/CommentList.tsx, frontend/components/comments/CommentItem.tsx, frontend/components/comments/CommentForm.tsx, frontend/__tests__/CommentList.test.tsx
    - _Requirements: 8.13, 8.14, 8.15, 8.16, 21.5, 25.3_
  - [x] 18.9 Build the /my-tasks page with MyTaskRow (T-70)
    - `app/my-tasks/page.tsx` Server Component calling `GET /api/cards?assignee=me`, grouping `CardListItem` rows by `board_name`; `components/card/MyTaskRow.tsx` shows `title`, `column_name` in a `BaseBadge` and a `BaseButton` linking to `/boards/<board_id>?card=<id>`; empty-state message.
    - Files: frontend/app/my-tasks/page.tsx, frontend/components/card/MyTaskRow.tsx, frontend/__tests__/MyTaskRow.test.tsx
    - _Requirements: 18.10, 18.11, 21.1_
  - [x] 18.10 Build the /profile page (T-71)
    - Controlled form pre-populated from `useAuth()`, username read-only, sends `PATCH /api/users/me` with `name` and `email` only, calls `updateUser` with the response `user` and shows a success toast; uses `BaseButton`. RTL test that Header and form show the new name without a reload.
    - Files: frontend/app/profile/page.tsx, frontend/__tests__/profile-page.test.tsx
    - _Requirements: 19.7, 19.8, 19.9, 21.1_

- [x] 19. Checkpoint - frontend pages
  - Ensure all tests pass, ask the user if questions arise.

- [x] 20. Responsive and accessibility pass
  - [x] 20.1 Apply the responsive and accessibility pass and add the viewport helper (T-72)
    - Review every page and the Card_Detail_Modal at 375, 768 and 1280 px: mobile-first classes, no arbitrary values, `min-h-11` controls, no horizontal page scroll, Kanban scrolls inside its container (FE-13); every icon-only button has `aria-label`; all buttons are `BaseButton`.
    - `frontend/e2e/helpers/viewport.ts` exporting the three widths and an assertion `scrollWidth <= innerWidth` used by `pages.spec.ts`.
    - Files: frontend/e2e/helpers/viewport.ts, frontend/components/ (class fixes only), frontend/app/ (class fixes only)
    - _Requirements: 23.1, 23.2, 23.3, 25.1, 25.2, 25.6_

- [x] 21. Playwright end-to-end suite
  - [x] 21.1 Create the Playwright configuration and API helpers (T-73)
    - `playwright.config.ts` with `baseURL` from `PLAYWRIGHT_BASE_URL`, desktop and mobile projects (the mobile project runs only `pages.spec.ts`), HTML reporter output `playwright-report/` kept in the repository; `e2e/helpers/api.ts` creating a user through the API with unique email and username for every test. No `waitForTimeout` anywhere.
    - Add an npm script `test:e2e` that runs `playwright test --repeat-each=3` (configuration only; it is not run against a live URL by any task).
    - Files: frontend/playwright.config.ts, frontend/e2e/helpers/api.ts, frontend/package.json
    - _Requirements: 28.6, 28.7, 28.8_
  - [x] 21.2 Write e2e/auth.spec.ts (T-74)
    - Four scenarios: successful login redirect, invalid credentials error, unauthenticated redirect to `/login`, post-logout redirect (cookie gone). Optional fifth in the same file: an invite link created through the API opens `/boards/<id>?invite=<token>` read-only without redirect. Web-first assertions only.
    - Files: frontend/e2e/auth.spec.ts
    - _Requirements: 3.8, 21.8, 21.9, 21.11, 21.12, 21.13, 28.4_
  - [x] 21.3 Write e2e/kanban.spec.ts (T-75)
    - The eight steps of TG-02: log in, create a Board, add "To Do", add "Done", create a Card in "To Do", drag it to "Done", reload, assert it is still in "Done"; own user per test; use `waitForResponse` or `expect.poll`, never fixed sleeps.
    - Files: frontend/e2e/kanban.spec.ts
    - _Requirements: 7.15, 28.5, 28.8_
  - [x] 21.4 Write e2e/pages.spec.ts (T-76)
    - Visit `/register`, `/login`, `/`, `/boards/[id]`, `/my-tasks`, `/profile` and open the Card_Detail_Modal at desktop and mobile widths; assert no horizontal overflow at 375, 768 and 1280 px with the viewport helper.
    - Files: frontend/e2e/pages.spec.ts
    - _Requirements: 21.1, 23.1, 23.2, 23.3, 27.9_

- [x] 22. Repository documentation
  - [x] 22.1 Write README.md with a project brief and screenshot placeholders (T-77)
    - Sections of R29.7: overview, AI workflow summary, features implemented, technologies, local run steps, test steps for pytest, `npm test` and Playwright, and a "Screenshots to capture" list (Postman for all 8 Blueprints, each major page, a Card being dragged, the Playwright report) with placeholders only; no URLs, no fake screenshots.
    - Project brief (R29.8): overview, roles (Team Admin, Team Member, Guest), core features, tech stack and at least two non-functional requirements (NFR-01 target not measured, NFR-02).
    - Files: README.md
    - _Requirements: 17.1, 29.7, 29.8_
  - [x] 22.2 Create the guideline violation report skeleton (T-78)
    - `guidelines/VIOLATIONS.md` with the `### V-nn` entry template (guideline ID, file and line, what the AI produced, the fix) and a before/after table with empty measured numbers. Do not add example violations; real entries are added when found.
    - Files: guidelines/VIOLATIONS.md
    - _Requirements: 29.5_
  - [x] 22.3 Add documentation checker scripts (T-79)
    - `backend/tools/check_guidelines.py` (ST-12 guideline checker), `backend/tools/check_changelog.py` (TC-21 round and label checker) and `backend/tools/check_traceability.py` (every `R<N>.<k>` of requirements.md appears in design.md and tasks.md). Read-only scripts, stdlib only, exit non-zero on failure.
    - Files: backend/tools/check_guidelines.py, backend/tools/check_changelog.py, backend/tools/check_traceability.py
    - _Requirements: 29.2, 29.3, 29.4_
  - [x] 22.4 Copy the final specs to the submission folder (T-80)
    - When the four spec files are final, copy `.kiro/specs/task-management-app/{requirements,design,tasks,CHANGELOG}.md` unchanged to `specs/` (the working copy is the source, ST-01 layout note). Run `check_traceability.py` against the copy.
    - Files: specs/requirements.md, specs/design.md, specs/tasks.md, specs/CHANGELOG.md
    - _Requirements: 29.2_

- [x] 23. Final checkpoint - all automated checks
  - Ensure all tests pass, ask the user if questions arise.
  - Coverage thresholds of TC-17 are configured and must pass when the suite is run: `pytest -v --cov=app --cov-fail-under=85` (at least 85 percent overall) and `coverage report --include="app/blueprints/*/service.py" --fail-under=90` (at least 90 percent for every `service.py`).
  - The Playwright `--repeat-each=3` setting (task 21.1) is configuration only; running it against the live Vercel URL is a manual step.

## Notes

- Requirement 28 mapping: every service function has at least one success and one failure test (R28.1, tasks 5.2, 6.2, 8.5, 9.2, 10.10, 11.5, 12.2, 13.2, 14.3); comments tests cover 201, 400, 401 and 403 (R28.2, task 12.2); RTL tests cover BaseButton, BaseBadge, BaseModal, useDragAndDrop, useNotifications and useDebouncedValue (R28.3, tasks 17.1, 17.2, 17.4, 17.5). Nothing here was run.

- Only the property tests carry the `*` marker (optional). Every other test sub-task is mandatory because Requirement 28 requires the three test layers.
- Task IDs `T-NN` are sequential over leaf tasks and appear at the end of each title; the Kiro number (for example 8.2) is the checklist position. Both are used in the coverage tables.
- Each leaf task lists `Files:` (ST-12) and `_Requirements:` (bare `N.k` equals `R<N>.<k>`).
- Property tests are seeded loops in pytest or Jest (fixed seed, at least 100 iterations); no property-testing library is added (tech.md TC-02, TC-03).
- Test tasks never run against a live URL and no task deploys, enters secrets, records a measurement or commits; see "Manual steps outside the task list".
- Ambiguity A-FE: the Admin-only analytics panel needs a component file that structure.md and FE-02 do not list; the plan adds `components/board/AnalyticsPanel.tsx` inside an existing folder. Ambiguity A-TOOLS: ST-01 fixes the repository root, so checker scripts live in `backend/tools/`.

## Task Dependency Graph

```json
{
  "waves": [
    {
      "id": 0,
      "tasks": [
        "1.1",
        "16.1"
      ]
    },
    {
      "id": 1,
      "tasks": [
        "1.2",
        "16.2"
      ]
    },
    {
      "id": 2,
      "tasks": [
        "2.1",
        "16.3"
      ]
    },
    {
      "id": 3,
      "tasks": [
        "2.2",
        "17.1"
      ]
    },
    {
      "id": 4,
      "tasks": [
        "2.3",
        "17.2"
      ]
    },
    {
      "id": 5,
      "tasks": [
        "3.1",
        "17.3"
      ]
    },
    {
      "id": 6,
      "tasks": [
        "3.2",
        "17.4"
      ]
    },
    {
      "id": 7,
      "tasks": [
        "3.3",
        "17.5"
      ]
    },
    {
      "id": 8,
      "tasks": [
        "3.4",
        "17.6"
      ]
    },
    {
      "id": 9,
      "tasks": [
        "4.1",
        "18.1"
      ]
    },
    {
      "id": 10,
      "tasks": [
        "4.2",
        "18.2"
      ]
    },
    {
      "id": 11,
      "tasks": [
        "4.3",
        "18.3"
      ]
    },
    {
      "id": 12,
      "tasks": [
        "5.1",
        "18.4"
      ]
    },
    {
      "id": 13,
      "tasks": [
        "5.2",
        "18.5"
      ]
    },
    {
      "id": 14,
      "tasks": [
        "5.3",
        "18.6"
      ]
    },
    {
      "id": 15,
      "tasks": [
        "6.1",
        "18.7"
      ]
    },
    {
      "id": 16,
      "tasks": [
        "6.2",
        "18.8"
      ]
    },
    {
      "id": 17,
      "tasks": [
        "8.1",
        "18.9"
      ]
    },
    {
      "id": 18,
      "tasks": [
        "8.2",
        "18.10"
      ]
    },
    {
      "id": 19,
      "tasks": [
        "8.3",
        "20.1"
      ]
    },
    {
      "id": 20,
      "tasks": [
        "8.4",
        "21.1"
      ]
    },
    {
      "id": 21,
      "tasks": [
        "8.5",
        "21.2"
      ]
    },
    {
      "id": 22,
      "tasks": [
        "8.6",
        "21.3"
      ]
    },
    {
      "id": 23,
      "tasks": [
        "8.7",
        "21.4"
      ]
    },
    {
      "id": 24,
      "tasks": [
        "9.1"
      ]
    },
    {
      "id": 25,
      "tasks": [
        "9.2"
      ]
    },
    {
      "id": 26,
      "tasks": [
        "10.1"
      ]
    },
    {
      "id": 27,
      "tasks": [
        "10.2"
      ]
    },
    {
      "id": 28,
      "tasks": [
        "10.3"
      ]
    },
    {
      "id": 29,
      "tasks": [
        "10.4"
      ]
    },
    {
      "id": 30,
      "tasks": [
        "10.5"
      ]
    },
    {
      "id": 31,
      "tasks": [
        "10.6"
      ]
    },
    {
      "id": 32,
      "tasks": [
        "10.7"
      ]
    },
    {
      "id": 33,
      "tasks": [
        "10.8"
      ]
    },
    {
      "id": 34,
      "tasks": [
        "10.9"
      ]
    },
    {
      "id": 35,
      "tasks": [
        "10.10"
      ]
    },
    {
      "id": 36,
      "tasks": [
        "11.1"
      ]
    },
    {
      "id": 37,
      "tasks": [
        "11.2"
      ]
    },
    {
      "id": 38,
      "tasks": [
        "11.3"
      ]
    },
    {
      "id": 39,
      "tasks": [
        "11.4"
      ]
    },
    {
      "id": 40,
      "tasks": [
        "11.5"
      ]
    },
    {
      "id": 41,
      "tasks": [
        "12.1"
      ]
    },
    {
      "id": 42,
      "tasks": [
        "12.2"
      ]
    },
    {
      "id": 43,
      "tasks": [
        "12.3"
      ]
    },
    {
      "id": 44,
      "tasks": [
        "13.1"
      ]
    },
    {
      "id": 45,
      "tasks": [
        "13.2"
      ]
    },
    {
      "id": 46,
      "tasks": [
        "13.3"
      ]
    },
    {
      "id": 47,
      "tasks": [
        "13.4"
      ]
    },
    {
      "id": 48,
      "tasks": [
        "14.1"
      ]
    },
    {
      "id": 49,
      "tasks": [
        "14.2"
      ]
    },
    {
      "id": 50,
      "tasks": [
        "14.3"
      ]
    },
    {
      "id": 51,
      "tasks": [
        "14.4"
      ]
    },
    {
      "id": 52,
      "tasks": [
        "22.1",
        "22.2",
        "22.3"
      ]
    },
    {
      "id": 53,
      "tasks": [
        "22.4"
      ]
    }
  ]
}
```

## Depends on a user decision

No OD or A entry is added by this plan. Each item below lists the tasks that use the narrowest behavior already stated in a guideline until the user decides.

| Item | Question | Tasks | Narrowest behavior used |
|---|---|---|---|
| U-01 | Should Columns be soft-deletable (DB-08 predicate on `board_columns`)? | 3.1, 3.3, 9.1 | Columns stay hard-deleted (R5.10); the partial index is created as DB-08 states and `deleted_at` is never written on Columns. |
| U-02 | What does `teams.owner_id` mean for a shared Team? | 3.1, 3.4, 8.5 | Only the personal Team is created by a route; tests create shared Teams with `owner_id` set to the creating user. No route creates shared Teams. |
| U-03 | R26.3 (mandatory) requires an index for case-insensitive Card title search. Is it created? | 3.2, 3.3, 10.8 | R26.3 is currently unmet for this part. Design D-07 recommends a trigram GIN index `ix_cards_title_lower_trgm` on `lower(title)` with the `pg_trgm` extension; it needs a change to database.md DB-08/DB-09 and a user decision first. No task creates it until then; search uses case-insensitive matching on `title` without that index. The other R26.3 indexes (including the 12 foreign-key indexes) are created in 3.1 to 3.3. |
| U-04 | Are Notifications of a soft-deleted Card hidden from the list? | 11.1, 11.5 | Hidden, following R6.16 and BE-15 (filter on `CardEntity.deleted_at IS NULL` through the Comment). |
| U-05 | Tombstone when a deleted middle Comment has only a deleted-reply chain | 12.1, 12.2 | Direct live replies only, as BE-15 states. |
| U-06 | PATCH or DELETE of an already-deleted Comment, reply to a deleted parent | 12.1, 12.2 | Not specified anywhere; the Comment is treated as not found (404 generic) and the case is recorded for the user. |
| U-07 / D-01 | Non-existent `team_id` in `POST /api/boards`: 400 or 403? | 8.1, 8.5 | 403 generic (`TeamAccessDeniedError`), per BE-15 and design D-01. |
| D-04 | Board Detail role source (Board payload has no role) | 18.4, 18.6, 18.7 | Role from `GET /api/boards/<id>/members` (own `user_id` row); no members request in Guest_Mode; `AnalyticsPanel` only for `admin`. |
| D-05 | Meaning of "stored Card equals one of the submitted versions" (R15.3) | 10.1, 10.10 | `update_card_service` takes a row lock (`with_for_update`) in one transaction; the final Card equals the last applied request. |
| D-06 | What the 3-query budget counts (R14.2) | 8.1, 8.5 | The Columns query and the Cards query (Assignee joined); the guard's Board and membership lookups are counted separately; no query per Column or Card. |
| D-07 | Trigram index for title search | 3.2, 3.3, 10.8 | No index and no `pg_trgm` extension is created (see U-03). |
| D-08 | Notification `message` text | 11.1, 11.5 | `<mentioner name> mentioned you on "<card title>"`, truncated to 255 characters. |
| U-08 | Dedicated exception for a Member deleting another user's Card | 10.1, 10.10 | `AdminAccessRequiredError` (BE-09). |
| U-09 | Body for a non-existent `invite_id` | 8.4, 8.5 | 404 `{"error": "Not found"}` (BE-10). |
| U-10 to U-12 | Notification and search links, empty bell for 30 s, silent polling failures | 18.2, 18.5, 17.4 | FE-28 and FE-29 text as written: `/boards/<board_id>?card=<card_id>`, no fetch on mount, no toast except 401. |
| U-13 / U-14 | User restore in layout, Guest 403 state, Board list item shape | 16.3, 18.6, 18.3 | FE-19, FE-22, FE-30 as written; `Board` type is `id`, `name`, `team_id`, `created_at`. |
| U-15 / U-19 | Invalid path UUID handling and double membership lookup | 4.1, 8.1 | BE-08 and BE-14 as written. |
| U-16 | ST-12 `T-<NN>` IDs versus Kiro numbering | all tasks | Both are kept: Kiro number plus `(T-NN)` suffix on every leaf title. |
| U-17 | P95 needs an access-log duration but the Procfile text has no log option | 14.4, 1.2 | Procfile kept exactly as TC-20; the load script only records durations and the measurement stays a manual step. |
| U-18 | CHANGELOG V2 to V5 lack the Prompt, Before and After labels (TC-21) | 22.3 | No task rewrites history; `check_changelog.py` reports the gap. |

## Manual steps outside the task list

Owner of every step: the user.

| Step | Criteria |
|---|---|
| Create the Railway API service and PostgreSQL database, set env variables and secrets, apply `flask db upgrade` through the release step | R27.1, R27.2, R27.8 |
| Create the Vercel project, set `API_BASE_URL` and `NEXT_PUBLIC_API_BASE_URL`, set CORS to the exact Vercel origin | R27.6, R27.7 |
| Verify `GET /api/health`, register, login and one authenticated request per Blueprint from Postman on the public URL | R27.3, R27.4, R27.5 |
| Open all seven screens on the live app at 375, 768 and 1280 px | R27.9 |
| Run `npx playwright test` and `--repeat-each=3` against the live Vercel URL, review and commit `playwright-report/` | R28.4, R28.5, R28.6, R28.7, R28.8 |
| Run the load test against a deployed API and fill `backend/tests/load/RESULTS.md` (record "not met" if above 300 ms) | R14.1, R14.6, R15.1, R15.2 |
| Capture the README screenshots (Postman for 8 Blueprints, each page, a Card being dragged, the Playwright report) | R29.7 |
| Record real violations in `guidelines/VIOLATIONS.md` | R29.5 |
| Create commits with the phase prefixes `spec:`, `guidelines:`, `feat(backend):`, `feat(frontend):`, `test:`, `docs:`, `chore(deploy):` | R29.9 |

## Requirement coverage

Generated from requirements.md by script. A cell lists task numbers (Kiro checklist numbers); "Manual steps" and "Depends on a user decision" mark criteria the agent cannot complete.

| Criterion | Tasks | Other |
|---|---|---|
| R1.1 | 4.1, 8.1, 8.5 | - |
| R1.2 | 4.1, 4.2, 8.1, 8.5 | - |
| R1.3 | 4.1, 8.1, 8.5 | - |
| R1.4 | 8.1, 8.5, 8.7 | - |
| R1.5 | 8.1, 8.2, 8.5 | - |
| R1.6 | 4.1, 8.5, 14.2 | - |
| R1.7 | 4.1, 4.2, 8.5 | - |
| R2.1 | 4.1, 8.5 | - |
| R2.2 | 8.5, 12.1, 12.2 | - |
| R2.3 | 8.1, 8.2, 8.4, 8.5, 13.1 | - |
| R2.4 | 8.5, 9.1, 10.1 | - |
| R2.5 | 8.5, 9.1, 9.2 | - |
| R2.6 | 8.1, 8.2, 8.4, 8.5, 9.1, 10.1, 13.1 | - |
| R2.7 | 8.1, 8.5 | - |
| R2.8 | 12.1, 12.2 | - |
| R2.9 | 8.5, 10.1 | - |
| R2.10 | 8.6 | - |
| R2.11 | 8.6 | - |
| R3.1 | 4.3, 8.4, 8.5 | - |
| R3.2 | 3.2, 4.3, 8.4, 8.5 | - |
| R3.3 | 4.1, 4.2, 4.3, 8.1 | - |
| R3.4 | 4.1, 4.2, 4.3 | - |
| R3.5 | 4.1, 4.2, 4.3 | - |
| R3.6 | 4.3, 8.4, 8.5 | - |
| R3.7 | 4.3, 8.4, 8.5 | - |
| R3.8 | 4.3, 18.6, 21.2 | - |
| R3.9 | 4.1, 4.2, 4.3 | - |
| R3.10 | 4.1, 4.2, 4.3 | - |
| R3.11 | 4.1, 4.2, 4.3 | - |
| R3.12 | 4.1, 4.2, 4.3 | - |
| R3.13 | 4.1, 4.2, 4.3 | - |
| R3.14 | 4.1, 4.2, 4.3 | - |
| R3.15 | 4.1, 4.2 | - |
| R4.1 | 8.1, 8.5, 18.3 | - |
| R4.2 | 8.1, 8.5, 18.3 | - |
| R4.3 | 8.1, 8.5 | - |
| R4.4 | 8.1, 8.5 | - |
| R4.5 | 8.1, 8.5, 18.3 | - |
| R4.6 | 8.1, 8.5 | - |
| R4.7 | 8.1, 8.5 | - |
| R4.8 | 8.1, 8.5 | - |
| R4.9 | 8.1, 8.5 | - |
| R4.10 | 18.4 | - |
| R5.1 | 9.1, 9.2, 18.4 | - |
| R5.2 | 2.3, 9.1, 9.2 | - |
| R5.3 | 2.3, 9.1, 9.2 | - |
| R5.4 | 9.1, 9.2 | - |
| R5.5 | 9.1, 9.2 | - |
| R5.6 | 9.1, 9.2 | - |
| R5.7 | 9.1, 9.2 | - |
| R5.8 | 9.1, 9.2 | - |
| R5.9 | 2.3, 9.1, 9.2 | - |
| R5.10 | 9.1, 9.2 | - |
| R5.11 | 9.1, 9.2 | - |
| R5.12 | 9.1, 9.2 | - |
| R5.13 | 9.1, 9.2, 10.4 | - |
| R5.14 | 9.1, 9.2 | - |
| R6.1 | 10.1, 10.10, 18.4 | - |
| R6.2 | 2.3, 10.10 | - |
| R6.3 | 10.1, 10.10 | - |
| R6.4 | 10.1, 10.10 | - |
| R6.5 | 10.1, 10.10 | - |
| R6.6 | 10.1, 10.10 | - |
| R6.7 | 10.1, 10.10 | - |
| R6.8 | 3.2, 3.4, 10.10 | - |
| R6.9 | 2.3, 10.1, 10.10 | - |
| R6.10 | 10.3, 10.4, 10.10 | - |
| R6.11 | 10.1, 10.10 | - |
| R6.12 | 12.3 | - |
| R6.13 | 10.1, 10.10 | - |
| R6.14 | 10.1, 10.10, 12.1, 12.2 | - |
| R6.15 | 10.1, 10.10 | - |
| R6.16 | 10.1, 10.2, 10.10 | - |
| R7.1 | 10.3, 10.10 | - |
| R7.2 | 10.3, 10.10 | - |
| R7.3 | 10.3, 10.10 | - |
| R7.4 | 10.3, 10.10 | - |
| R7.5 | 10.3, 10.10 | - |
| R7.6 | 10.3, 10.10 | - |
| R7.7 | 10.3, 10.10 | - |
| R7.8 | 2.3, 10.3, 10.10 | - |
| R7.9 | 10.3, 10.10 | - |
| R7.10 | 10.3, 10.10 | - |
| R7.11 | 10.3, 10.7 | - |
| R7.12 | 10.3, 10.5 | - |
| R7.13 | 10.3, 10.6, 10.10 | - |
| R7.14 | 10.3, 10.10 | - |
| R7.15 | 18.4, 21.3 | - |
| R7.16 | 16.2, 17.5 | - |
| R7.17 | 17.5 | - |
| R7.18 | 17.5 | - |
| R7.19 | 17.5 | - |
| R7.20 | 17.5 | - |
| R8.1 | 12.1, 12.2 | - |
| R8.2 | 12.1, 12.2 | - |
| R8.3 | 12.1, 12.2 | - |
| R8.4 | 12.1, 12.2 | - |
| R8.5 | 4.1, 12.1, 12.2 | - |
| R8.6 | 12.1, 12.2 | - |
| R8.7 | 12.1, 12.2 | - |
| R8.8 | 12.1, 12.2 | - |
| R8.9 | 12.1, 12.2 | - |
| R8.10 | 12.1, 12.2 | - |
| R8.11 | 12.1, 12.2 | - |
| R8.12 | 12.1, 12.2 | - |
| R8.13 | 18.8 | - |
| R8.14 | 18.8 | - |
| R8.15 | 18.8 | - |
| R8.16 | 18.8 | - |
| R8.17 | 12.3 | - |
| R8.18 | 12.1, 12.2 | - |
| R8.19 | 12.1, 12.2 | - |
| R9.1 | 11.1, 11.2, 11.5 | - |
| R9.2 | 11.1, 11.2, 11.5 | - |
| R9.3 | 11.1, 11.2, 11.5 | - |
| R9.4 | 11.1, 11.2, 11.5 | - |
| R9.5 | 11.1, 11.5 | - |
| R9.6 | 11.1, 11.5 | - |
| R9.7 | 11.1, 11.3, 11.5 | - |
| R9.8 | 11.1, 11.5 | - |
| R9.9 | 11.1, 11.5 | - |
| R9.10 | 11.1, 11.5 | - |
| R9.11 | 11.1, 11.5 | - |
| R9.12 | 11.1, 11.5 | - |
| R9.13 | 11.1, 11.4, 11.5 | - |
| R9.14 | 17.4 | - |
| R9.15 | - | Depends on a user decision (Deferred by OD-04; no task implements it) |
| R9.16 | 18.2 | - |
| R9.17 | 18.2 | - |
| R10.1 | 10.8, 10.10 | - |
| R10.2 | 10.8, 10.10 | - |
| R10.3 | 10.8, 10.10 | - |
| R10.4 | 10.8, 10.10 | - |
| R10.5 | 10.8, 10.10 | - |
| R10.6 | 10.8, 10.9, 10.10 | - |
| R10.7 | 10.8, 10.9 | - |
| R10.8 | 10.8, 10.9 | - |
| R10.9 | 10.8, 10.10 | - |
| R10.10 | 17.2, 17.6, 18.5 | - |
| R10.11 | 17.6, 18.5 | - |
| R11.1 | 13.1, 13.2 | - |
| R11.2 | 13.1, 13.2 | - |
| R11.3 | 13.1, 13.2 | - |
| R11.4 | 13.1, 13.2 | - |
| R11.5 | 13.1, 13.2 | - |
| R11.6 | 13.1, 13.2 | - |
| R11.7 | 13.1, 13.2 | - |
| R11.8 | 13.2, 13.3 | - |
| R11.9 | 13.2, 13.3 | - |
| R11.10 | 13.1, 13.2 | - |
| R11.11 | 18.4, 18.7 | - |
| R12.1 | 8.2, 8.5 | - |
| R12.2 | 8.2, 8.5 | - |
| R12.3 | 8.2, 8.5 | - |
| R12.4 | 8.2, 8.5 | - |
| R12.5 | 8.2, 8.5, 11.4 | - |
| R12.6 | 8.2, 8.5, 11.4 | - |
| R12.7 | 8.2, 8.5 | - |
| R12.8 | 8.2, 8.5 | - |
| R12.9 | 8.2, 8.5 | - |
| R12.10 | 8.2, 8.3, 8.5 | - |
| R13.1 | 5.1, 5.2, 5.3 | - |
| R13.2 | 5.1, 5.2 | - |
| R13.3 | 5.1, 5.2, 5.3 | - |
| R13.4 | 5.1, 5.2, 18.1 | - |
| R13.5 | 5.1, 5.2 | - |
| R13.6 | 5.1, 5.2 | - |
| R13.7 | 5.1, 5.2 | - |
| R13.8 | 4.1, 4.2, 14.2 | - |
| R13.9 | 4.1, 14.2 | - |
| R13.10 | 5.1, 5.2 | - |
| R13.11 | 5.1, 5.2 | - |
| R13.12 | 4.1, 5.2 | - |
| R13.13 | 4.1, 4.2 | - |
| R13.14 | 4.1, 4.2 | - |
| R14.1 | - | Manual steps (TC-23 load-test measurement) |
| R14.2 | 8.1, 8.5 | - |
| R14.3 | 2.2 | - |
| R14.4 | 14.4 | - |
| R14.5 | 14.4 | - |
| R14.6 | 14.4 | Manual steps (TC-23 load-test measurement) |
| R15.1 | 14.4 | Manual steps (TC-23 load-test measurement) |
| R15.2 | 14.4 | Manual steps (TC-23 load-test measurement) |
| R15.3 | 10.1, 10.3, 10.10 | - |
| R15.4 | 10.3, 10.10 | - |
| R16.1 | 16.1 | - |
| R16.2 | 1.1 | - |
| R16.3 | 1.1, 3.3, 3.4 | - |
| R16.4 | 1.1, 14.2 | - |
| R16.5 | 12.3 | - |
| R17.1 | 14.3, 22.1 | - |
| R17.2 | 14.2 | - |
| R17.3 | 14.2 | - |
| R17.4 | 14.2 | - |
| R18.1 | 10.1, 10.10 | - |
| R18.2 | 10.1, 10.10 | - |
| R18.3 | 10.1, 10.10 | - |
| R18.4 | 10.1, 10.10 | - |
| R18.5 | 10.8, 10.10 | - |
| R18.6 | 10.8, 10.10 | - |
| R18.7 | 10.8, 10.10 | - |
| R18.8 | 10.8, 10.10 | - |
| R18.9 | 10.8, 10.10 | - |
| R18.10 | 18.9 | - |
| R18.11 | 18.9 | - |
| R18.12 | 10.1, 10.10 | - |
| R19.1 | 6.1, 6.2 | - |
| R19.2 | 6.1, 6.2 | - |
| R19.3 | 6.1, 6.2 | - |
| R19.4 | 6.1, 6.2 | - |
| R19.5 | 6.1, 6.2 | - |
| R19.6 | 6.1, 6.2 | - |
| R19.7 | 18.10 | - |
| R19.8 | 18.10 | - |
| R19.9 | 16.3, 18.10 | - |
| R20.1 | 2.1, 2.2, 14.2 | - |
| R20.2 | 2.2, 14.2 | - |
| R20.3 | 2.2, 14.2 | - |
| R20.4 | 2.1, 14.2 | - |
| R20.5 | 2.1, 8.1, 14.2 | - |
| R20.6 | 14.1 | - |
| R20.7 | 2.2 | - |
| R20.8 | 14.1 | - |
| R20.9 | 5.1, 6.1, 14.2 | - |
| R20.10 | 1.2, 14.2 | - |
| R20.11 | 2.1, 14.2 | - |
| R20.12 | 4.1, 4.2, 14.2 | - |
| R20.13 | 2.1 | - |
| R21.1 | 18.9, 18.10, 21.4 | - |
| R21.2 | 18.3 | - |
| R21.3 | 18.3 | - |
| R21.4 | 18.4 | - |
| R21.5 | 18.8 | - |
| R21.6 | 18.1 | - |
| R21.7 | 18.1 | - |
| R21.8 | 16.3, 18.1, 21.2 | - |
| R21.9 | 18.1, 21.2 | - |
| R21.10 | 16.3 | - |
| R21.11 | 16.3, 18.6, 21.2 | - |
| R21.12 | 16.3, 18.2, 21.2 | - |
| R21.13 | 16.3, 21.2 | - |
| R21.14 | 18.2 | - |
| R21.15 | 16.2 | - |
| R21.16 | 16.2 | - |
| R21.17 | 16.2, 18.6 | - |
| R22.1 | 16.3, 17.3 | - |
| R22.2 | 17.3 | - |
| R22.3 | 17.3 | - |
| R22.4 | 17.3 | - |
| R22.5 | 17.3 | - |
| R22.6 | 18.1 | - |
| R22.7 | 16.2 | - |
| R23.1 | 20.1, 21.4 | - |
| R23.2 | 20.1, 21.4 | - |
| R23.3 | 20.1, 21.4 | - |
| R24.1 | 3.1, 3.2, 3.4, 9.1 | - |
| R24.2 | 10.3, 10.10 | - |
| R24.3 | 10.1, 10.10 | - |
| R24.4 | 10.3, 10.10 | - |
| R24.5 | 10.3, 10.10 | - |
| R24.6 | 9.1, 9.2 | - |
| R24.7 | 13.1, 13.2, 13.4 | - |
| R24.8 | 13.1, 13.2, 13.4 | - |
| R25.1 | 17.1, 20.1 | - |
| R25.2 | 17.1, 20.1 | - |
| R25.3 | 17.1, 18.8 | - |
| R25.4 | 17.1, 17.2 | - |
| R25.5 | 17.1, 17.2 | - |
| R25.6 | 17.1, 20.1 | - |
| R26.1 | 3.1, 3.2, 3.4 | - |
| R26.2 | 3.2, 3.4 | - |
| R26.3 | 3.3, 3.4 | Depends on a user decision (D-07) for the title-search index; unmet until decided. The remaining indexes are created by 3.3 |
| R26.4 | 3.3, 3.4, 8.1 | - |
| R26.5 | 5.1, 5.2 | - |
| R26.6 | 3.1, 3.2, 3.4 | - |
| R26.7 | 3.1, 3.2, 3.3, 3.4, 9.1, 10.4, 10.10 | - |
| R26.8 | 9.1, 9.2, 10.3, 10.4 | - |
| R26.9 | 3.1, 3.4 | - |
| R26.10 | 3.2, 3.4 | - |
| R26.11 | 3.2, 3.4 | - |
| R26.12 | 3.1, 3.4, 5.3 | - |
| R27.1 | 1.2 | Manual steps (Railway/Vercel deployment and verification) |
| R27.2 | 1.2 | Manual steps (Railway/Vercel deployment and verification) |
| R27.3 | 2.2 | Manual steps (Railway/Vercel deployment and verification) |
| R27.4 | - | Manual steps (Railway/Vercel deployment and verification) |
| R27.5 | - | Manual steps (Railway/Vercel deployment and verification) |
| R27.6 | - | Manual steps (Railway/Vercel deployment and verification) |
| R27.7 | 1.2 | Manual steps (Railway/Vercel deployment and verification) |
| R27.8 | 1.2 | Manual steps (Railway/Vercel deployment and verification) |
| R27.9 | 21.4 | Manual steps (Railway/Vercel deployment and verification) |
| R28.1 | 1.1, 5.2, 6.2, 8.5, 9.2, 10.10, 11.5, 12.2, 13.2, 14.3 | - |
| R28.2 | 12.2 | - |
| R28.3 | 17.1, 17.2, 17.3, 17.4, 17.5 | - |
| R28.4 | 21.2 | Manual steps (Playwright run against the live Vercel URL) |
| R28.5 | 21.3 | Manual steps (Playwright run against the live Vercel URL) |
| R28.6 | 21.1 | Manual steps (Playwright report evidence) |
| R28.7 | 21.1 | Manual steps (Playwright report committed and reviewed) |
| R28.8 | 21.1, 21.3 | Manual steps (Playwright run with --repeat-each=3) |
| R29.1 | 14.1 | - |
| R29.2 | 22.3, 22.4 | - |
| R29.3 | 22.3 | Depends on a user decision (CHANGELOG entries V2 to V5 lack Prompt/Before/After labels (user decision)) |
| R29.4 | 22.3 | - |
| R29.5 | 22.2 | Manual steps (violation entries from real reviews) |
| R29.6 | 1.2, 16.1 | - |
| R29.7 | 22.1 | Manual steps (screenshots) |
| R29.8 | 22.1 | - |
| R29.9 | - | Manual steps (commits with phase prefixes) |

## Route and page coverage

| Route or page | Tasks |
|---|---|
| POST /api/auth/register | 5.1, 5.2 |
| POST /api/auth/login | 5.1, 5.2 |
| POST /api/boards | 8.1, 8.5 |
| GET /api/boards | 8.1, 8.5 |
| GET /api/boards/<id> | 8.1, 8.5 |
| PATCH /api/boards/<id> | 8.1, 8.5 |
| DELETE /api/boards/<id> | 8.1, 8.5 |
| POST /api/boards/<id>/columns | 9.1, 9.2 |
| PATCH /api/columns/<id> | 9.1, 9.2 |
| DELETE /api/columns/<id> | 9.1, 9.2 |
| PATCH /api/boards/<id>/columns/reorder | 9.1, 9.2 |
| POST /api/columns/<id>/cards | 10.1, 10.10 |
| PATCH /api/cards/<id> | 10.1, 10.10 |
| DELETE /api/cards/<id> | 10.1, 10.10 |
| PATCH /api/cards/<id>/position | 10.3, 10.10 |
| POST /api/cards/<id>/comments | 12.1, 12.2 |
| GET /api/cards/<id>/comments | 12.1, 12.2 |
| PATCH /api/comments/<id> | 12.1, 12.2 |
| DELETE /api/comments/<id> | 12.1, 12.2 |
| GET /api/notifications | 11.1, 11.5 |
| PATCH /api/notifications/<id>/read | 11.1, 11.5 |
| GET /api/boards/<id>/analytics | 13.1, 13.2 |
| GET /api/users/me | 6.1, 6.2 |
| PATCH /api/users/me | 6.1, 6.2 |
| GET /api/health | 2.2, 14.1 |
| GET /api/cards | 10.8, 10.10 |
| POST /api/boards/<id>/members | 8.2, 8.5 |
| DELETE /api/boards/<id>/members/<user_id> | 8.2, 11.4, 8.5 |
| GET /api/boards/<id>/members | 8.2, 8.5 |
| PATCH /api/boards/<id>/members/<user_id> | 8.2, 8.5 |
| POST /api/boards/<id>/invite-links | 8.4, 8.5 |
| DELETE /api/boards/<id>/invite-links/<invite_id> | 8.4, 8.5 |
| /register | 18.1, 21.4 |
| /login | 18.1, 21.2, 21.4 |
| / | 18.3, 21.4 |
| /boards/[id] | 18.4, 18.5, 18.6, 18.7, 21.3, 21.4 |
| /my-tasks | 18.9, 21.4 |
| /profile | 18.10, 21.4 |
| Card_Detail_Modal | 18.8, 21.4 |

## Property coverage

| Property | Title | Validates | Task |
|---|---|---|---|
| Property 1 | Active order stays unique, strictly increasing, and positive | 5.13, 6.10, 26.7, 26.8 | 10.4 (T-30) |
| Property 2 | Move round trip | 7.12 | 10.5 (T-31) |
| Property 3 | Move idempotence | 7.13 | 10.6 (T-32) |
| Property 4 | Card count invariant under move | 7.11 | 10.7 (T-33) |
| Property 5 | Role monotonicity and determinism | 2.10, 2.11 | 8.6 (T-23) |
| Property 6 | Board isolation | 1.4 | 8.7 (T-24) |
| Property 7 | Access Resolution Table totality | 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13, 3.14 | 4.3 (T-12) |
| Property 8 | Notification deduplication and no self-notification | 9.1, 9.2, 9.3, 9.4 | 11.2 (T-38) |
| Property 9 | Search soundness, completeness, and idempotence | 10.6, 10.7, 10.8 | 10.9 (T-35) |
| Property 10 | Analytics sums | 11.8, 11.9 | 13.3 (T-47) |
| Property 11 | At-least-one-Admin invariant | 12.10 | 8.3 (T-20) |
| Property 12 | Create/read round trip for Cards, Comments, and serialization | 6.12, 8.17, 16.5 | 12.3 (T-44) |
| Property 13 | Soft-delete retention | 6.16 | 10.2 (T-28) |
| Property 14 | Completed-this-week window | 24.7, 24.8 | 13.4 (T-48) |
| Property 15 | Pagination arithmetic | 9.7 | 11.3 (T-39) |
| Property 16 | Username normalization uniqueness | 13.1, 13.3, 26.12 | 5.3 (T-15) |
