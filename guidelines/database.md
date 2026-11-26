---
inclusion: fileMatch
fileMatchPattern: "backend/app/models/**/*.py"
---

# Sevy Database Guidelines (PostgreSQL + SQLAlchemy)

Database guidelines for **Sevy**: PostgreSQL 16, SQLAlchemy 2 models through Flask-SQLAlchemy, UUID keys, and FLOAT ordering.

Four guideline groups cover **Naming · Required Columns · Data Types · Relationships**. Every guideline has **RULE**, **RATIONALE**, **EXAMPLE**, and a **VERIFY** check. IDs use the `DB-nn` format.

**Ownership boundary:** This file owns table and column naming, required columns, model data types, database constraints, indexes, foreign keys, ORM relationships, and the persistence deletion policy. It does not define API behavior, request validation, API input limits, response envelopes, authentication, or service-layer business logic; those belong to `backend.md` and `requirements.md`. The FLOAT order-allocation and rebalance algorithm belongs to `backend.md`. Migration workflow, test database setup, and database connection/SSL configuration belong to `tech.md`.

The v1 schema contains **ten tables**: `users`, `teams`, `team_memberships`, `boards`, `board_columns`, `cards`, `card_comments`, `notifications`, `activity_events`, and `invite_links`. This is a deliberate Sevy domain decision: a Board is owned by one Team (`boards.team_id`), Team membership (`team_memberships`) determines Member and Admin access, and Guest access is provided through Invite Links. Do not add a parallel `board_members` table.

---

## 1. Naming

### DB-01 — Tables are plural snake_case; columns are snake_case

- **RULE:** Table names MUST use plural `snake_case`; column names MUST use `snake_case`. Set `__tablename__` explicitly on every model. The v1 tables are exactly: `users`, `teams`, `team_memberships`, `boards`, `board_columns`, `cards`, `card_comments`, `notifications`, `activity_events`, and `invite_links`. The table that stores a Board's Columns is `board_columns`, never `columns`. No `board_members` table exists.
- **RATIONALE:** Predictable names make models and SQL easy to scan, prevent inconsistent names across generated models, and avoid using the generic `columns` identifier for a table.
- **EXAMPLE:** `cards`, `board_columns`, `card_comments`, `activity_events`; columns `team_id`, `board_id`, `column_id`, `assignee_id`.
- **VERIFY:**
  ```bash
  grep -rhoP "__tablename__ = ['\"]\K[^'\"]+" backend/app/models | LC_ALL=C sort | tr '\n' ' '
  ```
  Expected table names: `activity_events board_columns boards card_comments cards invite_links notifications team_memberships teams users`.
  ```bash
  grep -rnP '^\s+[a-z]+[A-Z]\w*\s*=\s*db\.Column' backend/app/models | wc -l
  grep -rniE 'board_members|BoardMemberEntity' backend | wc -l
  ```
  Expected results: `0` for both commands (no camelCase column names; no `board_members` table or model).

### DB-02 — Foreign keys, role-specific user references, flags, and timestamps have predictable names

- **RULE:** A foreign-key column MUST use `<singular_entity>_id` where possible (`team_id`, `board_id`, `column_id`, `card_id`). A foreign key to `users` that represents a specific role MUST use that role (`owner_id`, `assignee_id`, `created_by_id`, `author_id`, `actor_id`, `recipient_id`). Boolean columns MUST start with `is_` (`is_personal`, `is_done`, `is_read`). Timestamp columns MUST end with `_at` (`created_at`, `completed_at`, `revoked_at`).
- **RATIONALE:** Names communicate the purpose of a relationship or state without requiring the reader to inspect the model definition.
- **EXAMPLE:** `cards.column_id` references `board_columns.id`; `cards.assignee_id` references `users.id`; `teams.owner_id` references `users.id`; `activity_events.actor_id` references `users.id`; `notifications.recipient_id` references `users.id`.
- **VERIFY:**
  ```bash
  grep -rnP '^\s+\w+\s*=\s*db\.Column\(db\.Boolean' backend/app/models | grep -vE '^.*\bis_[a-z0-9_]+\s*=' | wc -l
  ```
  Expected result: `0`. Review foreign-key names against their semantic role in the DB-09 schema catalog.

### DB-03 — Constraint and index names follow one metadata convention

