---
inclusion: fileMatch
fileMatchPattern: "backend/app/**/*.py"
---

# Sevy Backend Guidelines (Flask)

Backend guidelines for **Sevy**: Flask 3 API, one Blueprint per feature, Marshmallow validation, SQLAlchemy services, JWT auth, Team-based authorization.
Eight sections: **Blueprint Structure · Input Validation · Response Envelope · Authentication and Access · Error Handling · Auth and Password Handling · FLOAT Ordering Allocation · Retention and Bootstrap Behavior**.
Every guideline has **RULE**, **RATIONALE**, **EXAMPLE**, and a **VERIFY** line (command, pytest, or count, run from the repository root). IDs are `BE-nn` (BE-01 to BE-15). BE-13 to BE-15 are appended after BE-12 and follow file order.

Scope: this file owns Blueprints, route-handler rules, request schemas and their limits, output schemas and serialization shapes, access decorators, Team authorization in services, the response envelope and status/body policy, error handling, authentication and password handling, JWT settings, the server-side FLOAT ordering allocation and rebalance algorithm, and service behavior for retention (soft delete, tombstones, activity events, notification cleanup) and registration bootstrap.
Not owned here: tables, columns, constraints, indexes, relationships and the deletion policy belong to `database.md` and are only referenced. Frontend behavior, including the client-side `order` computation in `lib/ordering.ts`, belongs to `frontend.md`. Product behavior and acceptance criteria are in `.kiro/specs/task-management-app/requirements.md` (referred to below as `requirements.md`). Tools and versions are in `tech.md`; folder tree, import direction and naming are in `structure.md` (ST-02, ST-03, ST-04, ST-10) and are referenced here, not repeated.

---

## 1. Blueprint Structure

### BE-01 — One Blueprint per feature, three working files
- **RULE:** Each feature is a Blueprint under `backend/app/blueprints/<feature>/` with `routes.py`, `service.py`, `schema.py` (plus an `__init__.py` that only defines `<feature>_bp`). The eight required features are `auth`, `boards`, `columns`, `cards`, `comments`, `notifications`, `analytics`, `users`. `GET /api/health` lives in `app/health.py`, not in a ninth Blueprint.
- **RATIONALE:** Identical layout per feature; the agent always knows where code goes.
- **EXAMPLE:** `app/blueprints/cards/{routes,service,schema}.py`, with `cards_bp` registered in `create_app()`.
- **VERIFY:**
  `ls backend/app/blueprints | wc -l` → `8`;
  `for d in backend/app/blueprints/*/; do ls $d | grep -cE "^(routes|service|schema)\.py$"; done` prints `3` eight times;
  `grep -c "register_blueprint" backend/app/__init__.py` → `8`.

### BE-02 — A route handler is at most 5 lines
- **RULE:** A route handler body is at most 5 lines. It validates input, calls one service function, and returns the envelope. It contains no business logic, no database queries, and no error handling (no `if`, `for`, `while`, `try`, `except`, `raise`, `db.session`). Decorators are not counted. The first handler argument is supplied by the guard decorator of BE-08 (`current_user` for `@token_required`, `access` for `@board_access_required(allow_guest_read=True)`).
- **RATIONALE:** Thin handlers keep the logic in services you can unit-test without Flask, and "at most 5 lines, calls a service" can be checked mechanically in seconds.
- **EXAMPLE:**
```python
# app/blueprints/cards/routes.py
@cards_bp.route('/cards/<card_id>/position', methods=['PATCH'])
@token_required
def move_card_route(current_user, card_id):
    data = CardPositionSchema().load(request.get_json(silent=True) or {})
    result = move_card_service(card_id, data, current_user.id)
    return success(CardMoveResultSchema().dump(result))
```
- **VERIFY:**
  `for f in backend/app/blueprints/*/routes.py; do awk '/^def /{if(infn&&n>5)print FILENAME": "name" has "n" lines"; infn=1; n=0; name=$2; next} /^[^ \t#@]/{if(infn&&n>5)print FILENAME": "name" has "n" lines"; infn=0} infn&&/^[ \t]+[^ \t]/{n++} END{if(infn&&n>5)print FILENAME": "name" has "n" lines"}' $f; done` → no output;
  `grep -nE "^\s+(if|for|while|try|except|raise)\b|db\.session|\.query\b" backend/app/blueprints/*/routes.py | wc -l` → `0`.

### BE-03 — Services own the work
- **RULE:** `service.py` holds all business logic: loading records, Team authorization (BE-09), ordering (BE-14), mention notifications, activity events, commits. Service functions take plain arguments (`user_id`, the resolved `access` object of BE-08, validated `data`), return model instances or dicts, and never import `flask`. Cross-feature effects call the other feature's service function (mention notifications created while storing a Comment go through `create_mention_notifications_service`). Analytics totals are computed with SQLAlchemy joins and aggregates (`func.count`, `.join(...)`) inside `analytics/service.py`, never by looping over fetched rows.
- **RATIONALE:** Plain-Python services are testable without a request context, and aggregation in SQL keeps analytics at a fixed number of queries.
- **EXAMPLE:** `move_card_service(card_id, data, user_id)` loads the card (404 when missing or soft-deleted), calls `require_team_member_service` for the card's Board, applies BE-14, sets or clears `completed_at` per requirements.md Requirement 24, records a `card_moved` Activity_Event, commits, and returns `{ "card": card, "rebalanced": False }`.
- **VERIFY:**
  `grep -rnE "^(from|import) flask" backend/app/blueprints/*/service.py | wc -l` → `0`;
  `grep -cE "\.join\(|func\.count" backend/app/blueprints/analytics/service.py` → ≥ `1`;
  pytest asserts `GET /api/boards/<id>/analytics` on a board with 5 columns and 50 cards issues ≤ 5 SQL queries.

---

## 2. Input Validation

