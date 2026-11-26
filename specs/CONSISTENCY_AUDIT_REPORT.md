# Sevy Consistency Audit Report

Status: COMPLETE for this round. Document consistency was checked by the commands in section 4. Code tests were NOT RUN (no code exists). One check FAILS (changelog labels, section 4, V3). Open decisions remain (section 5).

Round: V7 (spec CHANGELOG entry). Date: 2026-11-26. Task source: the pasted text of `Sevy_Kiro_Conflict_Resolution_Prompt.md` (the file itself is not in the workspace).

## 1. Baseline and canonical sources

| File | Location | Role |
|---|---|---|
| requirements.md | `.kiro/specs/task-management-app/requirements.md` | Canonical for product behavior and acceptance criteria. No copy at `/specs/requirements.md`. |
| CHANGELOG.md | `.kiro/specs/task-management-app/CHANGELOG.md` | Canonical spec history. |
| product.md, tech.md, structure.md | `.kiro/steering/` | Canonical (Kiro-active, `inclusion: always`). |
| backend.md, database.md, frontend.md | `/guidelines/` | Canonical for their rules. They exist only in `/guidelines`; they are not under `.kiro/steering` (see Open Decision OD-20). |
| guidelines/tech.md, guidelines/structure.md | not present | Earlier mirrors were already removed from `/guidelines` before this round. No mirror sync was needed. |
| design.md, tasks.md | not present | Missing source files. Nothing to update. |
| backend/, frontend/, migrations | not present | No application code or migrations exist. Code tests are NOT RUN. |

## 2. Findings and approved decisions (canonical contract)

Every file edit in this round follows this contract. Names are exact.

### P0