- **RULE:** `app/extensions.py` MUST configure SQLAlchemy `MetaData(naming_convention=...)` for primary keys, foreign keys, unique constraints, check constraints, and indexes. Use the convention prefixes `pk_`, `fk_`, `uq_`, `ck_`, and `ix_`. Explicitly name composite indexes, partial and functional (expression) indexes, and check constraints. A unique index created with `db.Index(..., unique=True)` uses the `uq_` prefix. Do not create unnamed constraints.
- **RATIONALE:** Stable constraint names make schema diffs and migrations predictable across local, test, and production databases.
- **EXAMPLE:** `uq_team_memberships_team_id_user_id`, `uq_users_username`, `uq_users_email_lower`, `ck_users_username_format`, `ck_cards_order_positive`, `ck_activity_events_event_type`, `uq_cards_column_id_order_active`, `uq_teams_owner_id_personal`, `ix_cards_column_id_order`, `ix_notifications_recipient_id_created_at`.
- **VERIFY:**
  ```bash
  grep -c 'naming_convention' backend/app/extensions.py
  grep -rn 'CheckConstraint(' backend/app/models
  ```
  Expected: every check constraint has an explicit `name=` argument. Confirm with a model-metadata test that all constraint and index names use the configured prefixes.

### DB-04 — Model classes use the Entity suffix, one model per file

- **RULE:** Each table MUST have exactly one SQLAlchemy model class named `<Noun>Entity` in its own `backend/app/models/<snake_case>.py` file. Use these names: `UserEntity`, `TeamEntity`, `TeamMembershipEntity`, `BoardEntity`, `BoardColumnEntity`, `CardEntity`, `CardCommentEntity`, `NotificationEntity`, `ActivityEventEntity`, and `InviteLinkEntity`. `CardEntity` is the Sevy Card model. Do not define multiple persisted model classes in one model file.
- **RATIONALE:** The `Entity` suffix distinguishes persistence models from Marshmallow schemas, frontend types, and domain/service objects. One model per file makes the schema easy to locate and review.
- **EXAMPLE:** `backend/app/models/card.py` contains `class CardEntity(db.Model):`; `backend/app/models/team_membership.py` contains `class TeamMembershipEntity(db.Model):`.
- **VERIFY:**
  ```bash
  grep -rhE '^class \w+\(db\.Model\)' backend/app/models | grep -vc 'Entity(db.Model)'
  for f in backend/app/models/*.py; do [ "$(basename "$f")" = "__init__.py" ] || [ "$(grep -c '^class ' "$f")" -eq 1 ] || echo "NOT ONE CLASS: $f"; done
  ```
  Expected results: `0` for the first command and no output for the loop.

---

## 2. Required Columns

### DB-05 — Every persisted model carries the same four required columns

- **RULE:** Every persisted model MUST explicitly declare these columns in its model file: `id` (UUID primary key with `uuid.uuid4` default), `created_at`, `updated_at`, and nullable `deleted_at`. Timestamps MUST be timezone-aware UTC values supplied by the shared `utc_now()` function in `backend/app/utils/time.py`. Do not use `datetime.utcnow()`. `updated_at` MUST have both a creation default and an `onupdate` handler and MUST never be NULL.
- **RATIONALE:** Uniform identity, creation/update auditing, and a consistent soft-delete marker make every persisted entity predictable. UUIDs avoid exposing sequential identifiers. A shared UTC helper prevents inconsistent timestamp generation.
- **EXAMPLE:**
  ```python
  import uuid
  from app.utils.time import utc_now

  id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4)
  created_at = db.Column(
      db.DateTime(timezone=True), nullable=False, default=utc_now
  )
  updated_at = db.Column(
      db.DateTime(timezone=True), nullable=False,
      default=utc_now, onupdate=utc_now,
  )
  deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)
  ```
- **VERIFY:**
  ```bash
  for f in $(find backend/app/models -maxdepth 1 -name '*.py' ! -name '__init__.py'); do
    for c in 'id = db.Column(db.UUID, primary_key=True' 'created_at = db.Column(db.DateTime' 'updated_at = db.Column(db.DateTime' 'deleted_at = db.Column(db.DateTime'; do
      grep -qF "$c" "$f" || echo "$f missing: $c"
    done
  done
  grep -rn 'datetime.utcnow\|datetime\.utcnow' backend/app | wc -l
  ```
  Expected results: no missing-column output and `0` for the final command.

### DB-06 — `deleted_at` is present on every model; only Cards and Comments use soft deletion