### BE-04 — Validate before the service runs
- **RULE:** Every JSON body and every query string is parsed by a Marshmallow schema from the same Blueprint's `schema.py` **before** the service is called; no service function ever sees unvalidated input. Input schemas use `unknown=RAISE`, so an undefined field is a 400. String fields are trimmed before length checks. A failure returns `400` with `{ "error": "<one string>" }`: the global handler (BE-11) normalizes the Marshmallow messages with one helper, `format_validation_error` in `app/utils/responses.py`: fields sorted alphabetically, each entry `<field>: <messages joined by ", ">`, entries joined by `" | "`. A path identifier that must be a UUID is validated by the guard decorators of BE-08 (after authentication, before the existence check) and fails as a 400 with `<name>: Not a valid UUID.`. Handlers read input only as `Schema().load(request.get_json(silent=True) or {})` or `Schema().load(request.args.to_dict())`.
- **RATIONALE:** Bad input never reaches the database, and one deterministic string is what the frontend `ApiError` carries as its `message`.
- **EXAMPLE:** `POST /api/columns/<id>/cards` with `{"title": ""}` → `400 { "error": "title: Length must be between 1 and 200." }`. `PATCH /api/cards/<id>/position` with `{"column_id": "abc", "order": -1}` → `400 { "error": "column_id: Not a valid UUID. | order: Must be greater than 0." }`.
- **VERIFY:**
  `grep -rnE "request\.(get_json|json|args|form)" backend/app/blueprints/*/routes.py | grep -v "\.load(" | wc -l` → `0`;
  `for f in backend/app/blueprints/*/schema.py; do grep -qE "^class \w+(Create|Update|Position|Reorder|Query|Add)Schema|^class (Register|Login)Schema" $f && ! grep -q "RAISE" $f && echo "NO RAISE: $f"; done` → no output;
  `grep -c "def format_validation_error" backend/app/utils/responses.py` → `1`;
  pytest: every POST/PATCH route has an invalid-payload test asserting status `400`, `isinstance(body["error"], str)`, exactly one of `data` / `error` present, a deterministic string for a fixed payload (the example above, byte for byte), an undefined field rejected with `400`, and no `Traceback` text in the body.