1. **Field lengths.** API input: Board name 1-100, Column name 1-100, Card title 1-200, Card description 0-5000, Comment content 1-2000. `String(255)` may remain only as storage capacity, never as an API input maximum.
2. **Username.** `users.username` String(30) NOT NULL, unique, stored lowercase. Registration field `username` 3-30 characters of letters, digits, underscore; compared case-insensitively; normalized to lowercase before storage and lookup. Constraint is a Proposed clarification (OD-05). Safe user payload: `id`, `name`, `username`, `email`, `created_at`. Never `password_hash`.
3. **Notification fields.** Stored columns: `recipient_id` (FK users.id), `comment_id` (FK card_comments.id), `type` (`mention`), `message`, `is_read`, plus the base columns. No `user_id` and no `card_id` columns. Card and Board are resolved through Comment, Card, Column, Board, Team. Payload item: `id`, `type`, `message`, `is_read`, `created_at`, `comment_id`, plus read-only derived `card_id` and `board_id` (OD-19).
4. **Activity event.** Allowed `event_type`: `card_created`, `card_updated`, `card_moved`, `card_deleted`, `comment_added`, in the named CHECK constraint. One `card_deleted` event per successful Card soft delete; none for a rejected delete.
5. **Comment tombstone.** `card_comments.deleted_at` is the only persisted tombstone. No `is_deleted` column. The API derives `is_deleted` as `deleted_at IS NOT NULL`. A deleted Comment with live replies is returned as a tombstone with empty `content`; a deleted Comment without live replies is hidden. The row is always kept.
6. **Active ordering uniqueness.** Partial unique indexes: Cards `(column_id, "order") WHERE deleted_at IS NULL`; Columns `(board_id, "order") WHERE deleted_at IS NULL`. Not deferrable. Positive-order CHECKs stay. Reorder and rebalance run in one transaction using a temporary range above the current maximum active order, then the final values, so active rows never collide.
7. **Access policy (OD-02).** No, malformed, or expired JWT on a JWT-protected route: 401. Authenticated user without Team access to an existing resource: 403. Nonexistent Board/Column/Card/Comment: 404. Soft-deleted Card: 404. Invalid or revoked Invite Link: 404. Valid Guest token on a permitted read: 200. Inaccessible and nonexistent Board-scoped resources use the same generic body `{"error": "Not found or access denied"}` (OD-17). Other 404 bodies: invalid or revoked Invite Link and unknown route `{"error": "Not found"}`; unregistered email when an Admin adds a member `{"error": "User not found"}`; Notification not owned by the requester `{"error": "Not found"}`. Role failure for a Team member keeps its specific 403 message (`Admin access required`).
8. **Guest access decorator.** Exactly two Guest read endpoints: `GET /api/boards/<id>` and `GET /api/cards/<id>/comments`. They use a purpose-specific decorator `@board_access_required(allow_guest_read=True)`, not `@token_required`. Public routes: register, login, health. Every other route uses `@token_required`. Guest never reaches Search, Notifications, Analytics, My Tasks, or Profile, and never writes. A malformed or expired JWT never falls back to Guest. Access Resolution Table, evaluated in order:
   1. Authorization header present and JWT invalid, malformed, or expired: 401 (even with a valid token).
   2. No Authorization header and no `X-Invite-Token`: 401.
   3. Board (or the Card's Board) does not exist, or Card soft-deleted: 404 generic body.
   4. Valid JWT and the user is a Team member of the owning Team: role applies, any token ignored.
   5. Valid JWT, non-member, no token: 403 generic body.
   6. Token invalid, revoked, or malformed: 404 `{"error": "Not found"}`.
   7. Valid, non-revoked token bound to this Board (no JWT, or valid JWT of a non-member): 200 Guest read-only.
   8. Valid token bound to a different Board: 403 generic body.
9. **Team authorization.** `boards.team_id` is ownership. Access resolves through `team_memberships(team_id, user_id)`; role comes from that row. No `board_members` table and no `BoardMemberEntity`. Guest access is separate and Invite-Link based. Service helpers are named for Teams (`require_team_member_service`, `require_team_admin_service`); exceptions `TeamAccessDeniedError` (403) and `AdminAccessRequiredError` (403).
10. **Notification pagination.** `GET /api/notifications` returns `data` with exactly `items`, `page`, `per_page`, `total`, `total_pages`, `unread_count`. `total_pages = ceil(total / per_page)`, and 0 when `total` is 0. `unread_count` counts all unread Notifications of the user, not only the page.
11. **400 error envelope (OD-18).** `{"error": "<one string>"}`. Marshmallow errors are normalized to one deterministic string: fields sorted alphabetically, each entry `<field>: <messages joined by ", ">`, entries joined by " | ". Example: `order: Must be greater than 0. | title: Length must be between 1 and 200.` No nested object under `error`. `ApiError` has `statusCode` and `message` only (no `fieldErrors`). A separately approved `details` property is future work.

### P1

12. **Search.** `GET /api/cards?q=<term>`: `q` alone searches every Board the user can access. `board_id` is optional and narrows the search; when supplied, Team access is verified. Title only, case-insensitive. 300 ms frontend debounce stays.
13. **Schemas.** Add: `AnalyticsQuerySchema` (`start_date`, `end_date`, `YYYY-MM-DD`, both or neither, end not before start, range at most 366 days); `MemberRoleUpdateSchema` (`role`: `admin` or `member`, required); `InviteLinkCreateSchema` (no fields; an empty body or `{}`; unknown fields rejected); `CommentCreateSchema` (`content` 1-2000, `parent_id` optional UUID). Revoking an Invite Link and removing a member take no body.
14. **AuthContext.** Value `{ user, token, isAuthenticated, login, logout, updateUser }`. Login response `data`: `access_token`, `token_type` `Bearer`, `expires_in` 3600, `user`. `PATCH /api/users/me` returns the updated safe `user`; Profile calls `updateUser` with it.
15. **Guest frontend.** `/boards/[id]?invite=<token>` is served without a redirect to `/login`. In Guest mode the API client sends only `X-Invite-Token` (no `Authorization`) and only to the two Guest read endpoints, never to other requests. Guest mode does not create an authenticated session (OD-16).
16. **Personal Team.** `teams.is_personal` BOOLEAN NOT NULL DEFAULT FALSE; `teams.owner_id` UUID NOT NULL FK users.id (ON DELETE RESTRICT); partial unique index `uq_teams_owner_id_personal` on `owner_id` WHERE `is_personal IS TRUE`. The owner has an `admin` row in `team_memberships`. Registration creates user, personal Team, and Admin membership in one transaction. Requirement 4.2 resolves the default Team as the requester's Team with `is_personal` true and `owner_id` equal to the requester.
17. **Rule ownership.** `product.md`: purpose, users, roles, features, scope, product invariants. `frontend.md`: pages, components, state, UI interactions, responsive behavior, API client, UI error mapping. `backend.md`: Blueprints, route/service boundary, schemas, access decorators, response envelope, error handling, auth and password handling, FLOAT ordering allocation. `database.md`: tables, columns, types, constraints, indexes, relationships, deletion policy. `tech.md`: runtime, dependencies, style tooling, deployment, environment, migrations, worker configuration, test tooling, process. `structure.md`: repository layout and file ownership only. Misplaced rules move to the owner and leave a one-line reference.
18. **product.md.** Team-based ownership, Team Admin/Member plus Guest read-only Invite Links, mention-only notifications, title-only search, route inventory owned by requirements Appendix A (no "28 routes" lock), no `REQ-`/`AC-` IDs, no ORM or Flask detail.
19. **ST-12 Rationale check.** Case-insensitive Python validator that counts `FE-nn`/`BE-nn`/`DB-nn` headings and `**Rationale:**` lines (any case) in each guideline file.
20. **Card soft delete keeps Comments.** Comment rows are never physically deleted by a Card soft delete. A soft-deleted Card hides the Card and its Comments, Notifications, and activity from Board, Search, My Tasks, and Analytics reads. Physical cascade only for approved hard deletes (Column delete, Board delete).

### Requirements-quality refinements

R1. Exact result shapes for nested Board Cards, Card list items (`GET /api/cards`), Search results, My Tasks results, and Notification items, plus the six pagination fields.
R2. Requirement 8.5 carve-out: Member and Admin Comment reads need Team access; Guests read only through a valid Board-specific Invite Link on `GET /api/cards/<id>/comments`; no Guest writes; tombstone and soft-delete visibility respected.
R3. Performance target P95 <= 300 ms under 200 concurrent users stays a measurable target. Requires a repeatable load-test script, the API-server measurement point, a 10-minute window, and a recorded environment (Railway plan, Gunicorn worker class and count, database plan, script). Deployment config inspected: `tech.md` TC-20 specifies `--workers 2` and no worker class; no `Procfile` exists. Not claimed as achieved.
R4. Version label V7 for this round (file said V6, CHANGELOG confirmed V1-V6).
R5. Open decisions handled in a dedicated section with question, impact, options, recommended default, and reason unresolved. `[Proposed]` removed only where this contract supplies the decision.
R6. Invite Link and Team member management stay API-only in V1 (OD-14); the product.md member-panel promise is removed.
R7. Every requirement has a `Routes/Pages:` line.

New open decisions created by this round: OD-16 Guest-mode frontend sends no JWT; OD-17 generic denial body text; OD-18 400 string format; OD-19 derived `card_id`/`board_id` in Notification payload; OD-20 backend/database/frontend guidelines live only in `/guidelines`.

## 3. Findings 1 to 20: disposition

Result key: PASS = the document check in section 4 passed; NOT RUN = needs code, a database, or a deployment that does not exist. No finding is marked fully verified because every test named in the guidelines is NOT RUN.

| # | Finding | Files changed | Decision applied | Verification result |
|---|---|---|---|---|
| 1 | Field-length limits | backend.md (BE-05, examples, VERIFY); database.md (DB-07 note) | API limits 100 / 100 / 200; 255 is storage capacity only | PASS: no 255 API limit in backend.md (one hit is the grep that must return 0); requirements 4 to 6 already state 100/100/200. Boundary tests NOT RUN |
| 2 | `username` missing | requirements.md (R13, R9, R26.12); database.md (DB-09); backend.md (BE-05, BE-13); frontend.md (FE-21, FE-25) | `users.username` String(30), lowercase, unique, CHECK format; registration field; safe user payload | PASS: present in the four files. Case-insensitive duplicate and mention tests NOT RUN. Format is a proposal (OD-05) |
| 3 | Notification fields | requirements.md (R9, R26.10); database.md (DB-09); backend.md (BE-06); frontend.md (FE-25) | `recipient_id`, `comment_id`; no stored `user_id` or `card_id`; derived `card_id` and `board_id` in the payload only | PASS: remaining `user_id` and `card_id` hits are explicit negations or service arguments. Derived payload fields are OD-19. This reverses your earlier `user_id` choice because the prompt is authoritative |
| 4 | `card_deleted` | requirements.md (R6.13, R26.11); database.md (DB-09); backend.md (BE-15) | Five event types in named CHECK; one event per successful soft delete | PASS: present in the three files. Event tests NOT RUN |
| 5 | Comment tombstone | requirements.md (R8, Glossary); database.md (DB-06, DB-09); backend.md (BE-06, BE-15); frontend.md (FE-31) | `deleted_at` only; `is_deleted` derived; tombstone only when live replies exist | PASS: no `is_deleted` column definition anywhere. Edge case with deleted middle comments is open (U-05) |
| 6 | Active order uniqueness | database.md (DB-08, DB-09); backend.md (BE-14); tech.md (TC-10); requirements.md (R26.7, R26.8) | Two partial unique indexes, not deferrable; two-phase rebalance in one transaction | PASS: old `uq_*_order` names and `UniqueConstraint` on order are gone; every "deferrable" hit says "not deferrable". Metadata and concurrency tests NOT RUN |
| 7 | Access denial vs not found | requirements.md (OD-02, R1, R2, R3, R6, R8, R10); backend.md (BE-08, BE-10); frontend.md (FE-24); product.md (PR-03); tech.md (TC-06 stub) | 401 / 403 / 404 policy; one generic body `Not found or access denied` for 403 and 404 on Board-scoped resources | PASS: legacy `"Access denied"` and per-entity bodies remain only in the V1 to V6 changelog history and one Appendix B note. Status-code tests NOT RUN. Wording is OD-17 |
| 8 | Guest decorators | requirements.md (R3); backend.md (BE-08); frontend.md (FE-23, FE-30); tech.md (TC-08 stub); product.md (PR-09) | `@board_access_required(allow_guest_read=True)` on exactly two routes; eight-step table; bad JWT never falls back to Guest | PASS: two routes and eight steps stated consistently. Guest tests NOT RUN. This reverses the V5 rule "expired JWT treated as absent" |
| 9 | Team-based authorization | backend.md (BE-09); database.md (DB-09, DB-12); structure.md (S-1, ST-10); product.md (P-1) | `boards.team_id` ownership; access through `team_memberships`; helpers `require_team_member_service` and `require_team_admin_service` | PASS: `board_members` and `BoardMemberEntity` appear only in prohibitions, the assignment mapping note, and changelog history |
| 10 | Notification pagination | requirements.md (R9.7); backend.md (BE-07); frontend.md (FE-25, FE-28); product.md (PR-05) | Six fields; `total_pages` = ceil(total / per_page), 0 when empty; `unread_count` over all unread | PASS: `total_pages` in four files. Zero-result test NOT RUN |
| 11 | 400 envelope | requirements.md (R20.1, R20.13, R22.4); backend.md (BE-04, BE-07, BE-11); frontend.md (FE-23, FE-24); tech.md (TC-06, TC-13 stubs) | One deterministic string; `ApiError` has `statusCode` and `message` only | PASS: `field-keyed` and `fieldErrors` remain only as negations and in changelog history. Exact format is OD-18 |
| 12 | Search | requirements.md (R10); backend.md (BE-05); frontend.md (FE-29); product.md (PR-07) | `q` alone searches all accessible Boards; `board_id` optional; title only; 300 ms debounce | PASS: no "q requires board_id" text. Tests NOT RUN |
| 13 | Missing schemas | backend.md (BE-05); requirements.md (Validation Rules in R3, R8, R11, R12) | Analytics query, member role update, Invite Link create, Comment create and update | PASS: all five names present in the catalog and its VERIFY loop |
| 14 | AuthContext user updates | requirements.md (R13.5, R19, R21); backend.md (BE-06, BE-07); frontend.md (FE-19) | `updateUser`; login returns safe `user`; `PATCH /api/users/me` returns safe `user` | PASS: `updateUser` in requirements and frontend.md. RTL tests NOT RUN |
| 15 | Guest invite frontend | requirements.md (R21.11, R21.16, R21.17); frontend.md (FE-22, FE-23, FE-30); tech.md (TC-12, TC-13 stubs) | Page served without redirect; Guest mode sends only `X-Invite-Token`, only on the two read requests | PASS: documented in requirements and frontend.md. Omitting the JWT is OD-16. Playwright test NOT RUN |
| 16 | Personal Team | requirements.md (R4.2, R13.2, R26.9); database.md (DB-08, DB-09, DB-11, DB-12); backend.md (BE-15); product.md (PR-10) | `is_personal`, `owner_id` NOT NULL RESTRICT, partial unique index, owner is Admin, one transaction | PASS: present in the four files. Uniqueness and isolation tests NOT RUN. Meaning of `owner_id` for shared Teams is U-02 |
| 17 | Duplicate rules | tech.md, structure.md, product.md, frontend.md, backend.md, database.md | One owner per rule; TC-06 to TC-08, TC-11 to TC-16 became `(moved)` stubs; ST-10 and ST-03 reference owners; no mirrors exist | PASS: 0 duplicated sentences of 110 characters or more across the six files (heuristic, exact match). Not a proof of no semantic overlap |
| 18 | Stale product.md | product.md | Team model, mentions only, title search, route inventory owned by Appendix A, F-11 API-only, F-13, PR-09, PR-10, G-07, G-08 | PASS: no `board_members`, `28 routes`, `REQ-`, `AC-`, `card_assigned`, `card_moved`, `title and description` |
| 19 | ST-12 Rationale check | structure.md (ST-12) | Case-insensitive Python checker replaces the brittle grep | PASS: run against the three guideline files, 59 headings, exit 0 |
| 20 | Card soft delete keeps Comments | requirements.md (R6.16, OD-15); database.md (DB-06, DB-11, DB-12); backend.md (BE-15) | Comment rows never deleted by a Card soft delete; physical cascade only on Board and Column delete | PASS: no sentence deletes a soft-deleted Card's Comments. Retention tests NOT RUN |

### Requirements-quality refinements (R1 to R7)

| Ref | Item | Result |
|---|---|---|
| R1 | Result shapes | PASS: shapes with `id` in requirements (R4, R9, R10), backend.md BE-06, frontend.md FE-25. Unsourced shapes are tagged Proposed |
| R2 | Guest comment-read carve-out | PASS: R8.5 and R8.19 edited; Guests cannot write |
| R3 | Performance target | PASS (documentation only): P95 <= 300 ms stays a target; `tech.md` TC-23 defines script, window, environment record; status is "not measured". Railway plan, worker class, database plan, script: NOT RECORDED. Nothing is claimed as achieved |
| R4 | Version label | PASS: file now says V7; CHANGELOG has V7 |
| R5 | OD review | PASS: 9 resolved, 11 open with question, impact, options, default, reason; criterion tags point only at open decisions |
| R6 | Invite Link and member UI | PASS: API-only in V1 (OD-14); the product.md member-panel promise is removed |
| R7 | Traceability | PASS: 26 of 26 requirements have `Routes/Pages:`; the 32 routes named equal the 32 routes of Appendix A |

## 4. Verification commands and results

The environment has no `grep` and no WSL distribution, so shell-based VERIFY lines inside the guideline files were not run. The checks below used Python 3.14 (`py`) and PowerShell, read-only, from the repository root. The audit scripts are in the temp folder and are not part of the repository.

| # | Check | Command or tool | Result |
|---|---|---|---|
| V1 | Stale terms, field names, tokens, `board_members`, 255, object-valued errors, deferrable, per-entity bodies | Python audit script over 8 documents (regex search, line-level hits reviewed by hand) | PASS (remaining hits classified as negations, prohibitions, history, or service arguments) |
| V2 | ST-12 guideline checker | command copied from `structure.md` ST-12, executed with `exec` | PASS: 59 headings (FE 32, BE 15, DB 12), exit 0, no MISSING |
| V3 | TC-21 changelog checker | command copied from `tech.md` TC-21, pointed at `.kiro/specs/task-management-app/CHANGELOG.md` | FAIL: 6 refinement rounds, but V2, V3, V4, V5 lack `**Prompt**`, `**Before**`, `**After**`; exit 1. `specs/CHANGELOG.md` does not exist |
| V4 | Requirements format | `validate_spec_format` | PASS: no issues |
| V5 | Routes/Pages against Appendix A | Python | PASS: 32 routes named, 32 in Appendix A, none unknown, none unused; 26 `Routes/Pages:` lines, 0 old labels |
| V6 | Reference integrity | Python: every `FE-`, `BE-`, `DB-`, `TC-`, `ST-`, `PR-`, `NFR-`, `OD-` reference resolves; every `R<N>.<k>` and "Requirement N criterion k" reference exists | PASS: none unresolved |
| V7 | Duplicate rule text | Python: sentences of 110 characters or more shared by two of the six steering and guideline files | PASS: 0 (heuristic) |
| V8 | OD tags | Python: criterion tags vs Resolved and Open lists | PASS: no tag points at a resolved or unknown decision |
| V9 | Front matter and heading IDs | Python | PASS: `inclusion: always` in the three steering files; FE-01 to FE-32, BE-01 to BE-15, DB-01 to DB-12 unique |
| V10 | Cross-file contract matrix | Python regex per file (section 7) | PASS after one regex false negative (R26.7 states the order-uniqueness outcome in other words) |

NOT RUN (cannot run; no code, database, or deployment exists): `pytest`, coverage, RTL/Jest, Playwright, `flake8`, `flask routes`, `flask db upgrade` and `flask db check`, `curl` health and CORS checks, the load test (TC-23, status "not measured"), every shell VERIFY line in the guidelines and steering, and the TC-22 commit-prefix check (the repository has one commit, `initial commit`, which does not follow the prefix rule).

## 5. Remaining open decisions

### Open decisions in requirements.md (none approved)
OD-01 Member Column permissions. OD-05 username format. OD-08 Members delete only own Cards. OD-10 stateless logout. OD-13 409 on equal `order` and the reorder body. OD-14 API-only member and Invite Link management. OD-16 Guest mode omits the JWT. OD-17 text of the generic denial body. OD-18 format of the 400 string. OD-19 derived `card_id` and `board_id` in Notification items. OD-20 guideline files live only in `/guidelines` and are not loaded as Kiro steering.

### Unresolved ambiguities found while editing (need a decision or a one-line rule)
| ID | Question | Where |
|---|---|---|
| U-01 | Finding 6 puts a `deleted_at IS NULL` predicate on Column order uniqueness, but Columns are hard-deleted. Should Columns be soft-deletable? | requirements Glossary "Active"; database.md DB-08 |
| U-02 | What does `teams.owner_id` mean for a shared Team (creator?) | database.md DB-09 |
| U-03 | Requirement 26.3 asks for a case-insensitive Card title search index. A `lower(title)` B-tree does not help substring search; a trigram index needs `pg_trgm`. No index was added | requirements R26.3; database.md |
| U-04 | Should `GET /api/notifications` omit Notifications of a soft-deleted Card? | requirements R9, R6.16 |
| U-05 | The tombstone rule counts direct live replies only. A deleted middle comment can leave a grandchild with a hidden parent | requirements R8.11; backend.md BE-15 |
| U-06 | `PATCH` or `DELETE` on an already-deleted Comment, and a reply to a deleted parent, are unspecified | requirements R8; backend.md |
| U-07 | A non-existent `team_id` in `POST /api/boards` gets 403 generic (BE-14) but OD-02 says a body ID that does not exist is 400 | backend.md; requirements R4.4 |
| U-08 | A Member deleting another user's Card raises `AdminAccessRequiredError`; a dedicated exception waits for OD-08 | backend.md BE-09 |
| U-09 | A non-existent `invite_id` returns `{"error": "Not found"}` (my choice) | requirements R1 Validation Rules |
| U-10 | Notification and search links use `/boards/<board_id>?card=<card_id>`. No source defines it | frontend.md FE-28, FE-29 |
| U-11 | The bell is not fetched on mount, so it is empty for the first 30 seconds (TC-15 test kept as written) | frontend.md FE-28 |
| U-12 | Polling failures show no toast except 401 | frontend.md FE-28 |
| U-13 | The layout fetches `GET /api/users/me` when the cookie exists to restore the user; the JWT is passed explicitly per call | frontend.md FE-19, FE-22, FE-23 |
| U-14 | In Guest mode a 403 shows the not-found state; other unlisted statuses show the generic toast; FE-20 (`router.refresh()`) and FE-31 (local update for Comments) read as an exception; the Board list item shape is not defined anywhere | frontend.md FE-20, FE-24, FE-25, FE-30, FE-31 |
| U-15 | `InvalidTargetColumnError` (400) was added because R7.4 and R7.5 need it; invalid path UUIDs raise a Marshmallow error from the guard decorators | backend.md BE-10, BE-08 |
| U-16 | ST-12 requires `T-<NN>` task IDs, but the Kiro task workflow numbers tasks `1.1`, `2.1` | structure.md ST-12 |
| U-17 | The server-side P95 needs an access-log duration; the Procfile text in TC-20 has no access-log option | tech.md TC-20, TC-23 |
| U-18 | The changelog format conflicts: change-management steering uses `### Changes`, `### Reason`, `### Impact`; ST-12 and TC-21 require `**Prompt**`, `**Before**`, `**After**`. V6 and V7 carry both; V2 to V5 carry only the first set | CHANGELOG.md; structure.md; tech.md |
| U-19 | The access decorator and `require_team_*_service` both read membership; Guest routes trust the `access` object. BE-14 also locks the parent row before sibling rows | backend.md BE-08, BE-14 |

## 6. Missing or uninspectable source files

| Item | Status |
|---|---|
| `Sevy_Kiro_Conflict_Resolution_Prompt.md` | Not in the workspace; the pasted text was used |
| `design.md`, `tasks.md` (working and submission copies) | Do not exist; nothing to update; the V7 changelog lists what they must follow |
| `/specs/requirements.md`, `/specs/design.md`, `/specs/tasks.md`, `/specs/CHANGELOG.md` | Do not exist; `/specs/` was created in this round only to hold this report; the submission copy has not been published |
| `guidelines/tech.md`, `guidelines/structure.md` | Not present; they were removed before this round, so no mirror sync was needed |
| `guidelines/VIOLATIONS.md` | Does not exist (required by the rubric and TC-21) |
| `backend/`, `frontend/`, `backend/migrations/`, `Procfile`, `.env.example`, load-test script, README | Do not exist |
| Standalone assignment Scenario or Requirements file | Not in `.kiro/references`; compliance with the original brief cannot be asserted beyond the four reference files |

## 7. Cross-file consistency matrix

`yes` = the contract item is stated in that file; `-` = not that file's job (ownership matrix); `GAP` = the check did not find it.

| Contract item | requirements | database | backend | frontend | tech | structure | product |
|---|---|---|---|---|---|---|---|
| username (unique, lowercase) | yes | yes | yes | yes | - | - | - |
| Notification `recipient_id` and `comment_id` | yes | yes | yes | yes | - | - | - |
| `card_deleted` event | yes | yes | yes | - | - | - | - |
| Comment tombstone via `deleted_at`, derived `is_deleted` | yes | yes | yes | yes | - | - | - |
| Partial unique active order indexes | yes (R26.7; regex false negative) | yes | yes | - | yes | - | - |
| 403 / 404 policy and generic body | yes | - | yes | yes | - | - | yes |
| Guest decorator and `X-Invite-Token` | yes | - | yes | yes | yes (stub) | - | yes |
| Team-based authorization, no `board_members` | yes | yes | yes | - | - | yes | yes |
| Notification `total_pages` | yes | - | yes | yes | - | - | yes |
| 400 error is one string | yes | - | yes | yes | - | - | yes |
| Search: `q` alone, optional `board_id`, title only | yes | - | yes | yes | - | - | yes |
| Missing request schemas | - | - | yes | - | - | - | - |
| `updateUser` and safe user in login | yes | - | yes | yes | - | - | - |
| Personal Team (`is_personal`, `owner_id`) | yes | yes | yes | - | - | - | yes |
| Card result shapes with `id` | yes | - | yes | yes | - | - | - |
| Card soft delete keeps Comments | yes | yes | yes | - | - | - | yes |
| Guest never reaches search, notifications, analytics, My Tasks | yes | - | yes | yes | - | - | yes |
| API-only member and Invite Link management | yes | - | - | yes | - | yes | yes |

## 8. Deviations, additions, and things to know

- **Earlier decisions that this task overrides** (the prompt is authoritative): notification recipient field `user_id` (your earlier answer) became `recipient_id`; V5 rule "expired or invalid JWT is treated as absent" became "401, never Guest"; V6 per-entity not-found bodies became one generic body; V6 field-keyed 400 object became one string; the V6 default "Frontend still forwards the JWT on invite pages" became Guest mode without the JWT (OD-16).
- **Additions not in the prompt** (each needed to keep documents consistent): unique index on `lower(email)` (R13 already said case-insensitive email); notification and FK indexes; `InvalidTargetColumnError`; `TC-23` load-test record; `BE-13` to `BE-15` and `FE-22` to `FE-32` (rules moved out of `tech.md` and `structure.md`, plus new Guest and retention rules); `PR-09`, `PR-10`, `F-13`, `G-07`, `G-08` in product.md; hook `useCardSearch` and component `MyTaskRow`.
- **Not changed:** application code, models, migrations, `design.md`, `tasks.md`, `.kiro/references`, `change-management.md`, `development-workflow.md`.
- **Not claimed:** that any test passes, that the P95 target is met, or that full consistency is proven. The document checks are text and structure checks; they cannot prove the behavior.
- **Counts not independently verified:** the numbers in the V7 changelog entry (54 criteria edited, 14 appended, 9 resolved and 11 open decisions, 19 tags) came from the editing step. Only the decision counts and the tag mapping were re-checked by script (section 4, V8); the edited and appended criterion counts were not recounted.
- **Final check run after the last edit:** alidate_spec_format on equirements.md reported no issues.