- **RULE:** `deleted_at IS NULL` means a row is active. The column MUST exist on every table (DB-05), but soft deletion is used for `cards` and `card_comments` only. `boards`, `board_columns`, `teams`, `team_memberships`, and `invite_links` are physically deleted according to DB-11 (an Invite Link is revoked by setting `revoked_at`, and its row is kept). Soft-deleting a Card sets only that Card's `deleted_at`; it MUST NOT delete, nullify, or modify any `card_comments`, `notifications`, or `activity_events` row. The Card's own `deleted_at` hides those rows from normal reads: every query that reaches them through a Card (Board, Column, Search, My Tasks, Comment, Notification, and Analytics reads) MUST filter `CardEntity.deleted_at.is_(None)`; `activity_events` rows are reached through `entity_type` and `entity_id`. Soft-deleting a Comment sets only that Comment's `deleted_at`; the row, its `content`, and its replies (`parent_comment_id`) are kept, so a tombstoned parent keeps its reply context. The persisted tombstone marker is `card_comments.deleted_at`; there is no `is_deleted` column, and the API derives `is_deleted` from `deleted_at IS NOT NULL`. Physical cascade happens only for the two approved hard deletes: deleting a Board (its Columns, Cards, Comments, Notifications, Activity Events, and Invite Links) and deleting a Column (its Cards and their Comments). An ORM delete cascade is never triggered by a soft delete. Business rules on which Notifications are removed when a Comment is deleted are owned by `backend.md` and `requirements.md`.
- **RATIONALE:** A uniform column keeps every model structurally consistent, while an explicit per-entity policy avoids mixing physical and logical deletion. Keeping Comment, Notification, and Activity Event rows when a Card is soft-deleted preserves the task history and avoids data loss; hiding them through the Card filter keeps normal reads correct.
- **EXAMPLE:** Soft-deleting a Card sets `card.deleted_at = utc_now()`; its `card_comments` rows are untouched. A normal Card query filters `CardEntity.deleted_at.is_(None)`, and a Comment query that joins through the Card applies the same filter. Deleting a Column physically deletes its Cards and their Comments; do not confuse that hard-delete cascade with a Card soft delete.
- **VERIFY:**
  ```bash
  grep -rn 'deleted_at = db.Column' backend/app/models | grep -vc 'nullable=True'
  grep -rnE 'is_deleted\s*=\s*db\.Column' backend/app/models | wc -l
  ```
  Expected results: `0` for both commands. Add pytest assertions that: (a) a soft-deleted Card remains in `cards` with non-NULL `deleted_at`, is absent from nested Board loads, and keeps all its `card_comments`, `notifications`, and `activity_events` rows unchanged; (b) a soft-deleted Comment with replies remains in `card_comments` with its `content` and its replies still reference it through `parent_comment_id`; (c) deleting a Column physically removes its Cards and their Comments; (d) deleting a Board physically removes its Columns, Cards, Comments, Notifications, Activity Events, and Invite Links.

---

## 3. Data Types and Schema Inventory

### DB-07 — Pick the type by the data, consistently

- **RULE:** Use the following types consistently. Any deviation MUST be justified by an explicit requirement and documented in the model/design review. A database column length is storage capacity, never the API input limit; API input limits belong to `backend.md` and `requirements.md`.

  | Use | Required type |
  |---|---|
  | Primary and foreign keys | `db.UUID` |
  | Short strings, names, titles, and email | `db.String(255)` unless a table-specific definition below specifies a smaller maximum |
  | Hashed passwords | `db.String(255)` |
  | Fixed-vocabulary codes (`role`, `type`, `event_type`) | `db.String(20)` for `role`; `db.String(50)` for event/type fields, with named `CheckConstraint` values |
  | Long text (descriptions and Comment bodies) | `db.Text` |
  | Card and Column ordering | `db.Float` |
  | Boolean flags (`is_personal`, `is_done`, `is_read`) | `db.Boolean`, `nullable=False`, with an explicit default |
  | Timestamps | `db.DateTime(timezone=True)` |

- **RATIONALE:** One consistent type per data category avoids needless schema variation and migration churn. Assignment-specific FLOAT ordering is mandatory for Sevy and takes precedence over generic integer-position examples.
- **EXAMPLE:** `title = db.Column(db.String(200), nullable=False)`; `description = db.Column(db.Text, nullable=True)`; `password_hash = db.Column(db.String(255), nullable=False)`; `order = db.Column(db.Float, nullable=False)`.
- **VERIFY:**
  ```bash
  grep -rn 'db.Boolean' backend/app/models | grep -vc 'nullable=False'
  grep -rnE 'db\.DateTime\(\)|db\.DateTime,|db\.DateTime\)' backend/app/models | wc -l
  ```
  Expected results: `0` for both commands. Review each fixed-vocabulary field to confirm it has a named check constraint.

### DB-08 — Card and Column ordering are FLOAT, never INTEGER, with partial unique indexes on active rows

- **RULE:** `board_columns.order` and `cards.order` MUST be declared as `db.Column(db.Float, nullable=False)`. Add named positive-value check constraints (`ck_board_columns_order_positive`, `ck_cards_order_positive`) and parent/order composite lookup indexes (`ix_board_columns_board_id_order`, `ix_cards_column_id_order`). Order uniqueness among active siblings MUST be enforced by PostgreSQL **partial unique indexes**, not by full-table unique constraints:
  - `uq_cards_column_id_order_active` ON `cards` (`column_id`, `"order"`) `WHERE deleted_at IS NULL`.
  - `uq_board_columns_board_id_order_active` ON `board_columns` (`board_id`, `"order"`) `WHERE deleted_at IS NULL`.

  Partial unique indexes are **not deferrable**: PostgreSQL checks them immediately, not at commit, so a statement that moves several rows can collide on an intermediate value. Soft-deleted rows may keep stale `order` values and never block an active row from using the same `order`. A service that reorders or rebalances siblings must therefore be written so that active rows never collide at any statement; the algorithm is owned by `backend.md`, and this file only defines the database constraint. `db.Integer` is forbidden for any Card or Column order/position field. Use a deterministic sibling ordering. `order` is a SQL reserved word; SQLAlchemy handles identifier quoting, and raw SQL MUST quote it as `"order"`.