### BE-05 — The schema catalog and its limits
- **RULE:** These input schemas exist with exactly these constraints; boundary tests cover the minimum, the maximum, and one past each. The limits are **API input limits**. A database column length is storage capacity only and is never an API limit (it is `database.md`'s concern, DB-07).

| Schema | Blueprint | Constraints |
|---|---|---|
| `RegisterSchema` | auth | `name` 1–100; `username` 3–30 of letters, digits, underscore, compared case-insensitively and **normalized to lowercase before the service is called**; `email` valid, ≤ 254; `password` 8–128 (load-only) |
| `LoginSchema` | auth | `email` valid; `password` non-empty |
| `UserUpdateSchema` | users | `name` 1–100 and `email` valid ≤ 254, both optional, at least one required (an empty body is 400); `password`, `password_hash`, `username` and any other field are unknown and rejected |
| `BoardCreateSchema` | boards | `name` 1–100, not blank; `team_id` UUID, optional |
| `BoardUpdateSchema` | boards | `name` 1–100, not blank, the only field |
| `MemberAddSchema` | boards | `email` valid ≤ 254; `role` is `admin` or `member` (default `member`) |
| `MemberRoleUpdateSchema` | boards | `role` is `admin` or `member`, required |
| `InviteLinkCreateSchema` | boards | no fields; an empty body or `{}` is accepted; any field is rejected (`unknown=RAISE`) |
| `ColumnCreateSchema` | columns | `name` 1–100; `is_done` boolean (default `false`) |
| `ColumnUpdateSchema` | columns | `name` 1–100 and `is_done` boolean, both optional, at least one required |
| `ColumnReorderSchema` | columns | `column_id` UUID; `order` float `> 0` |
| `CardCreateSchema` | cards | `title` 1–200; `description` 0–5000, optional; `assignee_id` UUID or null, optional |
| `CardUpdateSchema` | cards | same fields as create, all optional, at least one required; `column_id`, `order`, `deleted_at`, `completed_at` are unknown and rejected |
| `CardPositionSchema` | cards | `column_id` UUID; `order` float `> 0` |
| `CardListQuerySchema` | cards | `assignee` equals `me`, optional; `q` 1–100 after trimming, not blank, optional and **does not require `board_id`**; `board_id` UUID, optional; at least one of `assignee` or `q` required (400 otherwise); matching is Card title only, case-insensitive |
| `CommentCreateSchema` | comments | `content` 1–2000 after trimming, not blank; `parent_id` UUID, optional |
| `CommentUpdateSchema` | comments | `content` 1–2000 after trimming, not blank |
| `NotificationQuerySchema` | notifications | `page` integer ≥ 1 (default 1); `per_page` integer 1–50 (default 10); a non-integer is 400 |
| `AnalyticsQuerySchema` | analytics | `start_date` and `end_date` in `YYYY-MM-DD`, both or neither; `end_date` not before `start_date`; range at most 366 days; when neither is given the service uses the last 7 days ending today (UTC) |

  Revoking an Invite Link and removing a Team member take no body and have no schema. When `board_id` is supplied to `CardListQuerySchema`, the service verifies Team access (BE-09): an existing inaccessible Board is 403 and a non-existent Board is 404, both with the generic body of BE-10.
- **RATIONALE:** Explicit limits turn "validate the input" into testable boundaries and stop the agent inventing its own, including reusing a storage length as an API maximum.
- **EXAMPLE:** `CardCreateSchema` accepts a 200-character title and rejects a 201-character one with `title: Length must be between 1 and 200.`; `ColumnCreateSchema` rejects a 101-character name with `name: Length must be between 1 and 100.`; `RegisterSchema` turns `Alice_01` into `alice_01` before `register_service` runs.
- **VERIFY:**
  `for s in RegisterSchema LoginSchema UserUpdateSchema BoardCreateSchema BoardUpdateSchema MemberAddSchema MemberRoleUpdateSchema InviteLinkCreateSchema ColumnCreateSchema ColumnUpdateSchema ColumnReorderSchema CardCreateSchema CardUpdateSchema CardPositionSchema CardListQuerySchema CommentCreateSchema CommentUpdateSchema NotificationQuerySchema AnalyticsQuerySchema; do grep -rqE "^class $s\(" backend/app/blueprints/*/schema.py || echo "MISSING $s"; done` → no output;
  `grep -rnE "Length\(.*max=255" backend/app/blueprints/*/schema.py | wc -l` → `0` (no storage length reused as an API limit);
  the comments tests include `201` success, `400` missing `content`, `401` no token, and `403` non-owner edit;
  pytest boundary tests: Board and Column name 100 passes and 101 fails, Card title 200 passes and 201 fails, `description` 5000 passes and 5001 fails, Comment `content` 2000 passes and 2001 fails, whitespace-only values fail, `per_page` 50 passes and 51 fails, `q` of 100 passes and 101 fails, `q` without `board_id` is accepted, and neither `assignee` nor `q` is 400.

### BE-06 — Responses are serialized only through output schemas
- **RULE:** Routes serialize with an output schema's `dump()`; they never return a model, `to_dict()`, or a hand-built dict of model fields. Output schemas never reference `password_hash`. All keys are `snake_case`. These shapes are fixed (each Card item includes `id`):

| Output schema | Keys |
|---|---|
| `UserSchema` (safe user: register `data`, login `user`, `GET`/`PATCH /api/users/me`) | `id`, `name`, `username`, `email`, `created_at` |
| `CardSchema` (nested Board Card, and the Card returned by create, update and position) | `id`, `title`, `description`, `order`, `column_id`, `assignee_id`, `assignee`, `created_by_id`, `completed_at`, `created_at`, `updated_at` |
| `CardListItemSchema` (`GET /api/cards`: Search item and My Tasks item) | `id`, `title`, `order`, `column_id`, `column_name`, `board_id`, `board_name`, `assignee_id`, `assignee` |
| `CommentSchema` | `id`, `card_id`, `parent_id`, `author_id`, `content`, `is_deleted`, `created_at`, `updated_at` |
| `NotificationSchema` (each element of `items`) | `id`, `type`, `message`, `is_read`, `created_at`, `comment_id`, `card_id`, `board_id` |

  `assignee` is an object `{id, name, username}` or `null` when the Card has no Assignee. A Search item and a My Tasks item are both the `CardListItemSchema` item; for My Tasks `assignee_id` equals the requester, and the frontend does the grouping by `board_name`. In `NotificationSchema`, `card_id` and `board_id` are **read-only values derived through the Comment** (Comment, Card, Column, Board) and are not stored (requirements.md OD-19); the persistence references of a Notification are `recipient_id` and `comment_id` only (no `user_id` or `card_id` is stored on a Notification; `database.md` DB-09). `CommentSchema` maps the API field `parent_id` to the database column `parent_comment_id` (`attribute='parent_comment_id'`) and derives `is_deleted` from `deleted_at` (BE-15). `GET /api/boards/<id>` returns the Board (`id`, `name`, `team_id`, `created_at`, `columns`) with Columns ordered by `order` ascending (each Column with `id`, `name`, `order`, `is_done`, `cards`), each Column's non-deleted Cards ordered by `order` ascending as `CardSchema` items.
- **RATIONALE:** One place decides which fields leave the server, so a password hash can never leak and each shape is the same everywhere it is used.
- **EXAMPLE:** `success(BoardDetailSchema().dump(board))` where `BoardDetailSchema` nests `ColumnSchema(many=True)` which nests `CardSchema(many=True)`.
- **VERIFY:**
  `grep -rnE "to_dict|__dict__" backend/app | wc -l` → `0`;
  `grep -rn "password_hash" backend/app/blueprints/*/schema.py | wc -l` → `0`;
  pytest asserts no JSON key containing `password` in the `register`, `login` and `users/me` responses;
  pytest asserts the exact key sets of `UserSchema`, `CardSchema`, `CardListItemSchema`, `CommentSchema` and `NotificationSchema` listed above, and that `GET /api/cards?assignee=me` returns only Cards whose `assignee_id` is the requester.

---

## 3. Response Envelope

### BE-07 — Success is `{ "data": ... }`, error is `{ "error": "<string>" }`
- **RULE:** Every endpoint wraps its payload the same way, built only with `success()` and `error()` from `app/utils/responses.py`. A response never contains both keys and never a bare body, including 401, 403, 404, 405 and 500 responses:

| Outcome | Shape | HTTP |
|---|---|---|
| Success | `{ "data": <payload> }` | 200 / 201 |
| Validation failure | `{ "error": "<one string>" }` built by `format_validation_error` (BE-04) | 400 |
| Handled error | `{ "error": "<message>" }` | 401 / 403 / 404 / 405 / 409 (and 400 for `InvalidAssigneeError`, `InvalidParentCommentError`, `InvalidTargetColumnError`) |
| Unexpected error | `{ "error": "Internal server error" }` | 500 |

  `error` is always one non-empty string. Create returns 201; read, update and delete return 200. DELETE returns `{ "data": { "id": "<uuid>" } }` (removing a Team member returns the removed user's id). `POST /api/auth/login` returns `{ "data": { "access_token", "token_type": "Bearer", "expires_in": 3600, "user": <UserSchema> } }`. `POST /api/boards/<id>/invite-links` returns 201 with `id`, `board_id`, `token`, `created_at`. `GET /api/notifications` returns `{ "data": { "items": [...], "page", "per_page", "total", "total_pages", "unread_count" } }` where `total_pages = ceil(total / per_page)` and is `0` when `total` is `0`, and `unread_count` counts **all** unread Notifications of the requester, not only those on the page. `PATCH /api/cards/<id>/position` returns `{ "card": {...}, "rebalanced": <bool> }` and `PATCH /api/boards/<id>/columns/reorder` returns `{ "column": {...}, "rebalanced": <bool> }` (BE-14). `GET /api/boards/<id>/analytics` returns exactly `cards_per_column`, `completed_this_week`, `member_activity`, `activity_per_day`, `start_date`, `end_date`. Other list endpoints return the array directly under `data`. `GET /api/health` returns `{ "data": { "status": "ok" } }`.
- **RATIONALE:** The frontend parses every response identically and never special-cases an endpoint.
- **EXAMPLE:** `GET /api/boards/<id>` → `{ "data": { "id": "...", "name": "...", "columns": [ { "cards": [ ... ] } ] } }`.
- **VERIFY:**
  `grep -rn "jsonify(" backend/app | grep -v "utils/responses.py" | wc -l` → `0`;
  the parametrised envelope test (requirements.md Requirement 20) passes: exactly one of `data` / `error` is present on every route's success, 400, 401, 403, 404 and 405 response, and `error` is a non-empty `str`;
  pytest asserts the key set of the notifications payload is exactly `items, page, per_page, total, total_pages, unread_count` and of the login payload exactly `access_token, token_type, expires_in, user`;
  pytest asserts a user with no Notifications gets `items == []`, `total == 0`, `total_pages == 0`, and that `unread_count` counts unread items beyond the requested page.

---

## 4. Authentication and Access

### BE-08 — Guard decorators: `@token_required` and `@board_access_required(allow_guest_read=True)`
- **RULE:** Every route carries exactly one guard directly below its route decorator, with these exemptions:
  - **Public (no guard):** `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/health`.
  - **Guest read endpoints (exactly two):** `GET /api/boards/<id>` and `GET /api/cards/<id>/comments` use `@board_access_required(allow_guest_read=True)` and never `@token_required`.
  - **Every other route:** `@token_required`.

  Both decorators live in `app/utils/auth.py` (which may import models, ST-04) and validate path UUIDs after authentication (BE-04). `@token_required` verifies the JWT with Flask-JWT-Extended, loads the user, and passes `current_user` as the **first** handler argument, or raises `AuthenticationRequiredError` (401) before the handler runs; a missing, malformed or expired token, or a token whose user no longer exists, is a 401; any `X-Invite-Token` is ignored. `@board_access_required(allow_guest_read=True)` resolves the request with the ordered Access Resolution Table below (requirements.md Requirement 3 owns the product table) and passes a plain `access` object (`user` or `None`, `role` of `admin`, `member` or `guest`) as the **first** handler argument. "Board of the resource" is the requested Board, or the Board that owns the requested Card. The first matching step applies:
  1. An `Authorization` header is present and its JWT is invalid, malformed or expired → `401`, even when a valid invite token is also present. A bad JWT never falls back to Guest access.
  2. No `Authorization` header and no `X-Invite-Token` → `401`.
  3. The Board (or the Card's Board) does not exist, or the Card is soft-deleted → `404` with the generic body.
  4. A valid JWT of a Team member of the Board's Team → the role from `team_memberships` applies and any invite token (valid or not) is ignored.
  5. A valid JWT of a non-member and no invite token → `403` with the generic body.
  6. The invite token is invalid, revoked or malformed (an empty header value counts as present and invalid), reached only when step 4 did not match → `404 {"error": "Not found"}`.
  7. A valid, non-revoked invite token bound to this Board, with no JWT or a valid JWT of a non-member → `200`, Guest read-only (`role` is `guest`).
  8. A valid invite token bound to another Board, with no JWT or a valid JWT of a non-member → `403` with the generic body.

  A Guest reaches only those two routes: the invite token is read **only** there and ignored on every other route, so a request that carries only a token on a `@token_required` route is `401`, and a Guest never reaches Search, Notifications, Analytics, My Tasks, Profile or any write. The invite token is looked up by hash (only the hash is stored, `invite_links.token_hash`, database.md DB-09; a link is revoked when `revoked_at` is set); the raw token is generated with `secrets.token_urlsafe(32)` and is returned once, in the create response. Services trust the `access` object on the two Guest read routes and do not repeat the membership lookup; for a Guest the service returns data read-only.
- **RATIONALE:** Protected resources reject unauthenticated requests before any handler code runs, an invite token can only add access and never reduce it, and a fixed ordered table removes every ambiguous combination of header, token and membership.
- **EXAMPLE:**
```python
# app/blueprints/boards/routes.py
@boards_bp.route('/boards/<board_id>', methods=['GET'])
@board_access_required(allow_guest_read=True)
def get_board_route(access, board_id):
    board = get_board_service(board_id, access)
    return success(BoardDetailSchema().dump(board))
```
- **VERIFY:**
  every route has exactly the guard above; this awk allows exactly the three public routes and the two Guest read routes and prints any violation → no output:
  ```bash
  awk '
  /^@[a-z_]+\.route/ {route=$0; tr=0; ba=0; next}
  /^@token_required/ {tr=1; next}
  /^@board_access_required\(allow_guest_read=True\)/ {ba=1; next}
  /^def / {
    if (route != "") {
      pub = (route ~ /auth\/register|auth\/login|\/health/)
      guest = (route ~ /route\(\047\/boards\/<[a-z_]+>\047, methods=\[\047GET\047\]\)/ || route ~ /route\(\047\/cards\/<[a-z_]+>\/comments\047, methods=\[\047GET\047\]\)/)
      if (pub && (tr || ba)) print FILENAME": "$0" public route has a guard"
      else if (guest && (tr || !ba)) print FILENAME": "$0" guest route needs only board_access_required"
      else if (!pub && !guest && (!tr || ba)) print FILENAME": "$0" needs @token_required"
    }
    route=""; tr=0; ba=0
  }' backend/app/blueprints/*/routes.py backend/app/health.py
  ```
  `grep -rA2 "^@token_required" backend/app/blueprints/*/routes.py | grep "def " | grep -vc "(current_user"` → `0`;
  `grep -rA2 "^@board_access_required" backend/app/blueprints/*/routes.py | grep "def " | grep -vc "(access"` → `0`;
  `grep -rc "board_access_required" backend/app/blueprints/*/routes.py` totals `2`;
  pytest iterates `app.url_map` and asserts `401` without a token for every route except the three public routes and the two Guest read routes, and `401` for a malformed token and an expired token on a `@token_required` route;
  pytest for the two Guest read routes covers every table step: valid Guest token `200` read-only (no JWT); invalid token `404 {"error": "Not found"}`; revoked token `404`; empty `X-Invite-Token` `404`; expired or malformed JWT with a valid token `401` (never Guest); no JWT and no token `401`; non-member JWT without token `403` generic; token bound to another Board `403` generic; Team member JWT with an invalid or foreign token `200` (token ignored); non-existent Board and soft-deleted Card `404` generic;
  pytest asserts a Guest write is denied (`401` without a JWT, `403` generic with a non-member JWT) and that a valid Guest token on Search, Notifications, Analytics, My Tasks and `GET /api/users/me` is `401` (token ignored), and that Team A cannot read Team B's Board (`403`).

### BE-09 — Team authorization lives in services
- **RULE:** `boards.team_id` is ownership: a Board belongs to exactly one Team. Member and Admin access resolves through `team_memberships (team_id, user_id)` and the role comes from that row (tables and constraints are owned by `database.md`; Board-level membership does not exist). Role permissions follow requirements.md Requirement 2. Authorization lives in services: `boards/service.py` defines `require_team_member_service(board_id, user_id)` and `require_team_admin_service(board_id, user_id)`. Each resolves the Board (`BoardNotFoundException` when it does not exist), then its Team, then the user's membership: a non-member raises `TeamAccessDeniedError`, a Member on an admin-only action raises `AdminAccessRequiredError`. Every service that reads or writes Board-scoped data (`columns`, `cards`, `comments`, `analytics`, and the `notifications` and `users` services wherever they touch Board-scoped data, such as mention resolution and member removal) first loads its own record (the not-found exception, evaluated first), resolves the record's Board, and then calls one of the two helpers. Listing endpoints (`GET /api/boards`, `GET /api/cards`) filter through the requester's `team_memberships`. A Member who deletes a Card another user created raises `AdminAccessRequiredError`. Adding, changing and removing Team members check the Admin role **before** the `email`, membership state or `role` is evaluated, and removing or demoting the last Admin raises `LastAdminError`. Comment edit and delete check ownership and raise `CommentOwnershipError`, also for an Admin. Guest access is separate and handled only by BE-08. Handlers never read roles.
- **RATIONALE:** One implementation of "who may do this" is the only way the permission rules stay consistent across eight Blueprints, and one lookup path (Board, Team, membership) prevents access from leaking between Teams.
- **EXAMPLE:** A Member calling `GET /api/boards/<id>/analytics` → `analytics/service.py` calls `require_team_admin_service` → `AdminAccessRequiredError` → `403 { "error": "Admin access required" }`. A user of another Team calling the same route → `TeamAccessDeniedError` → `403 { "error": "Not found or access denied" }`.
- **VERIFY:**
  `grep -nE "\.role\b|is_admin|team_memberships|board_members" backend/app/blueprints/*/routes.py | wc -l` → `0`;
  `grep -cE "^def require_team_(member|admin)_service" backend/app/blueprints/boards/service.py` → `2`;
  `for b in columns cards comments analytics; do grep -qE "require_team_(member|admin)_service" backend/app/blueprints/$b/service.py || echo "NO ACCESS CHECK: $b"; done` → no output;
  `grep -rniE "board_members|BoardMemberEntity" backend | wc -l` → `0` (no Board-level membership);
  pytest `-k permission` has at least one test per applicable cell of the requirements.md Requirement 2 table, plus: cross-Team denial for Board, Column, Card and Comment ids (`403` generic body, and an Admin of Team A is denied on Team B), Member denied every Admin-only action with the specific message, `404` before `403` for a non-existent id, last-Admin removal and demotion `409`, and non-Admin member management `403` before the `email` lookup.

---

## 5. Error Handling

### BE-10 — Typed exceptions, never bare ones
- **RULE:** Services raise typed exceptions defined in `app/exceptions.py`. Every one subclasses `AppException`, which carries `status_code` and a default `message`. Not-found classes end in `NotFoundException`; every other class ends in `Error`. Services never raise `KeyError`, `ValueError`, `Exception` or `RuntimeError`, and never call `abort()`. The status and body policy is:
  - No, malformed or expired JWT on a JWT-protected route: `401`. Authenticated user without Team access to an existing resource: `403`. Non-existent Board, Column, Card or Comment: `404`. Soft-deleted Card: `404`. Existence is evaluated first (404), then Team membership (403), then role (403).
  - Inaccessible and non-existent Board-scoped resources share the generic body `{"error": "Not found or access denied"}`, held in the constant `ACCESS_OR_NOT_FOUND_MESSAGE` in `app/exceptions.py`.
  - An invalid or revoked Invite Link, and an unknown route: `{"error": "Not found"}`. An unregistered email when an Admin adds a member: `{"error": "User not found"}`. A Notification not owned by the requester: `{"error": "Not found"}`. A Team member without the required role keeps `{"error": "Admin access required"}`.
  - An id in a request body or query string that does not exist is a `400`, except `board_id` in `GET /api/cards` (`404` generic).

  The catalog:

| Exception | Raised when | HTTP and body |
|---|---|---|
| `InvalidCredentialsError` | login email or password is wrong (same message for both) | 401 `Invalid credentials` |
| `AuthenticationRequiredError` | token missing, malformed or expired, or its user no longer exists | 401 |
| `EmailAlreadyRegisteredError` | register or profile update uses an existing email (case-insensitive) | 409 |
| `UsernameAlreadyTakenError` | register uses an existing username (case-insensitive) | 409 |
| `UserNotFoundException` | a member is added by an email with no account | 404 `User not found` |
| `BoardNotFoundException` | a Board id does not exist | 404 generic |
| `ColumnNotFoundException` | a Column id does not exist | 404 generic |
| `CardNotFoundException` | a Card id does not exist or the Card is soft-deleted | 404 generic |
| `CommentNotFoundException` | a Comment id does not exist | 404 generic |
| `TeamAccessDeniedError` | an authenticated user touches a resource of a Team they do not belong to | 403 generic |
| `AdminAccessRequiredError` | a Team member attempts an admin-only action | 403 `Admin access required` |
| `CommentOwnershipError` | a user edits or deletes a Comment they did not write | 403 |
| `MemberAlreadyExistsError` | the user is already in the Team | 409 |
| `MemberNotFoundException` | the user to change or remove is not in the Team | 404 |
| `LastAdminError` | the last Admin of a Team would be removed or demoted | 409 |
| `InviteLinkNotFoundException` | an Invite Link is invalid, revoked, or not bound to the Board in the path | 404 `Not found` |
| `NotificationNotFoundException` | a Notification does not exist or belongs to another user | 404 `Not found` |
| `InvalidAssigneeError` | `assignee_id` is not a Team member, including a UUID that is not an existing user | 400 `Assignee must be a Team member` |
| `InvalidParentCommentError` | `parent_id` does not exist or belongs to a different Card | 400 |
| `InvalidTargetColumnError` | `column_id` in a move body does not exist or is on a different Board | 400 |
| `OrderConflictError` | the submitted `order` equals an active sibling's `order` (BE-14) | 409, envelope only, no hint |

- **RATIONALE:** Naming what went wrong lets one global handler own the error-to-HTTP mapping, and keeps `KeyError` tracebacks away from clients. One shared body for 403 and 404 avoids a second wording for the same denial.
- **EXAMPLE:** `if card is None or card.deleted_at is not None: raise CardNotFoundException()` where the class carries `status_code = 404` and `message = ACCESS_OR_NOT_FOUND_MESSAGE`.
- **VERIFY:**
  `grep -rnE "raise (KeyError|ValueError|Exception|RuntimeError)|abort\(" backend/app | wc -l` → `0`;
  `grep -E "^class " backend/app/exceptions.py | grep -vE "class (AppException|[A-Za-z]+NotFoundException|[A-Za-z]+Error)\(" | wc -l` → `0`;
  `for c in InvalidCredentialsError AuthenticationRequiredError EmailAlreadyRegisteredError UsernameAlreadyTakenError UserNotFoundException BoardNotFoundException ColumnNotFoundException CardNotFoundException CommentNotFoundException TeamAccessDeniedError AdminAccessRequiredError CommentOwnershipError MemberAlreadyExistsError MemberNotFoundException LastAdminError InviteLinkNotFoundException NotificationNotFoundException InvalidAssigneeError InvalidParentCommentError InvalidTargetColumnError OrderConflictError; do grep -q "^class $c(" backend/app/exceptions.py || echo "MISSING $c"; done` → no output;
  `grep -c "ACCESS_OR_NOT_FOUND_MESSAGE" backend/app/exceptions.py` → ≥ `5`;
  pytest asserts, for each of Board, Column, Card and Comment: a non-existent id is `404` with the generic body, an id of another Team is `403` with the same body, and a soft-deleted Card is `404` on all five Card-id routes; a non-existent `board_id` in `GET /api/cards?q=...&board_id=...` is `404` and an inaccessible one is `403`; a non-UUID `assignee_id` that is not an existing user and a non-member `assignee_id` both give `400 {"error": "Assignee must be a Team member"}`.

### BE-11 — One global handler, never a traceback
- **RULE:** `register_error_handlers(app)` in `app/error_handlers.py` is called once from `create_app()` in `app/__init__.py`. It registers: `AppException` → its `status_code` with `{ "error": message }`; Marshmallow `ValidationError` → `400 { "error": format_validation_error(...) }` (BE-04); Werkzeug `HTTPException` (`404` unknown route `{ "error": "Not found" }`, `405`) → the envelope; any other `Exception` → `500 { "error": "Internal server error" }`. The Flask-JWT-Extended callbacks of BE-13 are registered in the same function. A production response never contains a Python traceback; production runs with `FLASK_DEBUG=0`. Services and handlers never catch `Exception` to hide a failure.
- **RATIONALE:** One place owns error-to-HTTP mapping; clients always get JSON in one shape, and internals are never leaked.
- **EXAMPLE:** `CardNotFoundException` → `404 { "error": "Not found or access denied" }`; an unexpected `RuntimeError` → `500 { "error": "Internal server error" }`.
- **VERIFY:**
  `grep -c "register_error_handlers" backend/app/__init__.py` → ≥ `1`;
  `grep -rnE "except (Exception|BaseException)|except:" backend/app/blueprints | wc -l` → `0`;
  pytest (with `PROPAGATE_EXCEPTIONS` off) patches a service to raise `RuntimeError` and asserts status `500`, body exactly `{ "error": "Internal server error" }`, and `"Traceback"` absent from the response text; another test asserts an unknown URL returns `404 { "error": "Not found" }` as JSON, not HTML, and a known route with an unsupported method returns `405` in the envelope.

### BE-12 — Structured JSON logs
- **RULE:** Every handled error is logged as a JSON object with exactly these four fields: `level`, `endpoint`, `error_type`, `user_id`. Client errors (4xx) log at `WARNING`; unexpected errors (500) log at `ERROR`. `user_id` is `null` for unauthenticated requests and for Guests. Logs never contain passwords, tokens (JWT or invite token), the `Authorization` or `X-Invite-Token` headers, or request bodies. Logging is configured in `app/logging_config.py`; `print()` is forbidden.
- **RATIONALE:** A fixed set of fields makes production logs searchable, for example every `CardNotFoundException` on `cards.move_card_route`.
- **EXAMPLE:** `{"level": "WARNING", "endpoint": "cards.move_card_route", "error_type": "CardNotFoundException", "user_id": "5b0c..."}`
- **VERIFY:**
  pytest with `caplog` triggers a 404 and a 500 and asserts `set(json.loads(record.getMessage()).keys()) == {"level", "endpoint", "error_type", "user_id"}` with the correct levels;
  `grep -rnE "logger\.\w+\(.*(password|token|authorization)" backend/app | wc -l` → `0`;
  `grep -rn "print(" backend/app | wc -l` → `0`.

---

## 6. Auth and Password Handling

### BE-13 — Password hashing, JWT settings, and registration identity rules
- **RULE:** Passwords are hashed with `werkzeug.security.generate_password_hash` and checked with `check_password_hash`; only `password_hash` is stored and it never leaves the persistence layer (BE-06). Tokens are issued with Flask-JWT-Extended, `JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=60)`, and the identity is the user UUID as a string (`create_access_token(identity=str(user.id))`); the login response carries `expires_in` `3600`. Login failure for an unknown email and for a wrong password returns the same `401 {"error": "Invalid credentials"}`. `JWT_SECRET_KEY` comes from the environment and is at least 32 characters in production; it is never a literal in code. Flask-JWT-Extended's error callbacks (`unauthorized_loader`, `invalid_token_loader`, `expired_token_loader`, `token_verification_failed_loader`) are registered in `register_error_handlers(app)` and all return the `401` envelope `{ "error": ... }` built with `error()`; the library default `422` for a malformed token is never returned. Logout is stateless: an unexpired JWT stays valid until it expires. `register_service` normalizes the username to lowercase (already done by `RegisterSchema`, BE-05), detects duplicate usernames and emails case-insensitively (`UsernameAlreadyTakenError`, `EmailAlreadyRegisteredError`, both 409), and also converts a database unique-violation raised by a concurrent registration (`database.md` DB-09 indexes) into the same 409; the same email rule applies to `PATCH /api/users/me`.
- **RATIONALE:** Identical login errors prevent account enumeration; env-held secrets keep the repository safe to publish; case-insensitive uniqueness stops two accounts that differ only by letter case, and a mention of `@Alice` must reach `alice`.
- **EXAMPLE:** `create_access_token(identity=str(user.id))`; registering `Alice_01` after `alice_01` exists → `409`.
- **VERIFY:**
  `grep -rniE "md5|sha1|plaintext" backend/app | wc -l` → `0`;
  `grep -rnE "JWT_SECRET_KEY\s*=\s*['\"]" backend/app | wc -l` → `0`;
  `grep -rn "generate_password_hash" backend/app/blueprints/auth/service.py | wc -l` → ≥ `1`;
  on the production environment `printf %s "$JWT_SECRET_KEY" | wc -c` → ≥ `32` (checked at deploy time);
  pytest asserts both login-failure cases return identical bodies, the decoded token has `exp - iat == 3600` and a string identity, a malformed token and an expired token return `401` in the envelope (never `422`), and no response contains `password` or `password_hash`;
  pytest asserts duplicate usernames are rejected case-insensitively (`alice_01` then `Alice_01` → `409`), duplicate emails are rejected case-insensitively (`a@example.com` then `A@example.com` → `409`), and the stored username is lowercase.

---

## 7. FLOAT Ordering Allocation

### BE-14 — Server-side FLOAT order allocation, conflict, and two-phase rebalance
- **RULE:** The server allocates and validates `order` for Columns (within a Board) and Cards (within a Column). The client computes the `order` it submits in `lib/ordering.ts` (`frontend.md`); the server never trusts it blindly.
  - **Constants and helpers:** `ORDER_STEP = 1024.0` and `MIN_GAP = 1e-6` live in `app/utils/ordering.py` together with the pure allocation helpers. First item `1024.0`; append = `last.order + ORDER_STEP`; insert at head = `first.order / 2`; insert between = `(prev.order + next.order) / 2`. Creates (`POST` Column, `POST` Card) append. Only **active** siblings count (a Card with `deleted_at` set is excluded); soft-deleted rows keep stale `order` values and never block an active row.
  - **Client-supplied `order`:** `CardPositionSchema` and `ColumnReorderSchema` require `order > 0` (BE-05). The service stores the submitted value. If it equals the `order` of another active sibling of the target parent (the moved row itself is excluded, so repeating the same move is idempotent), the service raises `OrderConflictError`: `409` with the standard envelope only and no suggested value, range or hint; stored data is unchanged and the client resolves the conflict.
  - **Gap check and rebalance:** after storing the order, if any two adjacent active siblings of the affected parent differ by less than `MIN_GAP`, the service rebalances that parent to `1024.0`, `2048.0`, `3072.0`, ... in the existing sequence and returns `rebalanced: true`; otherwise `false`. Deleting a Column or Card leaves the other orders unchanged.
  - **One transaction, never a duplicate active `order`:** the partial unique indexes of `database.md` DB-08 are not deferrable, so no statement may leave two active siblings with the same `order`. A reorder or rebalance runs in ONE transaction, takes a row lock on the affected parent's active siblings (`SELECT ... FOR UPDATE`, ordered by `order, id`; the parent row is locked first, and when a Card changes Column both parents are locked in `id` order) so concurrent moves serialize, and writes in two phases: **phase 1** moves every affected active row to a distinct temporary value above the current maximum active `order` of that parent (`max + ORDER_STEP * (i + 1)`), **phase 2** writes the final values in ascending sequence (`ORDER_STEP * (i + 1)`). Every intermediate statement is collision free, and the commit makes the result visible all-or-nothing.
  - **Reads:** lists are always returned `ORDER BY order ASC`. A move returns `{ "card": {...}, "rebalanced": <bool> }` and a Column reorder returns `{ "column": {...}, "rebalanced": <bool> }`; the returned row carries its final `order` after any rebalance.
- **RATIONALE:** Float ordering moves one row per drag instead of renumbering the column, but halving needs a floor to avoid precision loss. A non-deferrable unique index makes a naive one-pass rebalance fail on an intermediate value, and without a lock two concurrent moves can pick the same slot.
- **EXAMPLE:** Cards at `1024.0` and `2048.0`; a drop between them is submitted as `1536.0` and stored as is. A request with `order: 2048.0` for another Card → `409 { "error": "Order already in use" }`. The same Card sent twice with `1536.0` returns the same board state.
- **VERIFY:**
  `grep -cE "^(ORDER_STEP = 1024\.0|MIN_GAP = 1e-6)$" backend/app/utils/ordering.py` → `2`;
  `grep -c "with_for_update" backend/app/blueprints/cards/service.py backend/app/blueprints/columns/service.py` → ≥ `1` for each file;
  `grep -rn "order_by" backend/app/blueprints/boards/service.py` shows ordering on both Columns and Cards;
  unit test: inserting at the head 60 times in a row keeps every `order` positive and strictly increasing once the service rebalances (`rebalanced: true` appears, and no gap is below `MIN_GAP` afterwards);
  pytest on PostgreSQL: a rebalance of 50 active siblings completes without an integrity error, preserves the sequence, and ends at `1024.0 * k`; a concurrent-move test (two simultaneous moves to the same slot) ends with unique, strictly increasing active orders (one request may be `409`); a test shows a soft-deleted Card's stale `order` does not block an active Card from using the same value and is ignored by the rebalance; an equal-order request is `409` with body exactly `{"error": "<non-empty string>"}` and no other key; `PATCH .../position` followed by `GET /api/boards/<id>` returns the new order and Columns and Cards in ascending order.

---

## 8. Retention and Bootstrap Behavior

### BE-15 — Card soft delete, Comment tombstone, activity events, notification cleanup, registration bootstrap
- **RULE:** Persistence of these rules (columns, constraints, cascades) is owned by `database.md` (DB-06, DB-09, DB-11); the service behavior is:
  - **Card soft delete:** `DELETE /api/cards/<id>` sets only the Card's `deleted_at`. It never physically deletes Comments, Notifications or Activity Events. Every read that reaches them through a Card (Board, Column, Search, My Tasks, Comment list, Notification and Analytics reads) filters `CardEntity.deleted_at IS NULL`, and Activity_Events of a soft-deleted Card are excluded from analytics. Every Card-id route (`PATCH /api/cards/<id>`, `DELETE /api/cards/<id>`, `PATCH /api/cards/<id>/position`, `POST` and `GET /api/cards/<id>/comments`) answers a soft-deleted Card with `404` and the generic body before any membership check. Physical cascade happens only for Board delete and Column delete, which delete the parent row and rely on the database cascade (no service loops over children).
  - **Activity events:** the allowed `event_type` values are `card_created`, `card_updated`, `card_moved`, `card_deleted`, `comment_added`. The service records exactly one event in the same transaction as the change: one per successful create, edit, move, soft delete and Comment creation, including exactly one `card_deleted` per successful Card soft delete, and none for a rejected request.
  - **Comment tombstone:** `DELETE /api/comments/<id>` sets the Comment's `deleted_at` and keeps the row. `CommentSchema` derives `is_deleted` from `deleted_at` (it is not stored). A deleted Comment with at least one live reply (a reply whose `deleted_at` is null) is serialized as a tombstone: `is_deleted` true, `content` the empty string, `author_id` and replies kept. A deleted Comment without a live reply is omitted from reads. Comments are returned as a flat list ordered by `created_at` ascending. The API field `parent_id` maps to the database column `parent_comment_id`.
  - **Notification cleanup:** when a Comment is deleted (tombstone or omitted) the service deletes the Notifications of that Comment; when a Team member is removed the service deletes that user's Notifications for Comments on the Team's Boards. Removing a member keeps the Cards and Comments the user authored and sets `assignee_id` to null on every non-deleted Card of the Team's Boards assigned to that user.
  - **Mention resolution:** a mention is `@` followed by 3–30 letters, digits or underscores; the mentioned name is lowercased and matched against the lowercase `username` of the Team's members. One `mention` Notification (unread) per mentioned member per Comment, none for the author, none for an unmatched name. Editing a Comment notifies only newly mentioned members who have no Notification for it; removing a mention deletes nothing.
  - **Registration bootstrap:** `register_service` creates the user, the personal Team (`is_personal` true, `owner_id` = the new user) and the `admin` membership of that user in ONE transaction, so either all three exist or none does. `POST /api/boards` without `team_id` uses the requester's personal Team; a `team_id` of a Team of which the requester is not an Admin is rejected with `TeamAccessDeniedError` (`403`, generic body).
- **RATIONALE:** Retention rules written once in services keep task history intact, make soft-deleted data invisible everywhere, and let analytics and notifications be tested against one definition.
- **EXAMPLE:** Soft-deleting a Card with 3 Comments leaves 3 Comment rows; `GET /api/boards/<id>` omits the Card; a second `DELETE` returns `404` generic and adds no `card_deleted` event.
- **VERIFY:**
  `grep -nE "session\.delete\(" backend/app/blueprints/cards/service.py backend/app/blueprints/comments/service.py | wc -l` → `0`;
  `grep -c "is_deleted" backend/app/blueprints/comments/schema.py` → ≥ `1`;
  pytest: a soft-deleted Card keeps its Comment, Notification and Activity_Event rows and is absent from Board, Search, My Tasks and Analytics responses; exactly one `card_deleted` event per successful soft delete and none for a rejected one; a deleted Comment with a live reply is returned with `is_deleted` true, `content` `""` and `author_id` kept, and one without is omitted; deleting a Comment removes its Notifications; deleting a Column or Board removes its children, and a Card soft delete removes nothing;
  pytest: `@Alice` in a Comment notifies the user `alice` once, a repeated mention still gives one Notification, a self-mention and an unmatched name give none, and an edit adding a mention notifies only the new member;
  pytest: registration creates exactly one user, one personal Team and one `admin` membership, and a forced failure after the user insert leaves none of the three; the personal Team owner is an Admin member of it; a user is not resolved as a member of another user's Team; `POST /api/boards` without `team_id` uses the personal Team and with a foreign `team_id` returns `403` with the generic body.

---

## Trace the Flow: Service → Global Handler → JSON Response

1. In `cards/service.py`, `move_card_service()` loads the card with `db.session.get(CardEntity, card_id)` and raises `CardNotFoundException` when it is `None` or soft-deleted.
2. In `app/exceptions.py`, that exception carries `status_code = 404` and `message = ACCESS_OR_NOT_FOUND_MESSAGE` (`'Not found or access denied'`).
3. In `app/error_handlers.py`, the `AppException` handler logs `{ level, endpoint, error_type, user_id }` and returns `error('Not found or access denied', 404)`, which the client receives as `404 { "error": "Not found or access denied" }`.