- **RATIONALE:** The Assignment explicitly requires a FLOAT `order` field for the Card model and a FLOAT ordering strategy for Card movement and Column reordering. Fractional values allow insertion between neighboring items without renumbering every sibling. A partial index protects the ordering of active rows while letting soft-deleted Cards keep their last `order` without blocking new Cards.
- **EXAMPLE:**
  ```python
  __table_args__ = (
      db.CheckConstraint('"order" > 0', name='ck_cards_order_positive'),
      db.Index('ix_cards_column_id_order', 'column_id', 'order'),
      db.Index(
          'uq_cards_column_id_order_active', 'column_id', 'order',
          unique=True,
          postgresql_where=db.text('deleted_at IS NULL'),
      ),
  )
  order = db.Column(db.Float, nullable=False)
  ```
  If sibling Cards have order values `1024.0` and `2048.0`, a Card inserted between them may receive `1536.0`. These values are illustrative.
- **VERIFY:**
  ```bash
  grep -c 'order = db.Column(db.Float, nullable=False)' backend/app/models/card.py backend/app/models/board_column.py
  grep -rniE '(order|position)\w* = db\.Column\(db\.Integer' backend/app/models | wc -l
  grep -rnE 'UniqueConstraint\(.*order' backend/app/models | wc -l
  ```
  Expected results: `1` for each file in the first command, `0` for the second and third. Add a metadata test asserting that `uq_cards_column_id_order_active` and `uq_board_columns_board_id_order_active` exist with `unique` true and the predicate `deleted_at IS NULL`, that both positive-order check constraints and both composite lookup indexes exist, and a database test proving that (a) two active Cards in one Column cannot share an `order`, and (b) a soft-deleted Card's `order` does not block an active Card from using the same value.

### DB-09 — Each table has only its defined domain columns in addition to the four required columns

- **RULE:** The ten v1 tables MUST use the following domain columns. Do not add speculative columns or a parallel membership model. All columns listed as required MUST be non-null; nullable columns are explicitly marked.

  | Table | Model | Domain columns (in addition to DB-05 columns) |
  |---|---|---|
  | `users` | `UserEntity` | `name` String(255) NOT NULL; `username` String(30) NOT NULL, stored lowercase, constraint `uq_users_username` (UNIQUE), CHECK `ck_users_username_format` (`username ~ '^[a-z0-9_]{3,30}$'`); `email` String(255) NOT NULL, unique case-insensitively through the unique index `uq_users_email_lower` on `lower(email)`; `password_hash` String(255) NOT NULL (never exposed outside the persistence layer) |
  | `teams` | `TeamEntity` | `name` String(255) NOT NULL; `is_personal` Boolean NOT NULL, default `False`; `owner_id` UUID FK `users.id` NOT NULL, indexed (`ix_teams_owner_id`); partial unique index `uq_teams_owner_id_personal` ON `teams` (`owner_id`) `WHERE is_personal IS TRUE` |
  | `team_memberships` | `TeamMembershipEntity` | `team_id` UUID FK `teams.id` NOT NULL; `user_id` UUID FK `users.id` NOT NULL, indexed; `role` String(20) NOT NULL, default `member`, CHECK `ck_team_memberships_role` in (`admin`, `member`); UNIQUE `uq_team_memberships_team_id_user_id` (`team_id`, `user_id`) |
  | `boards` | `BoardEntity` | `team_id` UUID FK `teams.id` NOT NULL, indexed; `name` String(100) NOT NULL |
  | `board_columns` | `BoardColumnEntity` | `board_id` UUID FK `boards.id` NOT NULL; `name` String(100) NOT NULL; `order` Float NOT NULL; `is_done` Boolean NOT NULL, default `False`; positive-order CHECK and partial unique index per DB-08 |
  | `cards` | `CardEntity` | `column_id` UUID FK `board_columns.id` NOT NULL; `created_by_id` UUID FK `users.id` NOT NULL; `assignee_id` UUID FK `users.id` NULL, indexed; `title` String(200) NOT NULL; `description` Text NULL; `order` Float NOT NULL; `completed_at` DateTime(timezone=True) NULL; positive-order CHECK and partial unique index per DB-08 |
  | `card_comments` | `CardCommentEntity` | `card_id` UUID FK `cards.id` NOT NULL, indexed; `author_id` UUID FK `users.id` NOT NULL; `parent_comment_id` UUID self-FK `card_comments.id` NULL; `content` Text NOT NULL (the stored text is kept when the Comment is soft-deleted; what the API exposes is owned by `backend.md`) |
  | `notifications` | `NotificationEntity` | `recipient_id` UUID FK `users.id` NOT NULL; `comment_id` UUID FK `card_comments.id` NOT NULL; `type` String(50) NOT NULL, CHECK `ck_notifications_type` in (`mention`); `message` String(255) NOT NULL; `is_read` Boolean NOT NULL, default `False`; UNIQUE `uq_notifications_recipient_id_comment_id_type` (`recipient_id`, `comment_id`, `type`); index `ix_notifications_recipient_id_created_at` (`recipient_id`, `created_at`) |
  | `activity_events` | `ActivityEventEntity` | `board_id` UUID FK `boards.id` NOT NULL; `actor_id` UUID FK `users.id` NOT NULL; `event_type` String(50) NOT NULL, CHECK `ck_activity_events_event_type` in (`card_created`, `card_updated`, `card_moved`, `card_deleted`, `comment_added`); `entity_type` String(50) NOT NULL; `entity_id` UUID NOT NULL; index `ix_activity_events_board_id_created_at` (`board_id`, `created_at`) |
  | `invite_links` | `InviteLinkEntity` | `board_id` UUID FK `boards.id` NOT NULL; `created_by_id` UUID FK `users.id` NOT NULL; `token_hash` String(255) NOT NULL, UNIQUE (`uq_invite_links_token_hash`); `revoked_at` DateTime(timezone=True) NULL |

  Foreign-key columns MUST be indexed unless an existing composite index starts with that foreign key (a partial index does not count). `cards.assignee_id` MUST be nullable to allow unassigned Cards. Store only a hash of an Invite Link token, never the raw token.

  **Notifications:** a `notifications` row has `recipient_id` and `comment_id` and no `user_id` and no `card_id` column. The Card and Board of a Notification are resolved by joins through Comment, Card, Column, Board, and Team (`notifications.comment_id` → `card_comments.card_id` → `cards.column_id` → `board_columns.board_id` → `boards.team_id`), and are never stored.

  **Domain decisions:** `boards.team_id` is ownership: a Board belongs to exactly one Team. Member and Admin access to a Board is resolved through `team_memberships` (`team_id`, `user_id`, `role`) of the owning Team. The Assignment's Board member/administrator language maps to Sevy's Team `member`/`admin` roles; do not create `board_members` or `BoardMemberEntity` alongside `team_memberships`. Guest access is represented by a valid `invite_links` row, not a Team membership. Card assignment is stored in `cards.assignee_id`; the rule that the assignee must belong to the Board's Team is a business rule owned by `backend.md` and `requirements.md`.

  **Personal Teams:** a Team with `is_personal` true is the personal Team of its `owner_id`; at most one such Team exists per user (`uq_teams_owner_id_personal`). Shared Teams have `is_personal` false. The owner of a personal Team has a `team_memberships` row with role `admin` in that Team; this is an integrity rule verified by a service-level test and is not enforced by a database trigger.

  `board_columns.is_done` and `cards.completed_at` persist the completion metric; when `completed_at` is set or cleared is a business rule owned by `backend.md` and `requirements.md`.

  **Example (users and personal Team constraints):**
  ```python
  # backend/app/models/user.py
  __table_args__ = (
      db.UniqueConstraint('username', name='uq_users_username'),
      db.CheckConstraint("username ~ '^[a-z0-9_]{3,30}$'", name='ck_users_username_format'),
      db.Index('uq_users_email_lower', db.text('lower(email)'), unique=True),
  )

  # backend/app/models/team.py
  __table_args__ = (
      db.Index(
          'uq_teams_owner_id_personal', 'owner_id',
          unique=True,
          postgresql_where=db.text('is_personal IS TRUE'),
      ),
  )
  ```

- **RATIONALE:** A fixed schema prevents generated models from inventing fields or relationships. It preserves the Sevy Team ownership model, the required My Tasks/assignee data, Notification-to-Comment integrity, Activity Event analytics data, and Guest Invite Link access while meeting the Assignment's Card UUID/timestamp/FLOAT requirements. Case-insensitive email and username uniqueness is enforced in the database so that no code path can create duplicates that differ only by letter case.
- **EXAMPLE:** `cards.completed_at` is nullable and set only for completed Cards; `cards.assignee_id` references the assigned User; `notifications.comment_id` references the Comment that triggered the mention.
- **VERIFY:**
  - Add a pytest schema test asserting that each model's `__table__.columns.keys()` equals the domain-column list above plus `id`, `created_at`, `updated_at`, and `deleted_at`, with no `board_members` table, no `is_deleted` column on `card_comments`, and no `user_id` or `card_id` column on `notifications`.
  - Assert all ten expected tables are registered exactly once.
  - Assert `users` has `uq_users_username`, `ck_users_username_format` (rejecting uppercase, spaces, and lengths under 3 or over 30), and the unique index `uq_users_email_lower` (rejecting `A@example.com` after `a@example.com`).
  - Assert `team_memberships` has a unique constraint on `(team_id, user_id)` and `ck_team_memberships_role`.
  - Assert `notifications` has a unique constraint on `(recipient_id, comment_id, type)` and the index `ix_notifications_recipient_id_created_at`.
  - Assert `activity_events` has `ck_activity_events_event_type` accepting exactly `card_created`, `card_updated`, `card_moved`, `card_deleted`, and `comment_added`.
  - Assert the DB-08 partial unique indexes on `cards` and `board_columns` (unique flag and `deleted_at IS NULL` predicate) and that no full-table unique constraint on `order` exists.
  - Assert `uq_teams_owner_id_personal` exists with the predicate `is_personal IS TRUE`; a second personal Team for the same owner is rejected, while any number of shared Teams may be owned by that user.
  - Service-level test (not a trigger): registering a user creates a personal Team whose owner has an `admin` membership; a user with no `team_memberships` row for a Team is not resolved as its member (isolation between Teams).

---

## 4. Relationships

### DB-10 — Define both sides with explicit `backref`, `lazy`, and ordering where needed

- **RULE:** Define each ORM relationship once on its chosen parent/collection side with `db.relationship()`, an explicit `backref`, and an explicit `lazy` strategy. Use `lazy='select'` by default. Ordered collections MUST declare `order_by`. Do not use `lazy='dynamic'`. For relationships with multiple foreign keys to the same table, specify `foreign_keys` explicitly. Self-referential relationships MUST specify the correct `remote_side`.
- **RATIONALE:** Both sides of a relationship remain navigable, while loading behavior is intentional. Explicit foreign-key paths prevent SQLAlchemy from guessing incorrectly when a model references the same parent table more than once.
- **EXAMPLE:**
  ```python
  # backend/app/models/board_column.py
  cards = db.relationship(
      'CardEntity',
      backref='column',
      lazy='select',
      order_by='CardEntity.order',
      cascade='all, delete-orphan',
      passive_deletes=True,
  )
  # column.cards and card.column are both navigable.
  ```
- **VERIFY:**
  ```bash
  [ "$(grep -rho 'db\.relationship(' backend/app/models | wc -l)" -eq "$(grep -rho 'backref=' backend/app/models | wc -l)" ] && echo 'backref count OK'
  [ "$(grep -rho 'db\.relationship(' backend/app/models | wc -l)" -eq "$(grep -rho 'lazy=' backend/app/models | wc -l)" ] && echo 'lazy count OK'
  grep -rnE "lazy=['\"]dynamic['\"]" backend/app/models | wc -l
  ```
  Expected: both count checks pass and the final command returns `0`.

### DB-11 — Every foreign key states its delete behavior explicitly

- **RULE:** Every `db.ForeignKey(...)` MUST set `ondelete` explicitly. Use the following v1 policy:
  - `teams.owner_id` → `users.id`: `RESTRICT`.
  - `team_memberships.team_id` → `teams.id`: `CASCADE`.
  - `team_memberships.user_id` → `users.id`: `CASCADE`.
  - `boards.team_id` → `teams.id`: `RESTRICT` (a Team with Boards cannot be physically removed implicitly).
  - `board_columns.board_id` → `boards.id`: `CASCADE`.
  - `cards.column_id` → `board_columns.id`: `CASCADE`.
  - `cards.created_by_id` → `users.id`: `RESTRICT`.
  - `cards.assignee_id` → `users.id`: `SET NULL`.
  - `card_comments.card_id` → `cards.id`: `CASCADE`.
  - `card_comments.author_id` → `users.id`: `RESTRICT`.
  - `card_comments.parent_comment_id` → `card_comments.id`: `CASCADE`.
  - `notifications.recipient_id` → `users.id`: `CASCADE`.
  - `notifications.comment_id` → `card_comments.id`: `CASCADE`.
  - `activity_events.board_id` → `boards.id`: `CASCADE`.
  - `activity_events.actor_id` → `users.id`: `RESTRICT`.
  - `invite_links.board_id` → `boards.id`: `CASCADE`.
  - `invite_links.created_by_id` → `users.id`: `RESTRICT`.

  The `CASCADE` rules on `cards.column_id`, `card_comments.card_id`, and `notifications.comment_id` apply only to physical deletes, which in v1 happen only through the hard deletes of a Column or a Board (DB-06). A Card soft delete and a Comment soft delete only set `deleted_at`, so no foreign-key cascade and no ORM delete cascade is triggered by them. Parent relationships for physically cascading children MUST define compatible ORM cascade settings and `passive_deletes=True` so that hard-delete cascades are performed by the database. Do not physically cascade-delete authored Cards or Comments merely because a Team membership is removed; membership deletion only removes the `team_memberships` row.
- **RATIONALE:** Explicit delete behavior prevents orphan records and accidental loss of user-authored history. It also makes Board/Column deletion, membership removal, and user retention predictable.
- **EXAMPLE:**
  ```python
  column_id = db.Column(
      db.UUID,
      db.ForeignKey('board_columns.id', ondelete='CASCADE'),
      nullable=False,
  )
  assignee_id = db.Column(
      db.UUID,
      db.ForeignKey('users.id', ondelete='SET NULL'),
      nullable=True,
  )
  owner_id = db.Column(
      db.UUID,
      db.ForeignKey('users.id', ondelete='RESTRICT'),
      nullable=False,
      index=True,
  )
  ```
- **VERIFY:**
  ```bash
  grep -rn 'ForeignKey(' backend/app/models | grep -vc 'ondelete='
  ```
  Expected result: `0`. Add pytest coverage proving that deleting a Team membership retains the user's authored Cards and Comments, that deleting a Board physically removes its dependent Columns, Cards, Comments, Notifications, Activity Events, and Invite Links, and that deleting a User who owns a Team is rejected (`RESTRICT`).

### DB-12 — The relationship catalog is fixed and navigable in both directions

- **RULE:** The following relationships MUST exist. Each row is declared once using DB-10 and exposes the listed parent-side attribute and child-side backref. `boards.team_id` is ownership (`TeamEntity.boards`); Member and Admin access is resolved through the `team_memberships` rows of the owning Team (`TeamEntity.memberships`, `UserEntity.memberships`). No relationship to a `board_members` table exists.

  | Parent entity | Parent attribute | Child entity | Backref on child | Relationship details |
  |---|---|---|---|---|
  | `TeamEntity` | `memberships` | `TeamMembershipEntity` | `team` | Cascade delete-orphan; `lazy='select'` |
  | `TeamEntity` | `boards` | `BoardEntity` | `team` | Board ownership. No Board ordering is defined; cascade delete-orphan is not used because Team deletion is restricted while Boards exist |
  | `UserEntity` | `owned_teams` | `TeamEntity` | `owner` | `foreign_keys='TeamEntity.owner_id'`; no ORM delete cascade (the foreign key is `RESTRICT`) |
  | `UserEntity` | `memberships` | `TeamMembershipEntity` | `user` | `lazy='select'`; membership rows may be removed independently |
  | `BoardEntity` | `columns` | `BoardColumnEntity` | `board` | Ordered by `BoardColumnEntity.order`; cascade delete-orphan; passive deletes |
  | `BoardEntity` | `activity_events` | `ActivityEventEntity` | `board` | Ordered by `ActivityEventEntity.created_at`; cascade delete-orphan; passive deletes |
  | `BoardEntity` | `invite_links` | `InviteLinkEntity` | `board` | Cascade delete-orphan; passive deletes |
  | `BoardColumnEntity` | `cards` | `CardEntity` | `column` | Ordered by `CardEntity.order`; cascade delete-orphan; passive deletes |
  | `UserEntity` | `assigned_cards` | `CardEntity` | `assignee` | `foreign_keys='CardEntity.assignee_id'` |
  | `UserEntity` | `created_cards` | `CardEntity` | `creator` | `foreign_keys='CardEntity.created_by_id'` |
  | `CardEntity` | `comments` | `CardCommentEntity` | `card` | Ordered by `CardCommentEntity.created_at`; cascade delete-orphan; passive deletes (the ORM cascade applies to physical deletes only, never to a soft delete) |
  | `CardCommentEntity` | `replies` | `CardCommentEntity` | `parent` | Self-referential; explicit `remote_side`; ordered by creation time; a soft-deleted parent keeps its replies |
  | `CardCommentEntity` | `notifications` | `NotificationEntity` | `comment` | Cascade delete-orphan; passive deletes |
  | `UserEntity` | `comments` | `CardCommentEntity` | `author` | No ORM delete cascade; preserve authored comments |
  | `UserEntity` | `notifications` | `NotificationEntity` | `recipient` | No ORM delete cascade beyond explicit recipient FK policy |
  | `UserEntity` | `activity_events` | `ActivityEventEntity` | `actor` | No ORM delete cascade; preserve actor history |
  | `UserEntity` | `created_invite_links` | `InviteLinkEntity` | `created_by` | No ORM delete cascade |

  `CardEntity` has two foreign keys to `users` and `TeamEntity` has one foreign key to `users`; every User-side relationship to them MUST specify `foreign_keys` explicitly. The polymorphic `ActivityEventEntity.entity_id` is not a foreign key; `entity_type` identifies whether the event refers to a Card or Comment. Do not invent a polymorphic ORM relationship for it. `NotificationEntity` has no relationship to `CardEntity` or `BoardEntity`; those are reached through `comment` (DB-09).
- **RATIONALE:** A fixed relationship catalog means the fiftieth generated model remains as predictable as the first. It prevents missing reverse attributes, ambiguous joins, and accidental cascades that violate retention rules.
- **EXAMPLE:** `card.assignee` resolves to a `UserEntity` or `None`; `user.assigned_cards` returns the Cards assigned to that User; `team.owner` resolves to the owning `UserEntity` and `user.owned_teams` lists the Teams that user owns. `comment.replies` and `reply.parent` navigate a Comment thread in both directions.
- **VERIFY:** Add pytest `test_relationships_both_sides` that calls `db.configure_mappers()` and asserts `hasattr(Parent, parent_attribute)` and `hasattr(Child, backref)` for every catalog row. Also test that `CardEntity.assignee`, `CardEntity.creator`, and `TeamEntity.owner` resolve through their respective foreign keys without `AmbiguousForeignKeysError`, and that no mapped class named `BoardMemberEntity` exists.

---

## Complete Example: `CardEntity`

The example below applies DB-01 through DB-12 to the Assignment's required Card model and Sevy's Team-based access model.

```python
# backend/app/models/card.py
import uuid

from app.extensions import db
from app.utils.time import utc_now


class CardEntity(db.Model):
    __tablename__ = 'cards'
    __table_args__ = (
        db.CheckConstraint('"order" > 0', name='ck_cards_order_positive'),
        db.Index('ix_cards_column_id_order', 'column_id', 'order'),
        db.Index(
            'uq_cards_column_id_order_active', 'column_id', 'order',
            unique=True,
            postgresql_where=db.text('deleted_at IS NULL'),
        ),
    )

    # DB-05: the four required columns
    id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False,
        default=utc_now, onupdate=utc_now,
    )
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # DB-09: Card domain columns
    # column_id needs no separate index: ix_cards_column_id_order starts with it.
    column_id = db.Column(
        db.UUID,
        db.ForeignKey('board_columns.id', ondelete='CASCADE'),
        nullable=False,
    )
    created_by_id = db.Column(
        db.UUID,
        db.ForeignKey('users.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
    )
    assignee_id = db.Column(
        db.UUID,
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    order = db.Column(db.Float, nullable=False)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # DB-10 / DB-12: this side owns Card comments. The ORM cascade applies to
    # physical deletes only; a Card soft delete never touches Comment rows (DB-06).
    comments = db.relationship(
        'CardCommentEntity',
        backref='card',
        lazy='select',
        order_by='CardCommentEntity.created_at',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )
```

The User-side relationships for `assignee` and `creator` are declared in `UserEntity` with explicit `foreign_keys` as required by DB-12.

---

## Database Model Review Checklist

Before considering a generated or modified model complete, verify:

- [ ] The table name is plural `snake_case` and `__tablename__` is explicit; no `board_members` table exists.
- [ ] The model class ends in `Entity` and is the only persisted model class in its file.
- [ ] The four required columns exist with UUID and timezone-aware UTC types.
- [ ] `deleted_at` follows DB-06: soft deletion only for Cards and Comments; a Card soft delete leaves Comment, Notification, and Activity Event rows untouched; there is no `is_deleted` column.
- [ ] Every foreign key uses the correct role-based column name and explicit `ondelete` behavior, including `teams.owner_id`.
- [ ] Data types match DB-07 and the exact schema inventory in DB-09; column lengths are treated as storage capacity, not API limits.
- [ ] `users` has lowercase `username` (`uq_users_username`, `ck_users_username_format`) and case-insensitive email uniqueness (`uq_users_email_lower`).
- [ ] `teams` has `is_personal` and `owner_id`, with the partial unique index `uq_teams_owner_id_personal`.
- [ ] `notifications` has `recipient_id` and `comment_id` and no `user_id` or `card_id`; `ix_notifications_recipient_id_created_at` exists.
- [ ] `activity_events.event_type` uses the named check `ck_activity_events_event_type` with the five allowed values.
- [ ] Card and Column ordering use FLOAT, never INTEGER, with positive-order checks and the partial unique indexes `uq_cards_column_id_order_active` and `uq_board_columns_board_id_order_active` (`WHERE deleted_at IS NULL`).
- [ ] Constraints and indexes have explicit, deterministic names.
- [ ] Relationships have both navigable sides, explicit `backref`, explicit `lazy`, and `order_by` where needed.
- [ ] Multiple foreign keys to the same table specify `foreign_keys`.
- [ ] Deletion behavior preserves authored work when Team membership is removed, and physical cascades occur only for Board and Column hard deletes.
- [ ] Schema and relationship tests pass.

Do not add a new table, column, relationship, or deletion policy merely because it seems convenient. First confirm that it is required by the Sevy requirements or Assignment, then update this guideline and its schema inventory deliberately.
