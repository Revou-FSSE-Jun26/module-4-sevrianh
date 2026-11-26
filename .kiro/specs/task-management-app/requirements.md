# Requirements Document

## Introduction

Sevy is a team task management web application similar to Trello. Team members organize work on Boards made of ordered Columns and Cards, move Cards between Columns with drag-and-drop, discuss work in threaded Comments, receive Notifications, track the Cards assigned to them, and monitor Board activity. The goal is fast, shared visibility of who is doing what.

This document is currently at **Version 9 (V9)**. It was built from the V2 refinement of the original 17-requirement Sevy V1 document, which integrated the FSSE Module 4 assignment reference files (`.kiro/references/backend-implementation.md`, `frontend-implementation.md`, `deliverables.md`, `grading-rubric.md`). Changes after V2 are recorded in `CHANGELOG.md`. V8 records the approval by the user of the recommended defaults of OD-01, OD-05, OD-08, OD-10, OD-13, OD-14, OD-16, OD-17, OD-18, OD-19, and OD-20, so that no open decision remains. V7 applied the decision contract in `specs/CONSISTENCY_AUDIT_REPORT.md` (section 2); where the contract and an earlier decision of this document differ, the contract applies. The original Sevy Team model (Teams own Boards, Admin and Member roles, read-only Guests through Invite_Links) is kept. The assignment's endpoint list, FLOAT ordering strategy, My Tasks, Profile, JWT authentication, response envelope, and frontend behaviors are added. Requirements 1 to 17 keep their V1 numbers; Requirements 18 to 26 are new in V2. Requirements 27 to 29 (deployment, automated testing, repository and documentation) are new in V9.

The frontend uses Next.js, React, TypeScript, and Tailwind CSS. The backend uses Flask and Python. The database is PostgreSQL accessed through SQLAlchemy.

Limitation: the assignment has no standalone Scenario or Requirements file in the workspace. This document is derived from the four reference files above, the existing Sevy V1 requirements, and the steering files `product.md`, `tech.md`, and `structure.md`. Compliance with the original assignment brief cannot be asserted beyond those files.

### Document Conventions

- **Priority**: Mandatory (required by the assignment reference files), Retained (existing Sevy requirement kept for security, reliability, data integrity, or measurable NFR value), Optional (not used in V2).
- **Source**: Assignment, Existing Sevy, Both, or Proposed clarification (neither source defines the behavior; the clarification is proposed here).
- A criterion tagged **[Proposed, A-nn]** depends on an assumption listed in the section "Assumptions". Tags of the form `[Proposed, OD-nn]` no longer occur, because every decision OD-01 to OD-20 is resolved (V8); a decision listed under "Resolved decisions" carries no tag. The marker **[Inactive; deferred, OD-04]** remains.
- A bare **[Proposed]** label marks a response shape or key set that the sources do not define; it is a design choice that design.md may refine and that has not been separately approved.
- Every requirement carries a `Routes/Pages:` line under Related Areas. It lists routes from Appendix A and pages from Requirement 21; for a requirement that applies to many routes it starts with the word "cross-cutting", and for a data-model requirement with the word "database".
- A criterion tagged **[Inactive; deferred, OD-nn]** is stated for a later version and is not part of the current scope.
- All JSON keys use snake_case. All identifiers are UUIDs unless stated otherwise.
- **Criterion IDs**: each acceptance criterion is identified as `R<N>.<k>`, where N is the Requirement number and k is the criterion number inside that Requirement (for example, `R6.14` is Requirement 6 criterion 14). Traceability in `design.md` uses these IDs. Requirement headings keep the form "Requirement N".

## Glossary

- **Sevy**: The team task management web application described in this document.
- **API**: The Flask backend HTTP interface used by the Frontend, organized as eight Blueprints (auth, boards, columns, cards, comments, notifications, analytics, users).
- **Frontend**: The Next.js, React, TypeScript, and Tailwind CSS web client.
- **Database**: The PostgreSQL database accessed through SQLAlchemy.
- **Team**: A group of users that owns one or more Boards. Every registered user belongs to at least one Team.
- **Board**: A workspace owned by exactly one Team, containing ordered Columns.
- **Column**: An ordered list of Cards within a Board, for example To Do, Doing, or Done. A Column has a boolean `is_done`.
- **Card**: A task that lives in exactly one Column, with a title, a description, an optional Assignee, and a nullable `completed_at`.
- **order (FLOAT)**: A positive floating-point value stored in `order` on each Column (within its Board) and each Card (within its Column). Items are returned sorted by `order` ascending. Replaces the V1 integer Position.
- **ORDER_STEP**: The constant 1024.0, the spacing used for the first item, appended items, and rebalanced items.
- **MIN_GAP**: The constant 1e-6, the smallest allowed difference between adjacent `order` values before a rebalance is required.
- **Rebalance**: Reassigning the `order` values of all non-deleted siblings to 1024.0, 2048.0, 3072.0, and so on while preserving their relative sequence.
- **Soft Delete**: Setting `deleted_at` on a Card or a Comment instead of removing the row. A soft-deleted Card is omitted from every collection in API responses, and a direct request that names its ID returns 404 with the Generic_Denial_Body (Requirement 1 criterion 2). A Card soft delete keeps the rows of the Card's Comments (Requirement 6 criterion 16).
- **Active (Card or Column)**: A Card or Column that is not soft-deleted. Columns are hard-deleted (Requirement 5 criterion 10), so every existing Column is active.
- **Generic_Denial_Body**: The single error body `{"error": "Not found or access denied"}` returned for a Board, Column, Card, or Comment that does not exist (404), for a soft-deleted Card (404), and for an existing resource the requester cannot access (403).
- **Comment**: A message on a Card. A Comment may be a reply to another Comment, forming a thread. A Comment is deleted by setting `deleted_at`; the row is kept.
- **Tombstone**: A deleted Comment (`deleted_at` set) that still has at least one live reply (a reply whose `deleted_at` is null). A Tombstone is returned with `is_deleted` true and empty `content`. `is_deleted` is derived (`deleted_at` is not null) and is not stored.
- **Mention**: A reference to a Team member by username inside a Comment, written as `@username`.
- **Notification**: A record created for a Team member (the recipient, stored as `recipient_id`) when that member is mentioned in a Comment (stored as `comment_id`). The Card and Board of a Notification are resolved through the Comment.
- **Guest**: A user who views a Board through an Invite_Link and is not a Team member. A Guest has read-only access and reaches only the two Guest_Read_Endpoints.
- **Guest_Read_Endpoint**: Either `GET /api/boards/<id>` or `GET /api/cards/<id>/comments`. These are the only endpoints that evaluate `X-Invite-Token`.
- **Guest_Mode**: The Frontend state of the page `/boards/[id]?invite=<token>`, in which the API_Client sends only `X-Invite-Token` and no `Authorization` header, and no authenticated session is created.
- **Personal Team**: A Team with `is_personal` true and `owner_id` equal to one user, created at that user's registration; the owner is its Admin.
- **Member**: A Team member with the Team role `member`. Corresponds to the assignment's "board member".
- **Admin**: A Team member with the Team role `admin`. Corresponds to the assignment's "board administrator". The Admin role is held at Team level and applies to every Board of that Team.
- **Invite_Link**: A URL token that grants a Guest read-only access to one Board.
- **Assignee**: The single user referenced by `assignee_id` on a Card. The Assignee must be a member of the Team that owns the Card's Board.
- **Completed Card**: A non-deleted Card whose `completed_at` is not null.
- **My Tasks**: The view of all non-deleted Cards whose Assignee is the signed-in user, grouped by Board name.
- **Activity_Event**: A record of a change on a Board with an event type, the acting user, the Board, and a UTC timestamp. Event types are `card_created`, `card_updated`, `card_moved`, `card_deleted`, and `comment_added`.
- **JWT**: The JSON Web Token returned by login and sent as `Authorization: Bearer <token>`.
- **AuthContext**: The Frontend React context that holds the JWT and the signed-in user and exposes `user`, `token`, `isAuthenticated`, `login`, `logout`, and `updateUser`.
- **API_Client**: The single Frontend module through which all HTTP requests to the API are made.
- **ApiError**: The Frontend error class thrown by the API_Client on non-2xx responses and when no HTTP response is received, with the fields `statusCode` (number; 0 when no HTTP response is received) and `message` (string) only. The API error envelope is always `{"error": "<non-empty string>"}`; the API_Client sets `message` to that string.
- **Authorization_Service**: The API component that decides whether a user may perform an action on a Board.
- **Access Resolution Table**: The ordered eight-step table in the Validation Rules of Requirement 3 that decides the response to every request to a Guest_Read_Endpoint from the Authorization header, the JWT state, the existence of the resource, Team membership, and the `X-Invite-Token` state. The first matching step applies.
- **Search_Service**: The API component that finds Cards by title keyword.
- **Analytics_Service**: The API component that computes per-board statistics.
- **Notification_Service**: The API component that creates and returns Notifications.
- **Kanban_Board**: The Frontend Client Component that renders the Columns and Cards of a Board and owns drag state.
- **Card_Detail_Modal**: The Frontend Client Component, rendered inside BaseModal, that shows one Card and its Comments.
- **Notification_Bell**: The Frontend header component that shows the unread Notification count.
- **BaseButton**: The shared Frontend button component with variants `primary`, `secondary`, and `destructive`.
- **BaseBadge**: The shared Frontend badge component with color variants `gray`, `green`, `yellow`, `red`, and `blue`.
- **BaseModal**: The shared Frontend modal shell that wraps every form.
- **Toast**: A transient Frontend message shown through the shared toast helper.
- **Assignment Terminology Mapping**: "Board member" in the assignment corresponds to a Member of the Team that owns the Board; "board administrator" corresponds to an Admin of that Team; the assignment's `board_members` concept is realized by Team membership.

## Assumptions, Resolved Decisions, and Open Decisions

This section has three parts. "Resolved decisions" lists every decision of this document, OD-01 to OD-20: decisions settled by the decision contract of V7 (`specs/CONSISTENCY_AUDIT_REPORT.md`, section 2) or by the current requirements, and decisions approved by the user in V8 (the recommended defaults of OD-01, OD-05, OD-08, OD-10, OD-13, OD-14, OD-16, OD-17, OD-18, OD-19, and OD-20); the criteria that depend on them carry no tag. "Open Decisions" is empty. "Assumptions" lists A-01 to A-05; a criterion that depends on an assumption carries the tag **[Proposed, A-nn]**.

### Resolved decisions

- **OD-01 (Member column permissions)**: A Member creates Columns; only an Admin renames, reorders, deletes, or changes `is_done` of a Column (Requirement 2 criteria 5 and 6, Requirement 5 criteria 5, 6, 10, and 14). *Alternatives considered*: steering `product.md` PR-03 split (Members add, rename, and reorder; Admins delete); not chosen because the assignment is silent and the Sevy V1 split is stricter. *Source*: user approval of the recommended default (V8).
- **OD-02 (Access and not-found policy)**: A request with no JWT, or with a malformed or expired JWT, on a JWT-protected route is answered 401. An authenticated user without Team access to an existing Board, Column, Card, or Comment gets 403 with the Generic_Denial_Body. A Board, Column, Card, or Comment that does not exist gets 404 with the Generic_Denial_Body, and so does a soft-deleted Card. An invalid or revoked Invite_Link token on a Guest_Read_Endpoint gets 404 `{"error": "Not found"}`. A valid Guest token on a permitted read gets 200. Existence is evaluated first (404), then Team membership and role (403). A Team member who lacks the required role keeps a specific 403 message (for example `{"error": "Admin access required"}`). Other 404 bodies: unknown route `{"error": "Not found"}`; unregistered email when an Admin adds a Team member `{"error": "User not found"}`; a Notification not owned by the requester `{"error": "Not found"}`. An ID in a request body or query string that does not exist is a validation failure (400), except `board_id` in `GET /api/cards` (Requirement 10 criterion 3). Cost: the status codes 403 and 404 differ, so an authenticated requester can tell a non-existent ID from an existing ID of another Team; the IDs are random UUIDs, so guessing an existing ID is not practical. This replaces the V2 to V5 rule (403 for non-existent IDs) and the V6 per-entity 404 bodies. *Source*: contract findings 7 and 8; the text of the denial body is fixed by OD-17.
- **OD-03 (Reply behavior when a parent Comment is deleted)**: A Comment delete sets `deleted_at` and keeps the row. A deleted Comment with live replies is returned as a Tombstone (`is_deleted` true, empty `content`, replies kept); a deleted Comment without live replies is omitted from reads. `is_deleted` is derived and not stored. *Source*: contract finding 5.
- **OD-04 (Notification triggers)**: Mentions only. The `card_assigned` trigger stays inactive and deferred (Requirement 9 criterion 15). *Source*: current requirements (Requirement 9); steering `product.md` PR-05 lists more triggers and is not changed by this document.
- **OD-05 (Username format)**: `username` has 3 to 30 characters of letters, digits, and underscore, is compared case-insensitively, is stored in lowercase, and cannot be changed through `PATCH /api/users/me` (Requirement 9 criterion 1, Requirement 13 criteria 1 and 3, Requirement 26). Mentions need a unique handle, but the assignment profile has only name and email. *Alternatives considered*: a different length range or character set; not chosen because no source defines one. *Source*: user approval of the recommended default (V8).
- **OD-06 (Personal Team at registration)**: Registration creates the user, a personal Team (`is_personal` true, `owner_id` = the new user), and the Admin membership in one transaction. `POST /api/boards` without `team_id` uses the requester's personal Team. *Source*: contract finding 16.
- **OD-07 (Route inventory)**: The route inventory in Appendix A is authoritative (32 routes). The 28-route lock of steering `product.md` PR-02 is not applied; per PR-02 a CHANGELOG entry must exist before code for the 4 routes beyond the steering list is generated, and the V2 entry records them. *Source*: contract finding 18; V2 changelog.
- **OD-08 (Member deletes own Cards only)**: An Admin deletes any Card; a Member deletes only Cards where `created_by_id` equals the Member (Requirement 2 criterion 9, Requirement 6 criterion 6). *Alternatives considered*: any Member deletes any Card (Sevy V1 did not name ownership); not chosen because steering PR-03 limits Members to own Cards. *Source*: user approval of the recommended default (V8).
- **OD-09 (Search fields)**: Card title only, case-insensitive. *Source*: contract finding 12.
- **OD-10 (Stateless logout)**: Logout clears Frontend state and the `sevy_token` cookie only; an unexpired JWT stays valid until expiry (Requirement 13, Requirement 21 criterion 12). The cookie is written by Frontend JavaScript and cannot be HttpOnly (steering TG-01). *Alternatives considered*: a server-side token deny list; not chosen because it adds a table and a route outside Appendix A. *Source*: user approval of the recommended default (V8).
- **OD-11 (Definition of completion)**: Column `is_done` plus Card `completed_at` (Requirement 24). *Source*: current requirements (Requirement 24).
- **OD-12 (Guest transport)**: A Guest sends the header `X-Invite-Token` on the two Guest_Read_Endpoints only (`GET /api/boards/<id>` and `GET /api/cards/<id>/comments`). The API resolves access with the eight-step Access Resolution Table of Requirement 3. A malformed or expired JWT never falls back to Guest access (401). The Frontend omits the JWT on invite pages (OD-16). *Source*: contract findings 8 and 15.
- **OD-13 (409 on equal order and reorder body)**: A submitted `order` equal to a sibling's `order` is rejected with 409 and the standard error envelope only; the client computes a new `order`. The Column reorder body is `{"column_id": "<uuid>", "order": <positive float>}` (Requirement 5 criteria 6 and 8, Requirement 7 criterion 6). *Alternatives considered*: the server shifts siblings; not chosen because the sources define neither the conflict response nor the reorder body and shifting hides conflicts. *Source*: user approval of the recommended default (V8).
- **OD-14 (API-only Team member management and Invite_Link management)**: Team member management and Invite_Link management are API-only in V1: no member panel and no invite UI, apart from the Guest view of Requirement 3 criterion 8 (Requirement 3 criteria 1 and 6, Requirement 12). *Alternatives considered*: a Frontend requirement for a member panel on `/boards/[id]` (steering `product.md` F-11 lists a member panel); not chosen for V1 scope. *Source*: user approval of the recommended default (V8).
- **OD-15 (Comments and Notifications of a soft-deleted Card)**: A Card soft delete never physically deletes its Comments. The Card and its Comments, Notifications, and activity are hidden from Board, Search, My Tasks, and Analytics reads, and Card-ID routes return 404. Physical cascade happens only for the approved hard deletes (Column delete, Board delete). Guideline `database.md` DB-06 and `backend.md` BE-15 were synchronised with this rule in the V7 round. *Source*: contract finding 20.
- **OD-16 (Guest mode omits the JWT)**: The Frontend on `/boards/[id]?invite=<token>` runs in Guest_Mode and sends only `X-Invite-Token`, no `Authorization` header (Requirement 3 criterion 8, Requirement 21 criteria 11, 16, and 17). Cost: a signed-in Member who opens an invite link sees a read-only view. *Alternatives considered*: send both and let the API resolve (steps 4 and 7 of the Access Resolution Table). *Source*: user approval of the recommended default (V8).
- **OD-17 (Generic denial body text)**: The Generic_Denial_Body is `{"error": "Not found or access denied"}` (Requirement 1 criteria 1, 2, and 5, Requirement 2 criterion 7, Requirement 8, Requirement 20, Frontend 403 and 404 handling). `backend.md` BE-10 carries the same text. *Alternatives considered*: separate 403 and 404 texts. *Source*: user approval of the recommended default (V8).
- **OD-18 (400 string format)**: A 400 validation error is one string: failing fields sorted alphabetically, each entry `<field>: <messages joined by ", ">`, entries joined by " | " (Requirement 20 criteria 1 and 13, Requirement 22 criterion 4). *Alternatives considered*: a nested object with a separate `details` property (future work, needs its own approval). *Source*: user approval of the recommended default (V8).
- **OD-19 (Derived `card_id` and `board_id` in Notification items)**: Notification items expose `card_id` and `board_id` as read-only values derived through the Comment (Comment, Card, Column, Board), not stored (Requirement 9 criterion 7 and Validation Rules, `NotificationBell`). *Alternatives considered*: omit them; not chosen because the Frontend needs the Card and Board to link a Notification. *Source*: user approval of the recommended default (V8).
- **OD-20 (Guideline location)**: `backend.md`, `database.md`, and `frontend.md` stay in `/guidelines` only and are not copied to `.kiro/steering`. *Alternatives considered*: also place them under `.kiro/steering`, which requires keeping the copies identical. *Source*: user approval of the recommended default (V8).

### Open Decisions

None. All decisions listed above are approved or resolved (V8). A new open decision is added here with question, impact, options, recommended default, and reason unresolved.

### Assumptions

- **A-01**: `GET /api/cards` is not paginated in V2.
- **A-02**: Analytics date range defaults to the last 7 days ending today (UTC) only when neither `start_date` nor `end_date` is provided; providing only one of them is invalid (HTTP 400, both-or-neither rule). The range is limited to 366 days.
- **A-03**: Drag-and-drop on touch devices, Column reorder user interface, and Board duplicate names are not constrained: duplicate Board names are allowed; no Column reorder user interface is required in V2.
- **A-04**: Role names stored as `admin` and `member`.
- **A-05**: Editing a Comment creates Notifications only for newly mentioned members who have no Notification for that Comment; removing a Mention does not delete an existing Notification.

## Requirements

### Requirement 1: Board Access Isolation

**Priority:** Retained
**Source:** Both
**User Story:** As a Team member, I want my Board's data visible only to my Team, so that confidential work stays private.

#### Acceptance Criteria

1. IF an authenticated user who is not a member of the Team of an existing Board, Column, Card, or Comment requests data of that resource by its ID, THEN THE Authorization_Service SHALL reject the request with HTTP status 403 and the Generic_Denial_Body `{"error": "Not found or access denied"}`, except where the Access Resolution Table (Requirement 3) resolves a request to a Guest_Read_Endpoint that carries an `X-Invite-Token` under its steps 6 to 8.
2. IF a request names in its URL path the ID of a Board, Column, Card, or Comment that does not exist, or the ID of a soft-deleted Card, THEN THE API SHALL respond with HTTP status 404 and the Generic_Denial_Body, before any Team membership or role evaluation (OD-02).
3. THE Authorization_Service SHALL evaluate Team membership against the Database on every API request that reads or modifies Board data.
4. FOR ALL Boards B and users U who are not members of B's Team and hold no valid Invite_Link for B, THE API SHALL return no Column, Card, Comment, Activity_Event, analytics, or Notification data of B to U, including in search results and My Tasks results.
5. WHEN a user is removed from a Team, THE Authorization_Service SHALL reject that user's subsequent requests to the Team's Boards with HTTP status 403 and the Generic_Denial_Body, including requests that carry an unexpired JWT issued before the removal.
6. IF a path parameter that must be a UUID is not a valid UUID, THEN THE API SHALL respond with HTTP status 400 and a non-empty `error` string.
7. WHEN a request names a Board-scoped ID in its URL path, THE API SHALL evaluate the request in this order: (1) the JWT on a JWT-protected route (401 under Requirement 13 criterion 13) or the Authorization header and token presence on a Guest_Read_Endpoint (steps 1 and 2 of the Access Resolution Table); (2) existence (404 under criterion 2); (3) Team membership and role (403 under criteria 1 and 5 and Requirement 2), and SHALL respond 403, never 404, to a requester who lacks permission on an existing resource (OD-02).

#### Validation Rules

- 401: no JWT, or a malformed or expired JWT, on a JWT-protected route (Requirement 13 criterion 13). A valid JWT without Team access to an existing resource is 403, never 401.
- 404 body for a Board, Column, Card, or Comment ID in the URL path that does not exist, and for a soft-deleted Card: the Generic_Denial_Body `{"error": "Not found or access denied"}` (OD-02, OD-17).
- 403 body for an existing Board, Column, Card, or Comment whose Board the requester cannot access: the Generic_Denial_Body. A Team member who lacks the required role keeps a specific 403 message (for example `{"error": "Admin access required"}`, Requirement 2).
- Other 404 responses: unknown routes, an invalid or revoked Invite_Link token on a Guest_Read_Endpoint, and an `invite_id` in the path of `DELETE /api/boards/<id>/invite-links/<invite_id>` that does not exist or is not bound to the Board in the path (`{"error": "Not found"}`); an unregistered email when an Admin adds a Team member (`{"error": "User not found"}`); a Notification not owned by the requester (`{"error": "Not found"}`). A Board-scoped ID in a request body (for example `column_id`) that does not exist is a 400 validation failure (Requirement 7 criterion 4).
- The status codes 403 and 404 still differ, so the shared body text does not hide whether an ID exists; the IDs are random UUIDs (OD-02).

#### Related Areas

Authorization_Service, all Blueprints, steering PR-03.

Routes/Pages: cross-cutting; all routes under the stated Blueprints, for example `GET /api/boards/<id>`, `PATCH /api/columns/<id>`, `PATCH /api/cards/<id>`, `PATCH /api/comments/<id>`, `DELETE /api/boards/<id>/invite-links/<invite_id>`; page `/boards/[id]`.

### Requirement 2: Role-Based Permission Enforcement

**Priority:** Retained
**Source:** Both
**User Story:** As a Team Admin, I want each role limited to its permitted actions, so that Guests and Members cannot change what only Admins may change.

#### Acceptance Criteria

1. THE Authorization_Service SHALL enforce permissions on the API for every request, independent of the controls shown in the Frontend.
2. IF a Guest sends a request that creates, edits, deletes, or moves any Board, Column, Card, or Comment, THEN THE API SHALL reject the request with HTTP status 403 and leave stored data unchanged; a request that carries no valid JWT is rejected with HTTP status 401 under Requirement 13 criterion 8 (Requirement 3, Validation Rules).
3. IF a Member sends a request to rename or delete a Board, to manage Team members, to manage Invite_Links, or to view analytics, THEN THE API SHALL reject the request with HTTP status 403 and leave stored data unchanged.
4. WHEN a Member sends a valid request to create a Column, Card, or Comment, to edit a Card, to assign a Card, or to move a Card, THE API SHALL perform the requested action.
5. IF a Member sends a request to rename, reorder, delete, or change `is_done` of a Column, THEN THE API SHALL reject the request with HTTP status 403 and leave stored data unchanged.
6. WHERE the requester is an Admin, THE API SHALL allow every action permitted to a Member plus Column rename, reorder, delete, and `is_done` changes, Board rename and delete, Team member management, Invite_Link management, deletion of any Card, and analytics viewing.
7. IF an Admin sends a request that names the ID of an existing Board, Column, Card, or Comment that belongs to a Team to which that Admin does not belong, THEN THE API SHALL reject the request with HTTP status 403 and the Generic_Denial_Body; an ID that does not exist, or the ID of a soft-deleted Card, returns 404 with the Generic_Denial_Body under Requirement 1 criterion 2 before this check (OD-02).
8. IF a user other than the author sends a request to edit or delete a Comment, THEN THE API SHALL reject the request with HTTP status 403, including when the user is an Admin.
9. IF a Member sends a request to delete a Card that another user created, THEN THE API SHALL reject the request with HTTP status 403 and leave stored data unchanged.
10. FOR ALL actions A and roles R, THE Authorization_Service SHALL return the same allow or deny decision for repeated evaluations of A by R on unchanged data (determinism).
11. FOR ALL actions A on the same target, if A is permitted to a Guest then A SHALL be permitted to a Member of the Team, and if A is permitted to a Member then A SHALL be permitted to an Admin of the Team (role monotonicity).

#### Validation Rules

| Action | Admin | Member | Guest | Non-member |
|---|---|---|---|---|
| View Board, Columns, Cards, Comments | allow | allow | allow (read-only) | 403 |
| Create Board in own Team | allow | 403 | not applicable | 403 |
| Rename or delete Board | allow | 403 | 403 | 403 |
| Create Column | allow | allow | 403 | 403 |
| Rename, reorder, delete Column | allow | 403 | 403 | 403 |
| Create, edit, assign, move Card | allow | allow | 403 | 403 |
| Delete Card | any Card | own Cards only | 403 | 403 |
| Add Comment | allow | allow | 403 | 403 |
| Edit or delete Comment | author only | author only | 403 | 403 |
| Manage Team members and Invite_Links | allow | 403 | 403 | 403 |
| View analytics | allow | 403 | 403 | 403 |

- The table applies to resources that exist; a Board-scoped ID that does not exist returns 404 with the Generic_Denial_Body before the table is evaluated (Requirement 1 criteria 2 and 7).
- A Team member who lacks the role for an action keeps a specific 403 message (for example `{"error": "Admin access required"}` for Admin-only actions); a user without Team access gets the Generic_Denial_Body (Requirement 1 criterion 1).
- A Guest has no JWT or holds only the Invite_Link token: a Guest write request without a valid JWT is answered 401, and with a valid JWT of a non-member 403 (Requirement 3 criterion 14).

#### Related Areas

Authorization_Service, steering PR-03 (differences flagged in OD-01 and OD-08).

Routes/Pages: cross-cutting; all routes under the stated Blueprints (boards, columns, cards, comments, analytics), for example `PATCH /api/boards/<id>`, `DELETE /api/columns/<id>`, `DELETE /api/cards/<id>`, `PATCH /api/comments/<id>`, `GET /api/boards/<id>/analytics`; page `/boards/[id]`.

### Requirement 3: Guest Access via Invite Link

**Priority:** Retained
**Source:** Existing Sevy
**User Story:** As an Admin, I want to share a Board through an invite link, so that outsiders can view progress without joining the Team.

#### Acceptance Criteria

1. WHEN an Admin sends `POST /api/boards/<id>/invite-links` with an empty body or `{}`, THE API SHALL create an Invite_Link bound to that Board and return HTTP status 201 with `id`, `board_id`, `token`, and `created_at`.
2. THE API SHALL generate each Invite_Link token from a cryptographically secure random source with at least 128 bits of entropy.
3. WHEN a request to a Guest_Read_Endpoint carries a valid, non-revoked `X-Invite-Token` bound to the Board of the requested resource and carries either no `Authorization` header or a valid JWT of a user who is not a Team member of that Board's Team, THE API SHALL return HTTP status 200 with the data in read-only form with the Guest role (step 7).
4. IF a request to a Guest_Read_Endpoint carries an `X-Invite-Token` that is invalid, revoked, or malformed and step 4 of the Access Resolution Table does not match, THEN THE API SHALL reject the request with HTTP status 404 and the body `{"error": "Not found"}` (step 6).
5. IF a request to a Guest_Read_Endpoint carries a valid `X-Invite-Token` bound to a Board other than the Board of the requested resource and step 4 of the Access Resolution Table does not match, THEN THE API SHALL reject the request with HTTP status 403 and the Generic_Denial_Body (step 8).
6. WHEN an Admin sends `DELETE /api/boards/<id>/invite-links/<invite_id>`, THE API SHALL revoke the Invite_Link and return HTTP status 200 with `{"data": {"id": "<uuid>"}}`.
7. WHEN an Invite_Link is revoked, THE API SHALL treat its token as revoked for every subsequent request, so that criterion 4 applies to each later request to a Guest_Read_Endpoint that uses the token and for which steps 1 to 5 of the Access Resolution Table do not match.
8. WHEN a user opens `/boards/<id>?invite=<token>`, THE Frontend SHALL display the Board's Columns, Cards, and Comments in Guest_Mode with no create, edit, delete, assign, or drag controls.
9. WHEN a request to a Guest_Read_Endpoint carries a valid, unexpired JWT of a user who is a Team member of the Team that owns the Board of the requested resource, THE API SHALL apply the Team role and permissions of that user and SHALL ignore any `X-Invite-Token`, whether the token is valid, invalid, revoked, malformed, or bound to another Board, and SHALL return no 404 and no 403 because of the token (step 4).
10. IF a request to a Guest_Read_Endpoint carries a valid, unexpired JWT of a user who is not a Team member of the Team that owns the Board of the requested resource and carries no `X-Invite-Token`, THEN THE API SHALL reject the request with HTTP status 403 and the Generic_Denial_Body (step 5).
11. IF a request to a Guest_Read_Endpoint carries no `Authorization` header and no `X-Invite-Token`, THEN THE API SHALL reject the request with HTTP status 401 and the standard error envelope (step 2).
12. THE Authorization_Service SHALL resolve every request to a Guest_Read_Endpoint by evaluating the eight steps of the Access Resolution Table in order and applying the first matching step, and the table SHALL take precedence over Requirements 1 (criteria 1 and 5), 2, and 13 for such a request; a request that names a Board or Card that does not exist, or a soft-deleted Card, is answered with 404 and the Generic_Denial_Body (step 3) after steps 1 and 2 and before steps 4 to 8.
13. THE API SHALL evaluate `X-Invite-Token` only on the two Guest_Read_Endpoints and SHALL ignore it on every other endpoint.
14. IF a request that carries only a valid `X-Invite-Token` and no JWT names any endpoint other than the two Guest_Read_Endpoints, THEN THE API SHALL respond with HTTP status 401 on a JWT-protected route, so that a Guest reaches no Search, Notifications, Analytics, My Tasks, Profile, or write endpoint.
15. THE API SHALL apply a purpose-specific access check to the two Guest_Read_Endpoints, which accepts either a Team member's JWT or a valid Invite_Link token and evaluates the Access Resolution Table, and SHALL apply the standard JWT-required check to every other endpoint except `POST /api/auth/register`, `POST /api/auth/login`, and `GET /api/health`.

#### Validation Rules

Principle: an invite token can only add access, never reduce it. A JWT decides access when its user is a Team member of the Team that owns the requested Board; otherwise a valid invite token bound to that Board applies. A malformed, invalid, or expired JWT never falls back to Guest access: the request is answered 401 even when a valid token is present.

Access Resolution Table (evaluate in this order; the first matching step applies). "Board of the requested resource" is the requested Board, or the Board that owns the requested Card.

| Step | Condition | Result |
|---|---|---|
| 1 | An `Authorization` header is present and its JWT is invalid, malformed, or expired (any `X-Invite-Token` state) | 401, standard error envelope |
| 2 | No `Authorization` header and no `X-Invite-Token` | 401, standard error envelope |
| 3 | The Board (or the Board of the Card) does not exist, or the Card is soft-deleted | 404 Generic_Denial_Body |
| 4 | Valid, unexpired JWT and the user is a Team member of the Team that owns the Board (any `X-Invite-Token` state, ignored) | The user's Team role and permissions apply |
| 5 | Valid, unexpired JWT, the user is not a Team member, and no `X-Invite-Token` | 403 Generic_Denial_Body |
| 6 | `X-Invite-Token` present and invalid, revoked, or malformed (reached only when step 4 does not match) | 404 `{"error": "Not found"}` |
| 7 | Valid, non-revoked `X-Invite-Token` bound to the Board of the requested resource, with no `Authorization` header or with a valid JWT of a non-member | 200, Guest read-only access |
| 8 | Valid `X-Invite-Token` bound to a different Board, with no `Authorization` header or with a valid JWT of a non-member | 403 Generic_Denial_Body |

- Every combination of Authorization header, JWT state, resource existence, membership, and token state matches exactly one step. An empty `X-Invite-Token` header is a present token and is invalid (step 6).
- The Guest_Read_Endpoints are `GET /api/boards/<id>` and `GET /api/cards/<id>/comments`. A Guest cannot create, edit, delete, or move anything, and cannot reach Search, Notifications, Analytics, My Tasks, or Profile (criterion 14, Requirement 2 criterion 2).
- Frontend: the page `/boards/<id>?invite=<token>` runs in Guest_Mode: the API_Client sends only `X-Invite-Token` and no `Authorization` header, only on the two Guest_Read_Endpoints, and no authenticated session is created (Requirement 21 criterion 17). A signed-in Member who opens an invite link therefore sees a read-only view.
- For `DELETE /api/boards/<id>/invite-links/<invite_id>`, a Board that does not exist returns 404 with the Generic_Denial_Body, and an `invite_id` that does not exist or is not bound to the Board in the path returns 404 `{"error": "Not found"}`; both are evaluated before the Admin check (Requirement 1 criteria 2 and 7).
- Every 403 that this document assigns to a Guest on an endpoint other than the Guest_Read_Endpoints applies to a request with a valid JWT; a request with no valid JWT receives 401 (Requirement 13 criterion 8).
- Invite_Link request fields: create takes an empty body or `{}` and rejects any unknown field with 400; revoke takes no body.
- Creating and revoking Invite_Links is API-only in V1: no Frontend screen exists for it, and the only Frontend criterion for Invite_Links is the Guest view (criterion 8) (OD-14).

#### Related Areas

boards Blueprint, comments Blueprint, Board Detail page, Authorization_Service.

Routes/Pages: `POST /api/boards/<id>/invite-links`, `DELETE /api/boards/<id>/invite-links/<invite_id>`, `GET /api/boards/<id>`, `GET /api/cards/<id>/comments`; page `/boards/[id]` (with the `invite` query parameter).

### Requirement 4: Board Management

**Priority:** Mandatory
**Source:** Both
**User Story:** As a Member, I want to work on Boards owned by my Team, so that the Team shares one workspace.

#### Acceptance Criteria

1. WHEN an Admin of a Team sends `POST /api/boards` with a `name` of 1 to 100 characters after trimming whitespace, THE API SHALL create a Board owned by that Team and return HTTP status 201 with the Board.
2. WHERE a `POST /api/boards` request body omits `team_id`, THE API SHALL use the personal Team of the requester (the Team with `is_personal` true and `owner_id` equal to the requester) as the owner; this rule applies to `POST /api/boards` only and to no other endpoint.
3. IF the submitted Board `name` is empty, whitespace-only, or longer than 100 characters, or the body contains an undefined field, THEN THE API SHALL reject the request with HTTP status 400 and a validation error message.
4. IF the requester is not an Admin of the Team named by `team_id`, THEN THE API SHALL reject the request with HTTP status 403.
5. WHEN a user sends `GET /api/boards`, THE API SHALL return HTTP status 200 with only the Boards owned by Teams to which that user belongs, ordered by `created_at` descending.
6. WHEN a Member or Admin sends `GET /api/boards/<id>`, THE API SHALL return HTTP status 200 with the Board, its Columns ordered by `order` ascending, and for each Column its non-deleted Cards ordered by `order` ascending, each Card with the keys defined in the Validation Rules of this Requirement.
7. WHEN an Admin sends `PATCH /api/boards/<id>` with a valid `name`, THE API SHALL persist the name and return HTTP status 200 with the updated Board.
8. IF a `PATCH /api/boards/<id>` body contains a field other than `name`, THEN THE API SHALL reject the request with HTTP status 400.
9. WHEN an Admin sends `DELETE /api/boards/<id>`, THE API SHALL delete the Board together with all of its Columns, Cards, Comments, Notifications referencing its Comments, Invite_Links, and Activity_Events, and return HTTP status 200 with `{"data": {"id": "<uuid>"}}`.
10. WHEN a Member opens a Board, THE Frontend SHALL display the Board's Columns in `order` ascending, each containing its Cards in `order` ascending.

#### Validation Rules

- Board `name`: 1 to 100 characters after trimming. Duplicate names are allowed (A-03).
- Board detail response (`GET /api/boards/<id>`): the Board with `id`, `name`, `team_id`, `created_at`, and `columns` **[Proposed]**; each Column with `id`, `name`, `order`, `is_done`, and `cards` **[Proposed]**.
- Nested Card shape (all keys snake_case): `id`, `title`, `description`, `order`, `column_id`, `assignee_id`, `assignee` (an object with `id`, `name`, `username`, or null when the Card has no Assignee), `created_by_id`, `completed_at`, `created_at`, `updated_at` **[Proposed]**; the sources do not define the keys. The Card list item of Requirement 10 is a different shape and is not used here.

#### Related Areas

boards Blueprint, Dashboard page, Board Detail page.

Routes/Pages: `POST /api/boards`, `GET /api/boards`, `GET /api/boards/<id>`, `PATCH /api/boards/<id>`, `DELETE /api/boards/<id>`; pages `/`, `/boards/[id]`.

### Requirement 5: Column Management and FLOAT Ordering

**Priority:** Mandatory
**Source:** Both
**User Story:** As a Member, I want to manage ordered Columns on a Board, so that the workflow stages match how my Team works.

#### Acceptance Criteria

1. WHEN a Member or Admin sends `POST /api/boards/<id>/columns` with a `name` of 1 to 100 characters and an optional boolean `is_done` defaulting to false, THE API SHALL create the Column and return HTTP status 201.
2. WHEN a Column is created in a Board that has no Columns, THE API SHALL set its `order` to 1024.0.
3. WHEN a Column is created in a Board that has Columns, THE API SHALL set its `order` to the largest existing Column `order` plus 1024.0.
4. IF a submitted Column name is empty, whitespace-only, or longer than 100 characters, or the body contains an undefined field, THEN THE API SHALL reject the request with HTTP status 400 and a validation error message.
5. WHEN an Admin sends `PATCH /api/columns/<id>` with `name` or `is_done`, THE API SHALL persist the change and return HTTP status 200 with the updated Column.
6. WHEN an Admin sends `PATCH /api/boards/<id>/columns/reorder` with `{"column_id": "<uuid>", "order": <number>}`, THE API SHALL store the submitted `order` on that Column and return HTTP status 200 with `{"data": {"column": {...}, "rebalanced": <boolean>}}`.
7. IF the reorder `order` is not a number greater than 0, or `column_id` is not a UUID of a Column on the Board in the path, THEN THE API SHALL reject the request with HTTP status 400.
8. IF the reorder `order` equals the `order` of another Column of the same Board, THEN THE API SHALL reject the request with HTTP status 409 and the standard error envelope `{"error": "<non-empty string>"}` only, with no suggested `order`, range, or other remediation hint, and leave stored data unchanged; the client resolves the conflict by computing a new `order`.
9. IF after storing an `order` the difference between any two adjacent Column `order` values of the Board is less than MIN_GAP, THEN THE API SHALL Rebalance the Columns of that Board and return `rebalanced` true.
10. WHEN an Admin sends `DELETE /api/columns/<id>`, THE API SHALL delete the Column together with its Cards and their Comments and return HTTP status 200 with `{"data": {"id": "<uuid>"}}`.
11. WHEN a Column is deleted, THE API SHALL leave the `order` values of the remaining Columns unchanged.
12. THE API SHALL return Columns sorted by `order` ascending in every response.
13. FOR ALL Boards, THE API SHALL keep Column `order` values positive, unique, and strictly increasing in the returned sequence after any create, reorder, or delete operation (invariant).
14. IF a Member sends a request to rename, reorder, or delete a Column, THEN THE API SHALL reject the request with HTTP status 403.

#### Validation Rules

- `order` ordering rules for any parent (shared with Requirement 6 and Requirement 7): first item 1024.0; append = last `order` + 1024.0; insert at head = first `order` / 2; insert between = (previous `order` + next `order`) / 2; ORDER_STEP = 1024.0; MIN_GAP = 1e-6.
- Column `name`: 1 to 100 characters after trimming.

#### Related Areas

columns Blueprint, Board Detail page, steering TC-11, OD-01.

Routes/Pages: `POST /api/boards/<id>/columns`, `PATCH /api/columns/<id>`, `DELETE /api/columns/<id>`, `PATCH /api/boards/<id>/columns/reorder`; page `/boards/[id]`.

### Requirement 6: Card Management

**Priority:** Mandatory
**Source:** Both
**User Story:** As a Member, I want to create and edit Cards, so that I can record tasks for my Team.

#### Acceptance Criteria

1. WHEN a Member or Admin sends `POST /api/columns/<id>/cards` with a `title` of 1 to 200 characters, an optional `description` of up to 5000 characters, and an optional `assignee_id`, THE API SHALL create the Card at the end of that Column and return HTTP status 201 with the Card.
2. WHEN a Card is created in a Column that has no non-deleted Cards, THE API SHALL set its `order` to 1024.0; otherwise THE API SHALL set its `order` to the largest non-deleted Card `order` in that Column plus 1024.0.
3. IF a submitted Card `title` is empty, whitespace-only, or longer than 200 characters, or `description` is longer than 5000 characters, or the body contains an undefined field, THEN THE API SHALL reject the request with HTTP status 400 and a validation error message.
4. WHEN a Member or Admin sends `PATCH /api/cards/<id>` with `title`, `description`, or `assignee_id`, THE API SHALL persist the change, set `updated_at` to the current UTC time, and return HTTP status 200 with the updated Card.
5. IF a `PATCH /api/cards/<id>` body contains `column_id`, `order`, `deleted_at`, `completed_at`, or any other undefined field, THEN THE API SHALL reject the request with HTTP status 400 and leave stored data unchanged.
6. WHEN an authorized user sends `DELETE /api/cards/<id>`, THE API SHALL set `deleted_at` to the current UTC time and return HTTP status 200 with `{"data": {"id": "<uuid>"}}`.
7. WHEN a Card is soft-deleted, THE API SHALL omit the Card from every GET response, search result, My Tasks result, and analytics count, and SHALL answer a direct request by Card ID with 404 and the Generic_Denial_Body as for a non-existent Card (criterion 14).
8. THE Database SHALL store for each Card a UUID primary key, `title`, `description`, `column_id`, `order` as a non-null Float, `assignee_id` (nullable), `created_by_id`, `completed_at` (nullable), `created_at`, `updated_at`, and `deleted_at` (nullable).
9. THE API SHALL apply the `order` rules of Requirement 5 (Validation Rules) to non-deleted Cards within each Column.
10. FOR ALL Columns, THE API SHALL keep non-deleted Card `order` values positive, unique, and strictly increasing in the returned sequence after any create, move, or delete operation (invariant).
11. FOR ALL Cards, THE API SHALL associate the Card with exactly one Column and, through that Column, exactly one Board (invariant).
12. FOR ALL valid Card inputs, creating a Card and then retrieving it SHALL return a Card with the same `title`, `description`, and `assignee_id` (round-trip property).
13. WHEN a Card is created, edited, or successfully soft-deleted, THE API SHALL record exactly one Activity_Event of type `card_created`, `card_updated`, or `card_deleted` respectively, with the acting user and a UTC timestamp, and SHALL record no Activity_Event for a request that is rejected.
14. IF a request to a Card-ID route (`PATCH /api/cards/<id>`, `DELETE /api/cards/<id>`, `PATCH /api/cards/<id>/position`, `POST /api/cards/<id>/comments`, or `GET /api/cards/<id>/comments`) names the ID of a soft-deleted Card, THEN THE API SHALL respond with HTTP status 404 and the Generic_Denial_Body, evaluated before any Team membership or role check (for `GET /api/cards/<id>/comments`, after steps 1 and 2 of the Access Resolution Table), and leave stored data unchanged (OD-02, Requirement 1 criterion 2). The API has no `GET /api/cards/<id>` route, so this rule applies to every Card-ID route.
15. IF `assignee_id` in `POST /api/columns/<id>/cards` or `PATCH /api/cards/<id>` references a UUID that is not a member of the Card's Team, including a UUID that is not an existing user, THEN THE API SHALL respond with HTTP status 400 and the body `{"error": "Assignee must be a Team member"}` and leave stored data unchanged (Requirement 18 criterion 2).
16. WHEN a Card is soft-deleted, THE API SHALL keep the rows of the Card's Comments (a Card soft delete SHALL NOT physically delete Comments), SHALL hide the Card and its Comments, Notifications, and Activity_Events from Board, Search, My Tasks, and Analytics reads, and SHALL answer Card-ID routes with 404 under criterion 14; physical cascade SHALL occur only for the approved hard deletes (Column delete in Requirement 5 criterion 10, Board delete in Requirement 4 criterion 9) (OD-15).

#### Validation Rules

- Card `title`: 1 to 200 characters after trimming. `description`: 0 to 5000 characters.
- Delete permission: Admin any Card; Member only Cards where `created_by_id` equals the Member (OD-08).

#### Related Areas

cards Blueprint, Board Detail page, Card_Detail_Modal.

Routes/Pages: `POST /api/columns/<id>/cards`, `PATCH /api/cards/<id>`, `DELETE /api/cards/<id>`, `PATCH /api/cards/<id>/position`, `POST /api/cards/<id>/comments`, `GET /api/cards/<id>/comments`, `GET /api/boards/<id>`, `GET /api/cards`; page `/boards/[id]`.

### Requirement 7: Drag-and-Drop Card Movement

**Priority:** Mandatory
**Source:** Both
**User Story:** As a Member, I want to drag Cards between and within Columns, so that the Board reflects work progress and the order stays as I left it.

#### Acceptance Criteria

1. WHEN a Member or Admin sends `PATCH /api/cards/<id>/position` with a valid `column_id` and `order`, THE API SHALL move the Card to that Column with that `order` and return HTTP status 200 with `{"data": {"card": {...}, "rebalanced": <boolean>}}`.
2. THE API SHALL validate the body with `CardPositionSchema`, which requires `column_id` as a UUID and `order` as a number greater than 0 and rejects undefined fields.
3. IF the body is not valid under `CardPositionSchema`, THEN THE API SHALL reject the request with HTTP status 400 and leave stored data unchanged.
4. IF `column_id` does not reference an existing Column, THEN THE API SHALL reject the request with HTTP status 400 and leave stored data unchanged.
5. IF `column_id` references a Column on a different Board than the Card, THEN THE API SHALL reject the request with HTTP status 400 and leave stored data unchanged.
6. IF `order` equals the `order` of another non-deleted Card in the target Column, THEN THE API SHALL reject the request with HTTP status 409 and the standard error envelope `{"error": "<non-empty string>"}` only, with no suggested `order`, range, or other remediation hint, and leave stored data unchanged; the client resolves the conflict by computing a new `order`.
7. WHEN a Card is moved, THE API SHALL commit the new `column_id` and `order` to the Database before returning the success response.
8. IF after a move the difference between two adjacent Card `order` values in the target Column is less than MIN_GAP, THEN THE API SHALL Rebalance that Column and return `rebalanced` true.
9. WHEN a Card changes Column or `order`, THE API SHALL record an Activity_Event of type `card_moved` with the acting user.
10. WHEN a Card moves between an `is_done` Column and a non-done Column, THE API SHALL update `completed_at` as defined in Requirement 24.
11. FOR ALL Boards and valid moves, THE API SHALL keep the total number of non-deleted Cards on the Board unchanged by the move (invariant).
12. FOR ALL Cards moved from Column X to Column Y, moving the Card back to Column X with its original `order` SHALL restore the original sequence of Cards in both Columns (round-trip property).
13. FOR ALL moves, sending the same move request twice SHALL produce the same Board state as sending it once (idempotence).
14. WHEN two users move Cards in the same Column at the same time, THE API SHALL serialize the moves in Database transactions with row locks so that the resulting `order` values in each affected Column are unique and strictly increasing.
15. WHEN a Member reloads the Board after a Card move, THE Frontend SHALL display the Cards in the same Columns and sequence as after the move (order persistence).
16. WHEN a Member drops a Card, THE Frontend SHALL compute the new `order` from the neighbors in the target Column using the rules in Requirement 5 (Validation Rules).
17. WHEN a Member drops a Card, THE Frontend SHALL update the local Card state before the API responds (optimistic update).
18. IF the API rejects or fails a move request, THEN THE Frontend SHALL restore the Card to its previous Column and `order` and show an error Toast.
19. WHEN the move response contains `rebalanced` true, THE Frontend SHALL reload the Board data from the API.
20. THE Frontend SHALL implement Card dragging with the native HTML5 Drag and Drop events (`draggable`, `dragstart`, `dragover`, `drop`).

#### Validation Rules

- `column_id`: UUID. `order`: number, 0 < order.
- Moves by Guests or non-members: HTTP 403 (Requirements 1 and 2). A path Card ID that does not exist or names a soft-deleted Card: HTTP 404 with the Generic_Denial_Body (Requirement 1 criterion 2); a `column_id` in the body that does not exist: HTTP 400 (criterion 4).

#### Related Areas

cards Blueprint, Kanban_Board, drag-and-drop hook, steering TC-11 and TC-14.

Routes/Pages: `PATCH /api/cards/<id>/position`, `GET /api/boards/<id>`; page `/boards/[id]`.

### Requirement 8: Threaded Comments

**Priority:** Mandatory
**Source:** Both
**User Story:** As a Member, I want to discuss a Card in threaded Comments, so that decisions stay attached to the work.

#### Acceptance Criteria

1. WHEN a Member or Admin sends `POST /api/cards/<id>/comments` with `content` of 1 to 2000 characters, THE API SHALL store the Comment with the author, `created_at`, and `updated_at`, and return HTTP status 201 with the Comment.
2. WHEN the request body includes `parent_id` of an existing Comment, THE API SHALL store the Comment as a reply to that parent.
3. IF `content` is missing, empty, whitespace-only, or longer than 2000 characters, THEN THE API SHALL reject the request with HTTP status 400 and a validation error message.
4. IF `parent_id` references a Comment that belongs to a different Card, THEN THE API SHALL reject the request with HTTP status 400.
5. IF a request to any Comment endpoint other than `GET /api/cards/<id>/comments` carries no valid JWT, THEN THE API SHALL reject the request with HTTP status 401; `GET /api/cards/<id>/comments` is a Guest_Read_Endpoint decided by the Access Resolution Table (Requirement 3), so a Member or Admin read needs a valid JWT and Team access (401 without a valid JWT in steps 1 and 2, 403 without Team access in step 5, 404 for a non-existent or soft-deleted Card in step 3) and a Guest reads only through a valid Invite_Link bound to the Board of the Card (step 7).
6. IF a user who is not a member of the Card's Team sends `POST /api/cards/<id>/comments`, THEN THE API SHALL reject the request with HTTP status 403 and the Generic_Denial_Body.
7. WHEN a Member or Admin with Team access, or a Guest with a valid Invite_Link bound to the Board of the Card, sends `GET /api/cards/<id>/comments`, THE API SHALL return HTTP status 200 with the Comments of the Card as a flat list ordered by `created_at` ascending, each with `id`, `card_id`, `parent_id`, `author_id`, `content`, `is_deleted`, `created_at`, and `updated_at`, omitting a deleted Comment that has no live replies (criterion 10), where `is_deleted` is derived from `deleted_at` and is not stored.
8. WHEN the author sends `PATCH /api/comments/<id>` with valid `content`, THE API SHALL persist the content, set `updated_at` to the current UTC time, and return HTTP status 200 with the updated Comment.
9. IF a user other than the author sends `PATCH /api/comments/<id>` or `DELETE /api/comments/<id>`, THEN THE API SHALL reject the request with HTTP status 403 and leave stored data unchanged.
10. WHEN the author sends `DELETE /api/comments/<id>` for a Comment that has no live replies, THE API SHALL set `deleted_at` on the Comment (the row is kept), omit the Comment from every later read, and return HTTP status 200 with `{"data": {"id": "<uuid>"}}`.
11. WHEN the author sends `DELETE /api/comments/<id>` for a Comment that has live replies, THE API SHALL set `deleted_at` on the Comment (the row is kept), keep its replies, return the Comment in later reads as a Tombstone with `is_deleted` true and empty `content`, and return HTTP status 200 with `{"data": {"id": "<uuid>"}}`.
12. WHEN a Comment is created, THE API SHALL record an Activity_Event of type `comment_added` with the author.
13. WHEN a Member opens a Card, THE Card_Detail_Modal SHALL display its Comments as threads, with each reply under its parent Comment, ordered by `created_at`.
14. WHEN a Comment has `updated_at` later than `created_at`, THE Card_Detail_Modal SHALL display an "edited" indicator on that Comment.
15. WHEN a Member submits the comment form in the Card_Detail_Modal, THE Frontend SHALL send `POST /api/cards/<id>/comments` and display the new Comment in the thread without a full page reload.
16. WHEN the author edits a Comment in the Card_Detail_Modal, THE Frontend SHALL send `PATCH /api/comments/<id>` and display the updated content.
17. FOR ALL valid Comment inputs, creating a Comment and then retrieving it SHALL return a Comment with the same `content`, `author_id`, and `parent_id` (round-trip property).
18. IF a request to a Comment endpoint names in its URL path a Card ID or Comment ID that does not exist, or the ID of a soft-deleted Card, THEN THE API SHALL respond with HTTP status 404 and the Generic_Denial_Body, before any Team membership or author check (Requirement 1 criterion 2, OD-02).
19. THE API SHALL accept `POST /api/cards/<id>/comments`, `PATCH /api/comments/<id>`, and `DELETE /api/comments/<id>` only from Team members under Requirement 2, so that a Guest cannot create, edit, or delete a Comment.

#### Validation Rules

- Create request fields: `content` (required) and `parent_id` (optional UUID); unknown fields are rejected with 400.
- `content`: 1 to 2000 characters after trimming. `parent_id`: optional UUID.
- Tombstone rule: `deleted_at` is the only stored deletion marker; `is_deleted` is true when `deleted_at` is not null; it is returned and never stored. A deleted Comment with at least one live reply is returned with empty `content`; a deleted Comment with no live reply is omitted.
- Test-visible outcomes: 201 success, 400 missing content, 401 unauthenticated, 403 non-owner edit or delete, 403 non-member create.

#### Related Areas

comments Blueprint, Card_Detail_Modal, steering TC-17.

Routes/Pages: `POST /api/cards/<id>/comments`, `GET /api/cards/<id>/comments`, `PATCH /api/comments/<id>`, `DELETE /api/comments/<id>`; page `/boards/[id]` (Card_Detail_Modal).

### Requirement 9: Mention Notifications

**Priority:** Mandatory
**Source:** Both
**User Story:** As a Member, I want to be alerted when someone mentions me in a Comment, so that I can respond promptly.

#### Acceptance Criteria

1. WHEN a Comment containing `@username` is stored and the mentioned name, converted to lowercase, matches the lowercase `username` of a member of the Board's Team, THE Notification_Service SHALL create one unread Notification of type `mention` for that member.
2. WHEN a Comment mentions the same member more than once, THE Notification_Service SHALL create exactly one Notification for that member for that Comment (idempotence).
3. WHEN a Comment that contains a Mention of a username that does not match a member of the Board's Team has been stored, THE Notification_Service SHALL create no Notification for that Mention.
4. WHEN a member authors a Comment that mentions the same member, THE Notification_Service SHALL create no Notification for that member.
5. WHEN a Comment is edited to add a Mention of a member who has no Notification for that Comment, THE Notification_Service SHALL create one Notification for that member **[Proposed, A-05]**.
6. THE Notification_Service SHALL store for each Notification `id`, `recipient_id`, `type`, `message`, `comment_id`, `is_read` (default false), and `created_at`, and SHALL resolve the Card and Board of a Notification through its Comment.
7. WHEN a user sends `GET /api/notifications`, THE Notification_Service SHALL return HTTP status 200 with `data` containing exactly `items`, `page`, `per_page`, `total`, `total_pages`, and `unread_count`, where `items` holds only that user's Notifications ordered by `created_at` descending, `total_pages` is `ceil(total / per_page)` and 0 when `total` is 0, and `unread_count` counts all unread Notifications of the user and not only those of the page.
8. IF `page` is less than 1, or `per_page` is less than 1 or greater than 50, or either is not an integer, THEN THE API SHALL reject the request with HTTP status 400.
9. WHERE `page` and `per_page` are omitted, THE API SHALL use `page` 1 and `per_page` 10.
10. WHEN a user sends `PATCH /api/notifications/<id>/read` for the user's own Notification, THE Notification_Service SHALL set `is_read` to true and return HTTP status 200 with the Notification.
11. WHEN a user marks an already-read Notification as read, THE Notification_Service SHALL leave the state unchanged and return HTTP status 200 (idempotence).
12. IF a user sends `PATCH /api/notifications/<id>/read` for a Notification that belongs to another user or does not exist, THEN THE API SHALL respond with HTTP status 404 and the body `{"error": "Not found"}`.
13. FOR ALL Notifications, THE Notification_Service SHALL reference a Comment on a Board that the recipient belongs to (invariant); WHEN a Comment is deleted (`deleted_at` set, whether it becomes a Tombstone or is omitted) or the recipient is removed from the Team, THE Notification_Service SHALL delete the affected Notifications.
14. WHILE a user is signed in, THE Frontend SHALL poll `GET /api/notifications` every 30 seconds (30000 ms), clear the polling timer when the polling component unmounts, and send no polling request while the user is not signed in.
15. WHERE the `card_assigned` trigger is introduced in a later version, WHEN a Card is assigned to a user other than the acting user, THE Notification_Service SHALL create one unread Notification of type `card_assigned` for the Assignee **[Inactive; deferred, OD-04]**.
16. WHILE the unread Notification count is greater than 0, THE Notification_Bell SHALL display that count in a badge.
17. WHILE the unread Notification count is 0, THE Notification_Bell SHALL hide the badge.

#### Validation Rules

- Mention syntax: `@` followed by 3 to 30 letters, digits, or underscores; the mentioned name is converted to lowercase before it is matched against the stored lowercase `username` (OD-05).
- The recipient of a Notification is stored in the field `recipient_id`, and the Comment in `comment_id` (criterion 6). The Notification has no stored `user_id` and no stored `card_id`.
- Notification item shape (each element of `items`): `id`, `type`, `message`, `is_read`, `created_at`, `comment_id`, and the read-only `card_id` and `board_id`. `card_id` and `board_id` are derived through the Comment (Comment, Card, Column, Board) and are not stored.
- Response shape of criterion 7: `{"data": {"items": [...], "page": <int>, "per_page": <int>, "total": <int>, "total_pages": <int>, "unread_count": <int>}}`.
- Polling interval: 30000 ms (changed from 15 seconds in V1).
- Criterion 15 is inactive and deferred (OD-04).
- A Notification of a soft-deleted Card is hidden under Requirement 6 criterion 16 (OD-15).

#### Related Areas

notifications Blueprint, comments Blueprint, Notification_Bell, steering PR-05 and TC-15.

Routes/Pages: `GET /api/notifications`, `PATCH /api/notifications/<id>/read`, `POST /api/cards/<id>/comments`, `PATCH /api/comments/<id>`, `DELETE /api/comments/<id>`, `DELETE /api/boards/<id>/members/<user_id>`; pages `/`, `/boards/[id]`, `/my-tasks`, `/profile` (header Notification_Bell).

### Requirement 10: Card Search

**Priority:** Mandatory
**Source:** Both
**User Story:** As a Member, I want to search Cards by title keyword, so that I can find work quickly.

#### Acceptance Criteria

1. WHEN a Member sends `GET /api/cards?q=<term>` with a trimmed term of 1 to 100 characters, THE Search_Service SHALL return HTTP status 200 with all non-deleted Cards whose title contains the term, ignoring letter case, on Boards of the Member's Teams.
2. WHERE the request includes `board_id`, THE Search_Service SHALL restrict results to Cards of that Board.
3. WHERE the request includes `board_id`, THE API SHALL verify that the requester is a member of the Team that owns that Board; IF `board_id` references an existing Board the requester cannot access, THEN THE API SHALL reject the request with HTTP status 403 and the Generic_Denial_Body; IF `board_id` references a Board that does not exist, THEN THE API SHALL reject the request with HTTP status 404 and the Generic_Denial_Body, evaluated first (Requirement 1 criteria 2 and 7).
4. THE Search_Service SHALL include in each search result the Card list item defined in the Validation Rules of this Requirement.
5. IF `q` is empty, whitespace-only, or longer than 100 characters, THEN THE API SHALL reject the request with HTTP status 400.
6. FOR ALL search results, THE Search_Service SHALL return only non-deleted Cards on Boards that the requester belongs to (invariant).
7. FOR ALL terms K, a search for K SHALL return every accessible non-deleted Card whose title contains K, and each returned Card's title SHALL contain K (soundness and completeness).
8. FOR ALL terms K, a search for K with unchanged data SHALL return the same result set when repeated (idempotence).
9. IF a search matches no Cards, THEN THE API SHALL return an empty list with HTTP status 200.
10. WHEN a user types in the Board Detail search input, THE Frontend SHALL send a search request only after 300 ms without further input.
11. WHILE the search input is empty, THE Frontend SHALL send no search request.

#### Validation Rules

- Matching field: Card title only, case-insensitive (OD-09). A description is not searched.
- Pagination: none in V2 (A-01).
- Relation to `board_id`: `q` alone searches all Boards the requester can access; `board_id` is optional and, when supplied, narrows the search to that Board after Team access is verified (criteria 2 and 3).
- Card list item (all keys snake_case; each item includes `id`): `id`, `title`, `order`, `column_id`, `column_name`, `board_id`, `board_name`, `assignee_id` (null when the Card has no Assignee), and `assignee` (an object with `id`, `name`, `username`, or null) **[Proposed]**. The sources list only `board_name`, `column_name`, and `title` (this Requirement) and `board_id`, `board_name`, `column_name`, and `title` (Requirement 18); the remaining keys are added here so that one shape serves every use.
- Search result item: the Card list item (criterion 4).
- My Tasks item (Requirement 18 criterion 5): the Card list item with `assignee_id` equal to the requester; the Frontend groups the items by `board_name`.
- The nested Card of `GET /api/boards/<id>` is a different shape (Requirement 4 Validation Rules).
- A Guest cannot reach `GET /api/cards` (Requirement 3 criterion 14).

#### Related Areas

cards Blueprint, Search_Service, Board Detail page, steering TC-16.

Routes/Pages: `GET /api/cards`; page `/boards/[id]`.

### Requirement 11: Board Analytics

**Priority:** Mandatory
**Source:** Both
**User Story:** As an Admin, I want per-board analytics, so that I can see workload distribution and team activity.

#### Acceptance Criteria

1. WHEN an Admin sends `GET /api/boards/<id>/analytics`, THE Analytics_Service SHALL return HTTP status 200 with the number of non-deleted Cards in each Column.
2. WHEN an Admin sends `GET /api/boards/<id>/analytics`, THE Analytics_Service SHALL return the number of Completed Cards completed this week as defined in Requirement 24.
3. WHEN an Admin sends `GET /api/boards/<id>/analytics`, THE Analytics_Service SHALL return, for each current Team member, the number of Activity_Events that member performed on the Board in the date range, including members with 0 events.
4. WHEN an Admin sends `GET /api/boards/<id>/analytics`, THE Analytics_Service SHALL return the number of Activity_Events per UTC day over the date range.
5. WHERE the request includes both `start_date` and `end_date` in `YYYY-MM-DD` format, THE Analytics_Service SHALL use that inclusive range; WHERE the request includes neither, THE Analytics_Service SHALL use the last 7 days ending today in UTC **[Proposed, A-02]**.
6. IF a Member or Guest requests analytics, THEN THE API SHALL reject the request with HTTP status 403.
7. IF only one of `start_date` or `end_date` is provided, `end_date` is earlier than `start_date`, a date is not in `YYYY-MM-DD` format, or the range exceeds 366 days, THEN THE API SHALL reject the request with HTTP status 400.
8. FOR ALL Boards, THE sum of the per-Column Card counts returned by THE Analytics_Service SHALL equal the total number of non-deleted Cards on the Board (invariant).
9. FOR ALL Boards, THE sum of the per-day Activity_Event counts returned by THE Analytics_Service SHALL equal the number of Activity_Events in the requested date range (invariant).
10. THE Analytics_Service SHALL compute the aggregates with SQLAlchemy joins in the service layer.
11. THE Frontend SHALL display the analytics panel on the Board Detail page only for Admins.

#### Validation Rules

- Request fields: `start_date` and `end_date`, both or neither, each `YYYY-MM-DD`, `end_date` not before `start_date`, range at most 366 days; any other query field is rejected with 400.
- Activity_Event types: `card_created`, `card_updated`, `card_moved`, `card_deleted`, `comment_added`. Activity_Events of a soft-deleted Card are excluded from analytics (Requirement 6 criterion 16).
- Response keys: `cards_per_column`, `completed_this_week`, `member_activity`, `activity_per_day`, `start_date`, `end_date`.
- Element shapes **[Proposed]** (the sources name the keys only):
  - `cards_per_column`: a list of `{column_id, column_name, count}` ordered by Column `order` ascending.
  - `completed_this_week`: an integer.
  - `member_activity`: a list of `{user_id, name, username, event_count}`, one item per current Team member.
  - `activity_per_day`: a list of `{date, count}` ordered by `date` ascending, with every day of the range present (`count` 0 for a day with no Activity_Events); `date` is a `YYYY-MM-DD` string.
  - `start_date` and `end_date`: `YYYY-MM-DD` strings that echo the range used.

#### Related Areas

analytics Blueprint, Board Detail page, Requirement 24.

Routes/Pages: `GET /api/boards/<id>/analytics`; page `/boards/[id]`.

### Requirement 12: Team Member Management

**Priority:** Retained
**Source:** Both
**User Story:** As an Admin, I want to manage Team members and their roles, so that the right people have the right access.

#### Acceptance Criteria

1. WHEN an Admin sends `POST /api/boards/<id>/members` with the `email` of a registered user and a `role` of `member` or `admin` (default `member`), THE API SHALL add that user to the Team that owns the Board and return HTTP status 201 with the membership.
2. IF an Admin of the Team sends `POST /api/boards/<id>/members` with an `email` that does not belong to a registered user, THEN THE API SHALL reject the request with HTTP status 404 and the body `{"error": "User not found"}`; a requester who is not an Admin receives HTTP status 403 under criterion 9 before the `email` is looked up.
3. IF an Admin of the Team sends a well-formed `POST /api/boards/<id>/members` request for a user who is already a member of the Team, THEN THE API SHALL reject the request with HTTP status 409; a requester who is not an Admin receives HTTP status 403 under criterion 9.
4. WHEN an Admin sends `PATCH /api/boards/<id>/members/<user_id>` with a valid `role`, THE API SHALL persist the new role and apply it to that member's subsequent requests.
5. WHEN an Admin sends `DELETE /api/boards/<id>/members/<user_id>`, THE API SHALL delete the membership, retain the Comments and Cards authored by that user, and return HTTP status 200 with `{"data": {"id": "<user_id>"}}`.
6. WHEN a member is removed, THE API SHALL set `assignee_id` to null on every non-deleted Card of the Team's Boards that has that user as Assignee.
7. WHEN an Admin or a Member sends `GET /api/boards/<id>/members`, THE API SHALL return HTTP status 200 with each Team member's `user_id`, `name`, `username`, and `role`.
8. IF an Admin attempts to remove or demote the last Admin of a Team, THEN THE API SHALL reject the request with HTTP status 409 and leave the membership unchanged.
9. IF a user who is not an Admin of the Team (a Member or a non-member) sends a request to add, change, or remove a Team member, THEN THE API SHALL reject the request with HTTP status 403 before evaluating the `email`, the membership state, or the `role`.
10. FOR ALL Teams, THE API SHALL keep at least one Admin in the Team (invariant).

#### Validation Rules

- `role`: `member` or `admin`. `email`: valid email format.
- `GET`, `PATCH` member routes and the Team scope of these routes are additions beyond the assignment endpoint list (OD-07).
- A Board ID in the path that does not exist returns 404 with the Generic_Denial_Body before the Admin check (Requirement 1 criteria 2 and 7).
- Request fields: add takes `email` (required) and `role` (optional, `admin` or `member`, default `member`); role update takes `role` (required, `admin` or `member`); remove takes no body; unknown fields are rejected with 400.
- Team member management is API-only in V1: no Frontend screen, member panel, or invite UI exists for this requirement (OD-14).

#### Related Areas

boards Blueprint, Authorization_Service, steering G-04.

Routes/Pages: `POST /api/boards/<id>/members`, `GET /api/boards/<id>/members`, `PATCH /api/boards/<id>/members/<user_id>`, `DELETE /api/boards/<id>/members/<user_id>`; no page.

### Requirement 13: Authentication

**Priority:** Mandatory
**Source:** Both
**User Story:** As a user, I want to register and sign in with a JWT, so that only I can act under my identity.

#### Acceptance Criteria

1. WHEN a visitor sends `POST /api/auth/register` with `name` (1 to 100 characters), `username` (3 to 30 characters of letters, digits, and underscore), a valid `email`, and `password` of at least 8 characters, THE API SHALL create the user with the `username` converted to lowercase and return HTTP status 201 with the safe user payload `id`, `name`, `username`, `email`, and `created_at`.
2. WHEN a visitor registers, THE API SHALL create the user, the personal Team of that user (`is_personal` true, `owner_id` = the new user), and the Admin membership of the user in that Team in one transaction, so that either all three exist or none exists.
3. IF the `email` or the `username` is already registered, comparing case-insensitively, THEN THE API SHALL reject the request with HTTP status 409.
4. IF a registration field is missing or invalid, THEN THE API SHALL reject the request with HTTP status 400 and a validation error message.
5. WHEN a user sends `POST /api/auth/login` with valid credentials, THE API SHALL return HTTP status 200 with `data` containing `access_token` (the JWT), `token_type` `Bearer`, `expires_in` 3600, and `user` (the safe user payload `id`, `name`, `username`, `email`, `created_at`).
6. THE API SHALL issue each JWT with an expiry of 60 minutes after issuance and a user UUID string as identity.
7. IF a user submits an unknown `email` or a wrong `password`, THEN THE API SHALL return HTTP status 401 with the identical body `{"error": "Invalid credentials"}` in both cases.
8. IF a request to a protected endpoint (every endpoint other than the exempt endpoints in criterion 9) lacks a valid, unexpired JWT, THEN THE API SHALL reject the request with HTTP status 401.
9. THE API SHALL require a JWT on every endpoint except the exempt endpoints `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/health`, and the Guest_Read_Endpoints named in Requirement 3 criterion 3, and THE API SHALL NOT require a JWT on any exempt endpoint (the JWT-required flag is false for each); THE API SHALL process a request to `POST /api/auth/register`, `POST /api/auth/login`, or `GET /api/health` whether or not an `Authorization` header is present, and THE API SHALL decide every request to a Guest_Read_Endpoint with the Access Resolution Table (Requirement 3 criteria 3 to 5 and 9 to 12), so that a request with an invalid, malformed, or expired JWT receives HTTP status 401 (step 1), a request with no `Authorization` header and no `X-Invite-Token` receives HTTP status 401 (step 2), a request with a valid JWT of a non-member and no `X-Invite-Token` receives HTTP status 403 (step 5), and a valid `X-Invite-Token` without an `Authorization` header makes a JWT unnecessary (step 7).
10. THE API SHALL store passwords only as salted hashes produced by a password hashing algorithm designed for password storage.
11. THE API SHALL exclude `password` and `password_hash` from every response body.
12. THE API SHALL perform authorization on the server for every protected endpoint, using the identity in the JWT and Team membership from the Database.
13. IF a request to a protected endpoint carries no JWT, THEN THE API SHALL respond with HTTP status 401 before any Team membership or role evaluation.
14. IF a request to a protected endpoint carries a valid, unexpired JWT and the requester fails the Team membership or role check, THEN THE API SHALL respond with HTTP status 403; HTTP status 401 is returned only for a missing, invalid, or expired JWT; on a Guest_Read_Endpoint the Access Resolution Table (Requirement 3) decides the response, and 401 applies only to steps 1 and 2.

#### Validation Rules

- `email`: valid format, at most 254 characters, unique case-insensitively. `password`: 8 to 128 characters. `username`: 3 to 30 characters of letters, digits, underscore, compared case-insensitively, normalized to lowercase before storage and lookup, unique (a case-insensitive duplicate gives 409).
- Safe user payload (register response `data`, login `user`, `GET` and `PATCH /api/users/me`): `id`, `name`, `username`, `email`, `created_at`; it never contains `password` or `password_hash`.
- Login response `data`: `access_token`, `token_type`, `expires_in`, `user`.
- Logout is performed by the Frontend (Requirement 21); an unexpired JWT stays valid until expiry (OD-10).

#### Related Areas

auth Blueprint, AuthContext, steering TC-08.

Routes/Pages: cross-cutting; `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/health`, `GET /api/boards/<id>`, `GET /api/cards/<id>/comments`, and every protected route under the stated Blueprints; pages `/register`, `/login`.

### Requirement 14: Response Time

**Priority:** Retained
**Source:** Both
**User Story:** As a Member, I want Sevy to respond within a measurable time, so that I can keep working without waiting.

#### Acceptance Criteria

1. WHILE 200 users are concurrently active on one Board of 5 Columns and 50 Cards on a warm API instance, THE API SHALL return responses in 300 ms or less for at least 95% of requests, measured at the API server over a 10-minute window.
2. WHEN a user sends `GET /api/boards/<id>`, THE API SHALL load the Columns and Cards with at most 3 SQL queries.
3. WHEN a client sends `GET /api/health`, THE API SHALL respond within 2000 ms.
4. THE repository SHALL contain a repeatable load-test script that generates the load of criterion 1 and records the 95th percentile response time measured at the API server over the 10-minute window; the script is a development tool and adds no runtime dependency.
5. WHEN a load-test run is recorded, THE performance record SHALL state the Railway plan, the Gunicorn worker class and worker count, the database plan, and the name and version of the load-test script.
6. WHILE no recorded run shows a 95th percentile of 300 ms or less under the conditions of criterion 1, THE performance status of Requirement 14 criterion 1 and Requirement 15 criterion 1 SHALL be "not measured" or "not met" and SHALL NOT be reported as met.

#### Validation Rules

- Steering NFR-01 states p95 of 500 ms for 20 sequential requests; the 300 ms figure here is stricter and does not conflict.
- The 300 ms target of criterion 1 is a measurable target and not a claimed result. The target is met only when a recorded run (criteria 4 and 5) shows it. The same method applies to Requirement 15 criterion 1.
- Current deployment configuration, as known from steering `tech.md` TC-20: Gunicorn with 2 workers (`--workers 2`); the worker class is not specified; no `Procfile` exists yet and no application code exists. Railway plan: NOT RECORDED. Database plan: NOT RECORDED. Load-test script name and version: NOT RECORDED. Current status: not measured.

#### Related Areas

boards Blueprint, Database indexes (Requirement 26).

Routes/Pages: cross-cutting; `GET /api/boards/<id>`, `GET /api/health`; criterion 1 applies to all routes under the stated Blueprints that the Board page uses; page `/boards/[id]`.

### Requirement 15: Concurrency Capacity

**Priority:** Retained
**Source:** Existing Sevy
**User Story:** As a Team lead, I want many people to work on one Board at once, so that large Teams can collaborate without slowdown.

#### Acceptance Criteria

1. WHILE 200 users are concurrently active on one Board, THE API SHALL keep the 95th percentile response time at or below 300 ms.
2. WHILE 200 users are concurrently active on one Board, THE API SHALL return no HTTP 5xx responses caused by Database contention.
3. WHEN two users edit the same Card at the same time, THE API SHALL apply the edits one after the other in a defined order so that the stored Card equals one of the submitted versions.
4. WHEN concurrent move requests target the same Column, THE API SHALL apply the serialization defined in Requirement 7 criterion 14.

#### Related Areas

Database transactions, Requirement 7, Requirement 26.

Routes/Pages: cross-cutting; `GET /api/boards/<id>`, `PATCH /api/cards/<id>`, `PATCH /api/cards/<id>/position`; page `/boards/[id]`.

### Requirement 16: Technology Constraints

**Priority:** Retained
**Source:** Both
**User Story:** As a developer, I want a fixed technology stack, so that the codebase stays consistent.

#### Acceptance Criteria

1. THE Frontend SHALL be implemented with Next.js, React, TypeScript, and Tailwind CSS.
2. THE API SHALL be implemented with Flask in Python.
3. THE Database SHALL be PostgreSQL, accessed from the API through SQLAlchemy, in development, test, and production.
4. THE API SHALL exchange data with the Frontend as JSON over HTTP.
5. WHEN the API serializes a Board, Column, Card, Comment, or Notification to JSON, THE API SHALL produce JSON that deserializes to an equivalent object (round-trip property).

#### Related Areas

steering tech.md TC-01 to TC-05.

Routes/Pages: cross-cutting; all routes under the stated Blueprints (criterion 5 serializes the Board, Column, Card, Comment, and Notification responses of `GET /api/boards/<id>`, `GET /api/cards/<id>/comments`, and `GET /api/notifications`); all pages of Requirement 21.

### Requirement 17: Version 2 Scope Boundary

**Priority:** Retained
**Source:** Both
**User Story:** As a product owner, I want a defined scope, so that the team delivers the core features first.

#### Acceptance Criteria

1. THE Sevy V2 release SHALL provide Boards, Columns, Cards with FLOAT ordering, Comments, drag-and-drop, Notifications, Search, Analytics, Card assignment with My Tasks, and user Profile.
2. THE Sevy V2 release SHALL exclude file attachments, email digests, and third-party integrations.
3. THE Sevy V2 release SHALL exclude real-time synchronization through WebSockets or server-sent events, password change and reset, OAuth and social login, internationalization, and touch-based drag-and-drop **[Proposed clarification from steering product.md section 8]**.
4. THE API SHALL expose only the routes listed in Appendix A.

#### Related Areas

Appendix A, steering PR-02 and section 8.

Routes/Pages: all routes under the stated Blueprints (the 32 routes of Appendix A); all pages of Requirement 21.

### Requirement 18: Card Assignment and My Tasks

**Priority:** Mandatory
**Source:** Both
**User Story:** As a Member, I want to assign Cards and see the Cards assigned to me, so that I can track my own work.

#### Acceptance Criteria

1. WHEN a Member or Admin sets `assignee_id` to the UUID of a member of the Card's Team through `POST /api/columns/<id>/cards` or `PATCH /api/cards/<id>`, THE API SHALL persist the Assignee and return the Card with `assignee_id`.
2. IF `assignee_id` references a user who is not a member of the Card's Team or a UUID that is not an existing user, THEN THE API SHALL reject the request with HTTP status 400 and the body `{"error": "Assignee must be a Team member"}`.
3. WHEN a Member or Admin sets `assignee_id` to null, THE API SHALL clear the Assignee.
4. THE API SHALL accept Cards with no Assignee.
5. WHEN a user sends `GET /api/cards?assignee=me`, THE API SHALL return HTTP status 200 with only the non-deleted Cards whose `assignee_id` equals the requester, each as the My Tasks item (the Card list item) defined in the Validation Rules of Requirement 10.
6. IF a Card is on a Board of a Team that the requester no longer belongs to, THEN THE API SHALL omit that Card from the `assignee=me` result.
7. IF a `GET /api/cards` request has an `assignee` query parameter with a value other than `me`, or has neither `assignee` nor `q`, THEN THE API SHALL reject the request with HTTP status 400; this rule applies to `GET /api/cards` requests only and not to any other request or to the `assignee_id` body field.
8. WHERE the request contains `assignee=me` together with `q` or `board_id`, THE API SHALL return only Cards that satisfy all given filters.
9. WHEN a Card is soft-deleted, THE API SHALL omit the Card from the Assignee's My Tasks result.
10. WHEN a user opens `/my-tasks`, THE Frontend SHALL display the returned Cards grouped under their Board names, with each Card row showing its title, Column name, and a BaseBadge.
11. WHERE the signed-in user has no assigned Cards, THE Frontend SHALL display an empty-state message on `/my-tasks`.
12. IF a Guest or non-member sends a request to assign a Card, THEN THE API SHALL reject the request with HTTP status 403.

#### Validation Rules

- `assignee_id`: UUID or null. A removed Team member's assignments are cleared (Requirement 12 criterion 6).
- Notification on assignment is deferred (OD-04, Requirement 9 criterion 15).
- A Guest cannot reach `GET /api/cards` (Requirement 3 criterion 14).

#### Related Areas

cards Blueprint, My Tasks page, steering PR-06.

Routes/Pages: `POST /api/columns/<id>/cards`, `PATCH /api/cards/<id>`, `GET /api/cards`; page `/my-tasks`.

### Requirement 19: User Profile

**Priority:** Mandatory
**Source:** Assignment
**User Story:** As a user, I want to view and update my profile, so that my name and email stay current.

#### Acceptance Criteria

1. WHEN a user sends `GET /api/users/me`, THE API SHALL return HTTP status 200 with the safe user payload `id`, `name`, `username`, `email`, and `created_at`, and no password data.
2. WHEN a user sends `PATCH /api/users/me` with `name` of 1 to 100 characters or a valid `email`, THE API SHALL persist the change and return HTTP status 200 with the updated safe user payload.
3. IF a `PATCH /api/users/me` body contains `password`, `password_hash`, `username`, or any other field except `name` and `email`, THEN THE API SHALL reject the request with HTTP status 400 and leave stored data unchanged.
4. IF the submitted `email` is not a valid email format or exceeds 254 characters, THEN THE API SHALL reject the request with HTTP status 400.
5. IF the submitted `email` belongs to another user, THEN THE API SHALL reject the request with HTTP status 409.
6. IF the `PATCH /api/users/me` body is empty, THEN THE API SHALL reject the request with HTTP status 400.
7. WHEN a user opens `/profile`, THE Frontend SHALL display a form with controlled inputs pre-populated from AuthContext.
8. WHEN a user submits the profile form with valid values, THE Frontend SHALL send `PATCH /api/users/me`, call the AuthContext operation `updateUser` with the `user` of the response, and show a success Toast.
9. THE AuthContext SHALL provide the operation `updateUser`, which replaces the stored user with a given user object and leaves the stored JWT unchanged.

#### Validation Rules

- `name`: 1 to 100 characters after trimming. `email`: unique case-insensitively.

#### Related Areas

users Blueprint, Profile page, AuthContext.

Routes/Pages: `GET /api/users/me`, `PATCH /api/users/me`; page `/profile`.

### Requirement 20: API Conventions and Health Check

**Priority:** Mandatory
**Source:** Both
**User Story:** As a Frontend developer, I want one consistent response shape, so that the API_Client can handle every response the same way.

#### Acceptance Criteria

1. THE API SHALL return every response body, including 401, 403, 404, 405, and 500 responses, as either `{"data": <payload>}` or `{"error": "<non-empty string>"}`, never both, so that `error` is always one non-empty string and never a nested object.
2. WHEN a request names an unknown route, THE API SHALL respond with HTTP status 404 and the body `{"error": "Not found"}`.
3. IF an unhandled exception occurs, THEN THE API SHALL respond with HTTP status 500 and the body `{"error": "Internal server error"}` without a stack trace.
4. THE API SHALL use HTTP status 200 for read, update, and delete responses and HTTP status 201 for create responses.
5. THE API SHALL return `{"data": {"id": "<uuid>"}}` with HTTP status 200 for every DELETE endpoint.
6. THE API SHALL organize its endpoints into eight Blueprints: auth, boards, columns, cards, comments, notifications, analytics, and users.
7. WHEN a client sends `GET /api/health` without a JWT, THE API SHALL respond with HTTP status 200 and `{"data": {"status": "ok"}}` **[Proposed clarification from steering G-01]**.
8. THE API SHALL expose the 24 endpoints listed in the assignment file `backend-implementation.md`, `GET /api/health`, `GET /api/cards`, `POST /api/boards/<id>/members`, `DELETE /api/boards/<id>/members/<user_id>`, and the 4 additional endpoints recorded in OD-07, 32 endpoints in total, as listed in Appendix A.
9. IF a request body contains a field that is not defined for the endpoint, THEN THE API SHALL reject the request with HTTP status 400.
10. IF a request carries an `Origin` header that is not in the configured allowed origins, THEN THE API SHALL omit the `Access-Control-Allow-Origin` header from the response.
11. THE API SHALL use snake_case for every JSON key.
12. FOR ALL routes, THE API SHALL respond to a request that lacks a valid JWT with HTTP status 401 unless the route is public under Requirement 13 criterion 9.
13. WHEN a request fails validation with HTTP status 400, THE API SHALL return one deterministic `error` string in which the failing fields are sorted alphabetically, each entry has the form `<field>: <messages joined by ", ">`, and the entries are joined by " | ", without a traceback; a 400 that names no field (such as an invalid path UUID under Requirement 1 criterion 6) carries a non-empty string; this format applies wherever another requirement of this document calls for a "validation error message" or a "non-empty `error` message" with HTTP status 400. Example: `{"error": "order: Must be greater than 0. | title: Length must be between 1 and 200."}`.

#### Validation Rules

- Status codes in use: 200, 201, 400, 401, 403, 404, 405, 409, 500. The status 405 applies to a known route requested with an unsupported method and carries the standard error envelope.
- Error shape: a single string `error` for every non-2xx response, including a 400 validation failure (criterion 13). A 409 carries a string `error` only, with no remediation hint (Requirement 5 criterion 8, Requirement 7 criterion 6).
- Not-found and denial bodies: `{"error": "Not found"}` for an unknown route (criterion 2), an invalid or revoked Invite_Link token on a Guest_Read_Endpoint, an `invite_id` that does not exist or is not bound to the Board, and a Notification not owned by the requester; the Generic_Denial_Body `{"error": "Not found or access denied"}` for a Board, Column, Card, or Comment ID in the URL path that does not exist or whose Board the requester cannot access, and for a soft-deleted Card (Requirement 1 criterion 2 and Validation Rules).
- The Frontend reads the error through the ApiError `message`, which is the `error` string (Glossary, Requirement 22 criterion 4).

#### Related Areas

All Blueprints, steering TC-06 and NFR-04.

Routes/Pages: cross-cutting; `GET /api/health` and all routes under the stated Blueprints; no page.

### Requirement 21: Frontend Pages, Authentication State, and Navigation

**Priority:** Mandatory
**Source:** Both
**User Story:** As a user, I want clear pages for sign-in and board work, so that I can complete my tasks in the browser.

#### Acceptance Criteria

1. THE Frontend SHALL provide exactly these routes: `/register`, `/login`, `/`, `/boards/[id]`, `/my-tasks`, and `/profile`, and present the Card detail as the Card_Detail_Modal instead of a route.
2. THE Frontend SHALL render `/` (Dashboard) and `/boards/[id]` (Board Detail) as Server Components that fetch data from the API and pass it to Client Components.
3. WHEN a user opens `/`, THE Frontend SHALL display the Boards returned by `GET /api/boards` and a control that opens a Board creation form inside BaseModal.
4. WHEN a user opens `/boards/[id]`, THE Frontend SHALL display the Board in the Kanban_Board with its Columns and Cards, a Card creation form, a Column creation form, and the search input.
5. WHEN a Member clicks a Card, THE Frontend SHALL open the Card_Detail_Modal inside BaseModal showing the Card details, the Comment threads, and a comment input form.
6. WHEN a visitor submits the `/register` form with valid values, THE Frontend SHALL send `POST /api/auth/register` and, on HTTP status 201, redirect to `/login`.
7. WHEN a visitor submits the `/register` form with an invalid field, THE Frontend SHALL show the validation message next to the field using client-side validation that applies the rules of Requirement 13.
8. WHEN a visitor submits valid credentials on `/login`, THE Frontend SHALL store the JWT and the `user` from the login response in AuthContext, write the JWT to the cookie `sevy_token` with `path=/`, `SameSite=Lax`, and a max-age of 3600 seconds, and redirect to `/`.
9. IF a visitor submits invalid credentials on `/login`, THEN THE Frontend SHALL display the error message "Invalid credentials" and remain on `/login`.
10. WHEN a signed-in user reloads `/boards/[id]`, THE Frontend SHALL keep the user signed in by reading the `sevy_token` cookie on the server.
11. IF an unauthenticated visitor requests `/`, `/boards/[id]`, `/my-tasks`, or `/profile`, THEN THE Frontend SHALL redirect the visitor to `/login`, except for a request to `/boards/[id]` that carries the `invite` query parameter, which THE Frontend SHALL serve in Guest_Mode without a redirect to `/login`, so that the API resolves access under Requirement 3.
12. WHEN a signed-in user chooses logout, THE Frontend SHALL clear AuthContext and the `sevy_token` cookie and redirect to `/login`.
13. WHEN a user has logged out and requests `/`, THE Frontend SHALL redirect to `/login`.
14. THE Frontend SHALL display the Notification_Bell in the header of every authenticated page.
15. THE Frontend SHALL send every HTTP request to the API through the API_Client and read the base URL from `API_BASE_URL` on the server and `NEXT_PUBLIC_API_BASE_URL` in the browser.
16. THE API_Client SHALL attach `Authorization: Bearer <token>` WHEN a token exists and the page is not in Guest_Mode (criterion 17), unwrap the `data` field of successful responses, and throw an ApiError with `statusCode` and `message` (the `error` string) on a non-2xx response; WHEN no HTTP response is received (network failure, timeout, or CORS block), THE API_Client SHALL throw an ApiError with `statusCode` 0.
17. WHILE the page `/boards/[id]?invite=<token>` is displayed in Guest_Mode, THE API_Client SHALL send the header `X-Invite-Token` and no `Authorization` header, only on `GET /api/boards/<id>` and `GET /api/cards/<id>/comments`, and THE Frontend SHALL create no authenticated session and write no `sevy_token` cookie.

#### Validation Rules

- Auth flow scenarios covered: successful login redirect (8), invalid credentials error (9), unauthenticated redirect (11), post-logout redirect (12, 13).
- Cookie transport follows steering TG-01; HttpOnly is not possible (OD-10).

#### Related Areas

Next.js App Router, AuthContext, middleware, API_Client, steering TC-12 and TC-13.

Routes/Pages: `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/boards`, `GET /api/boards/<id>`, `GET /api/cards/<id>/comments`, `POST /api/cards/<id>/comments`, `GET /api/notifications`, and all routes under the stated Blueprints through the API_Client; pages `/register`, `/login`, `/`, `/boards/[id]`, `/my-tasks`, `/profile`.

### Requirement 22: Frontend Error Handling

**Priority:** Mandatory
**Source:** Both
**User Story:** As a user, I want clear messages when something fails, so that I know what to do next.

#### Acceptance Criteria

1. WHEN the API_Client receives an HTTP status 401 response, THE Frontend SHALL show the Toast "Session expired, please log in", clear AuthContext and the `sevy_token` cookie, and redirect to `/login`.
2. WHEN the API_Client receives an HTTP status 403 response, THE Frontend SHALL show the Toast "You don't have permission".
3. WHEN the API_Client receives an HTTP status 404 response, THE Frontend SHALL show the Toast "Not found".
4. WHEN the API_Client receives an HTTP status 400 or 409 response, THE Frontend SHALL show the `message` of the thrown ApiError as a Toast, which is the server `error` string (for a 400 validation failure the normalized string of Requirement 20 criterion 13; Glossary entry ApiError).
5. WHEN the API_Client receives an HTTP status of 500 or higher, or throws an ApiError with `statusCode` 0 because no HTTP response was received (Requirement 21 criterion 16), THE Frontend SHALL show the Toast "Something went wrong. Try again."
6. IF a request to the `/login` endpoint returns HTTP status 401, THEN THE Frontend SHALL display the login error message from Requirement 21 criterion 9 instead of the session-expired Toast.
7. THE Frontend SHALL show Toasts only through the shared toast helper that wraps `toast.success()`, `toast.error()`, and `toast.loading()`.

#### Related Areas

ApiError, error-handler hook, toast helper, steering TC-13.

Routes/Pages: `POST /api/auth/login` (criterion 6) and all routes under the stated Blueprints through the API_Client; pages `/register`, `/login`, `/`, `/boards/[id]`, `/my-tasks`, `/profile`.

### Requirement 23: Responsive Layout

**Priority:** Mandatory
**Source:** Both
**User Story:** As a user on any device, I want every page to fit my screen, so that nothing is cut off or overlapping.

#### Acceptance Criteria

1. WHILE the viewport width is 375 px, 768 px, or 1280 px, THE Frontend SHALL render each of `/register`, `/login`, `/`, `/boards/[id]`, `/my-tasks`, and `/profile` with `document.documentElement.scrollWidth` less than or equal to `window.innerWidth`.
2. WHILE the viewport width is 375 px, 768 px, or 1280 px, THE Frontend SHALL render each page and the Card_Detail_Modal with no clipped or overlapping content.
3. WHILE the viewport width is smaller than the combined width of the Board's Columns, THE Kanban_Board SHALL scroll horizontally inside its own container and THE page body SHALL not scroll horizontally.

#### Validation Rules

- Mobile touch-based dragging is out of scope (Requirement 17 criterion 3); mobile verification covers layout only.

#### Related Areas

All pages, Tailwind CSS, steering NFR-03.

Routes/Pages: no route; pages `/register`, `/login`, `/`, `/boards/[id]`, `/my-tasks`, `/profile`.

### Requirement 24: Card Completion Tracking

**Priority:** Mandatory
**Source:** Proposed clarification
**User Story:** As an Admin, I want a single definition of a completed Card, so that "cards completed this week" is measurable.

#### Acceptance Criteria

1. THE Database SHALL store on each Column a boolean `is_done` with default false and on each Card a nullable `completed_at` timestamp.
2. WHEN a Card is moved from a Column with `is_done` false into a Column with `is_done` true, THE API SHALL set `completed_at` to the current UTC time.
3. WHEN a Card is created in a Column with `is_done` true, THE API SHALL set `completed_at` to the current UTC time.
4. WHEN a Card is moved from a Column with `is_done` true into a Column with `is_done` false, THE API SHALL set `completed_at` to null.
5. WHEN a Card is moved between two Columns that both have `is_done` true, THE API SHALL leave `completed_at` unchanged.
6. WHEN an Admin changes `is_done` of a Column from false to true, THE API SHALL set `completed_at` to the current UTC time on each non-deleted Card in that Column whose `completed_at` is null; WHEN from true to false, THE API SHALL set `completed_at` to null on each Card in that Column.
7. THE Analytics_Service SHALL count as "completed this week" each Card with `completed_at` greater than or equal to 00:00 UTC on the Monday of the current ISO week and `deleted_at` null.
8. FOR ALL Cards with `completed_at` on the Sunday before the current ISO week, THE Analytics_Service SHALL exclude the Card from the completed-this-week count.

#### Validation Rules

- `is_done` is settable on Column create and Column update only.

#### Related Areas

columns Blueprint, cards Blueprint, analytics Blueprint, steering PR-04.

Routes/Pages: `POST /api/boards/<id>/columns`, `PATCH /api/columns/<id>`, `POST /api/columns/<id>/cards`, `PATCH /api/cards/<id>/position`, `GET /api/boards/<id>/analytics`; page `/boards/[id]`.

### Requirement 25: Shared UI Components and Modal Interaction

**Priority:** Mandatory
**Source:** Both
**User Story:** As a user, I want consistent buttons, badges, and dialogs, so that the interface behaves the same on every page.

#### Acceptance Criteria

1. THE Frontend SHALL render every button through BaseButton with variant `primary`, `secondary`, or `destructive`, including on `/my-tasks` and `/profile`.
2. THE Frontend SHALL render status and label badges through BaseBadge with color `gray`, `green`, `yellow`, `red`, or `blue`.
3. THE Frontend SHALL render every form and the Card_Detail_Modal inside BaseModal.
4. WHEN a user presses the Escape key while BaseModal is open, THE BaseModal SHALL close.
5. WHEN BaseModal opens, THE BaseModal SHALL move keyboard focus into the modal; WHEN BaseModal closes, THE BaseModal SHALL return focus to the element that opened it.
6. THE Frontend SHALL give every icon-only button an `aria-label`.

#### Related Areas

`components/shared`, steering NFR-05, ST-08.

Routes/Pages: no route; pages `/` and `/boards/[id]` (BaseModal forms), `/my-tasks` and `/profile` (BaseButton), and every other page of Requirement 21 that renders a button.

### Requirement 26: Data Storage and Integrity

**Priority:** Retained
**Source:** Both
**User Story:** As a developer, I want a defined data model with indexes and transactions, so that data stays consistent and queries stay fast.

#### Acceptance Criteria

1. THE Database SHALL use a UUID primary key on the tables for users, teams, team memberships, boards, columns, cards, comments, notifications, invite links, and activity events.
2. THE Database SHALL store `created_at`, `updated_at`, and `deleted_at` on Cards and `deleted_at` on Comments, and THE API SHALL set `updated_at` on every Card update.
3. THE Database SHALL have indexes on Team membership lookups by user and Team, Boards by Team, Columns by Board and `order`, Cards by Column and `order`, Cards by Assignee, case-insensitive Card title search, Comments by Card, Notifications by recipient, Activity_Events by Board and timestamp, and a unique index on the Invite_Link token.
4. THE Database SHALL enforce `ON DELETE CASCADE` from Board to Columns, Invite_Links, and Activity_Events, from Column to Cards, and from Card to Comments; a Card soft delete SHALL trigger no cascade (Requirement 6 criterion 16).
5. WHEN a write request fails after partial changes, THE API SHALL roll back all changes of that request.
6. THE Database SHALL store the Card `order` and Column `order` as non-null Float values.
7. THE Database SHALL keep the `order` of active Cards unique within one Column and the `order` of active Columns unique within one Board, and a soft-deleted Card SHALL NOT block an active Card from using the same `order`.
8. WHEN a Card or Column reorder or a Rebalance changes several `order` values, THE API SHALL apply the change in one transaction so that no committed or concurrently visible state contains a duplicate active `order` and the change is all-or-nothing.
9. THE Database SHALL store on each Team a boolean `is_personal` (default false) and an `owner_id` that references a user, SHALL allow at most one personal Team per user, and SHALL keep the owner of a personal Team as an Admin member of that Team.
10. THE Database SHALL store on each Notification `recipient_id` (a user) and `comment_id` (a Comment) and no `user_id` and no `card_id`.
11. THE Database SHALL accept for the `event_type` of an Activity_Event only `card_created`, `card_updated`, `card_moved`, `card_deleted`, and `comment_added`.
12. THE Database SHALL store on each user a `username` that is unique case-insensitively and stored in lowercase.

#### Related Areas

models, migrations, steering TC-10 and ST-12.

Routes/Pages: database; all routes under the stated Blueprints that write or read the stored entities (for example `POST /api/columns/<id>/cards`, `PATCH /api/cards/<id>`, `DELETE /api/boards/<id>`, `DELETE /api/columns/<id>`, `GET /api/boards/<id>`); no page.

### Requirement 27: Deployment and Environment

**Priority:** Mandatory
**Source:** Assignment
**User Story:** As a grader, I want both applications live on public URLs, so that I can verify the product end to end.

#### Acceptance Criteria

1. THE API SHALL be deployed on Railway at a public HTTPS URL with a PostgreSQL database and SHALL be started with `gunicorn "app:create_app()"`.
2. WHEN the API is deployed, THE release step SHALL run `flask db upgrade` so that all migrations are applied before the API serves traffic.
3. WHEN `GET /api/health` is requested at the public URL, THE API SHALL respond as stated in Requirement 20 criterion 7 within the time limit of Requirement 14 criterion 3.
4. WHEN `POST /api/auth/register` and `POST /api/auth/login` are sent from Postman to the public URL, THE API SHALL return JSON in the envelope of Requirement 20 criterion 1.
5. WHEN one authenticated request to a route of each of the eight Blueprints (auth, boards, columns, cards, comments, notifications, analytics, users) is sent to the public URL, THE API SHALL return JSON in the envelope of Requirement 20 criterion 1 for each request.
6. THE Next.js application SHALL be deployed on Vercel at a public URL and SHALL call the deployed API through `API_BASE_URL` on the server and `NEXT_PUBLIC_API_BASE_URL` in the browser (Requirement 21 criterion 15).
7. THE API SHALL allow cross-origin requests only from the exact Vercel production origin, and from `http://localhost:3000` in development, and SHALL NOT allow `*` in production (Requirement 20 criterion 10).
8. THE hosted PostgreSQL connection string SHALL include `sslmode=require` unless the provider documents otherwise.
9. WHEN the live application is used, THE Frontend SHALL load Register, Login, Dashboard, Board Detail, Card Detail Modal, My Tasks, and Profile at the viewport widths of Requirement 23 (375 px, 768 px, and 1280 px).

#### Validation Rules

- The criteria are verification criteria of the delivered system. This document records no public URL and claims no criterion as met; until a deployment is verified, the status of each criterion is "not verified".
- Criterion 5: the authenticated request for the `auth` Blueprint is the `POST /api/auth/login` request; the other seven Blueprints use a valid JWT from that login.
- Worker class, worker count, Railway plan, and database plan are not fixed by this requirement; they are recorded with each load-test run (Requirement 14 criterion 5).
- Rubric traceability:

| Criterion | Grading rubric or deliverables item |
|---|---|
| 1 | Rubric (Complete Implementation): the Flask API is live on a public URL; Deliverable 3: live Flask API; the start command is not a rubric item (approved rule: tech.md TC-20) |
| 2 | Deliverable 3: all migrations applied with `flask db upgrade` |
| 3 | Rubric (Complete Implementation): `GET /api/health` returns 200 on the public URL; Deliverable 3: verified with `GET /api/health` from Postman |
| 4 | Rubric (Complete Implementation): register and login return JSON; Deliverable 3: verified with register and login from Postman |
| 5 | Deliverable 3: all eight Blueprints reachable and returning JSON in the envelope |
| 6 | Rubric (Complete Implementation): the Next.js app is live on a public URL; Deliverable 4: connected to the deployed Flask API |
| 7 | none in the rubric; approved rule: tech.md TC-20 |
| 8 | none in the rubric; approved rule: tech.md TC-10 |
| 9 | Rubric (Complete Implementation): the listed pages load and the live app is usable at mobile size; Deliverable 4: all seven pages load on desktop and mobile screen sizes |

#### Related Areas

Railway, Vercel, PostgreSQL, Gunicorn, steering `tech.md` TC-09, TC-10, and TC-20.

Routes/Pages: cross-cutting; `GET /api/health`, `POST /api/auth/register`, `POST /api/auth/login`, and one route of each of the eight Blueprints (Appendix A); pages `/register`, `/login`, `/`, `/boards/[id]`, `/my-tasks`, `/profile`, and the Card_Detail_Modal (on `/boards/[id]`).

### Requirement 28: Automated Testing

**Priority:** Mandatory
**Source:** Assignment
**User Story:** As a developer, I want a three-layer test suite, so that regressions are caught before deployment.

#### Acceptance Criteria

1. WHEN `pytest -v` is run from the Flask project root, ALL backend tests SHALL pass, and every service function SHALL have at least one success test and at least one failure test.
2. THE comments tests SHALL include HTTP status 201 for a successful create, 400 for missing `content`, 401 for an unauthenticated request, and 403 for an edit or delete by a user who is not the author (Requirement 8 Validation Rules).
3. WHEN `npm test` is run from the Next.js project root, THE React Testing Library tests for BaseButton, BaseBadge, BaseModal, `useDragAndDrop`, `useNotifications`, and `useDebouncedValue` SHALL pass.
4. WHEN `npx playwright test` is run against the live Vercel URL, THE suite SHALL cover four auth scenarios: successful login redirect, invalid credentials error, unauthenticated redirect to `/login`, and post-logout redirect (Requirement 21 criteria 8, 9, 11, 12, and 13).
5. THE Playwright Kanban journey SHALL cover eight steps: (1) log in; (2) create a Board; (3) add the Column "To Do"; (4) add the Column "Done"; (5) create a Card in "To Do"; (6) drag the Card to "Done"; (7) reload the page; (8) assert that the Card is still in "Done" (Requirement 7 criterion 15).
6. THE Playwright test files SHALL contain no call to `waitForTimeout`.
7. THE Playwright HTML report directory SHALL be committed to the repository, and the report SHALL show all tests passed.
8. WHEN the Playwright suite runs with `--repeat-each=3`, ALL tests SHALL pass, and each test SHALL create its own user through the API with a unique email and a unique username (OD-05).

#### Validation Rules

- The criteria are verification criteria of the delivered system. Until a run is recorded, the status of each suite is "not run", and this document claims no test result.
- Criterion 5: the eight steps follow steering `tech.md` TG-02.
- Rubric traceability:

| Criterion | Grading rubric or deliverables item |
|---|---|
| 1 | Rubric (Complete Implementation): `pytest -v` passes; the success and failure test per service function is not a rubric item (approved rule: tech.md TC-17) |
| 2 | Rubric (Complete Implementation): the comments tests cover 201, 400, 401, and 403 |
| 3 | Deliverable 7: README test steps for the React Testing Library tests with `npm test`; the named components and hooks are not a rubric item (approved rule: tech.md TC-18) |
| 4 | Rubric (Complete Implementation) and Deliverable 5: the Playwright suite against the live Vercel URL covers the four auth scenarios |
| 5 | Rubric (Complete Implementation) and Deliverable 5: the Playwright suite covers the Kanban journey of eight steps, including position persistence after reload |
| 6 | Rubric (Complete Implementation) and Deliverable 5: no `waitForTimeout` in the test files |
| 7 | Rubric (Complete Implementation): the Playwright report shows all tests passing; Deliverable 5: the full test report is in the repository |
| 8 | none in the rubric; approved rule: tech.md TC-19 |

#### Related Areas

pytest, React Testing Library, Playwright, steering `tech.md` TC-17, TC-18, and TC-19.

Routes/Pages: `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/cards/<id>/comments`, `GET /api/cards/<id>/comments`, `PATCH /api/comments/<id>`, `DELETE /api/comments/<id>`; pages `/login`, `/`, `/boards/[id]`.

### Requirement 29: Repository and Documentation

**Priority:** Mandatory
**Source:** Assignment
**User Story:** As a grader, I want a traceable repository, so that I can check specs, guidelines, code, and evidence.

#### Acceptance Criteria

1. THE repository SHALL separate `/specs`, `/guidelines`, `backend/app/blueprints/<feature>/` (each with `routes.py`, `service.py`, and `schema.py`), `frontend/components/shared/`, `frontend/hooks/`, and `frontend/lib/`.
2. THE `/specs` folder SHALL contain `requirements.md`, `design.md`, `tasks.md`, and `CHANGELOG.md`, THE `design.md` SHALL map every acceptance criterion ID `R<N>.<k>` to a Flask route or a Next.js page, and THE `tasks.md` SHALL map every route and every page to at least one task.
3. THE `CHANGELOG.md` SHALL contain at least 5 refinement entries, each with a Prompt, a Before, and an After.
4. THE `/guidelines` folder SHALL contain `frontend.md`, `backend.md`, and `database.md`, and each guideline SHALL have an ID, a Rule, a Rationale, and an Example.
5. THE repository SHALL include the violation report `guidelines/VIOLATIONS.md` that lists at least 3 guideline violations found in AI-generated code, each with the guideline ID, the file and line, what the AI produced, and the fix applied, and at least one documented before and after comparison that reports a measured number.
6. THE repository SHALL commit a `.env.example` for both projects that lists every variable the project reads with a placeholder value, and SHALL exclude every real `.env*` file, `__pycache__/`, `.venv/`, `venv/`, `.next/`, and `node_modules/` through `.gitignore`.
7. THE `README.md` SHALL contain an overview, an AI workflow summary, the features implemented, the technologies used, local run steps, test steps for all three test layers, and screenshots: a Postman screenshot of all 8 Blueprints, each major page, a Card being dragged, and the Playwright report.
8. THE repository SHALL contain a project brief with an overview, the user roles, the core features, the tech stack, and at least 2 non-functional requirements, in the `README.md` or in `/specs`.
9. THE commit history SHALL include at least one commit for each of the commit message prefixes `spec:`, `guidelines:`, `feat(backend):`, `feat(frontend):`, `test:`, `docs:`, and `chore(deploy):`.

#### Validation Rules

- The criteria are verification criteria of the delivered system; this document claims no criterion as met.
- Criterion 1: the eight Blueprints are those of the Glossary entry "API"; the layout follows steering `structure.md` ST-01, ST-02, ST-07, and ST-09.
- Criterion 3: the heading of each entry is `## V<N> - YYYY-MM-DD`, each entry carries the labels **Prompt**, **Before**, and **After**, and the V1 baseline `## V1 - Initial Release` is not counted as a refinement entry (steering `tech.md` TC-21).
- Criterion 4: guideline IDs are `FE-nn`, `BE-nn`, and `DB-nn`, and the labels are checked by the guideline checker of steering `structure.md` ST-12.
- Criterion 5: the entries of the violation report are `### V-nn` (steering `tech.md` TC-21).
- Criterion 6: the variables are those of steering `tech.md` TC-09 (steering `structure.md` ST-13).
- Criterion 9: the prefixes are those of steering `tech.md` TC-22; the `spec:` prefix covers specification, `chore(deploy):` covers deployment, and `docs:` is the seventh approved prefix.
- Rubric traceability:

| Criterion | Grading rubric or deliverables item |
|---|---|
| 1 | Rubric (Steering Guidelines): `app/blueprints/` has the eight folders with `routes.py`, `service.py`, and `schema.py`; Deliverable 6: clean folder structure |
| 2 | Rubric (AI Development Life Cycle): `/specs` has the four files; Deliverable 1: every criterion maps to a route or page and every route and page has a task |
| 3 | Rubric (AI Development Life Cycle): at least 5 refinement entries with a before and an after; Deliverable 1: every refinement round has before and after entries; the Prompt label is not a rubric item (approved rule: tech.md TC-21) |
| 4 | Rubric (Steering Guidelines): `/guidelines` has the three files and every guideline has a Rule, a Rationale, and an Example; Deliverable 2: 3-part structure |
| 5 | Rubric (Steering Guidelines): a violation report with at least 3 violations, each with the guideline and the fix; Deliverable 2: violation report and one measurable before and after comparison |
| 6 | Rubric (Complete Implementation): `.env.example` committed for both projects and no real `.env` files; Deliverable 6: `.gitignore` and `.env.example` |
| 7 | Rubric (Complete Implementation) and Deliverable 7: README sections and screenshots |
| 8 | Rubric (AI Development Life Cycle): a project brief in the README or `/specs` |
| 9 | Deliverable 6: commit history across specification, guidelines, backend, frontend, testing, and deployment |

#### Related Areas

repository layout, `README.md`, `.gitignore`, steering `structure.md` ST-01, ST-02, ST-07, ST-09, ST-12, and ST-13, and steering `tech.md` TC-09, TC-21, and TC-22.

Routes/Pages: cross-cutting; repository and documentation requirement with no route or page of its own.
## Appendix A: Route Inventory

| Method and Route | Blueprint | Requirement | Origin |
|---|---|---|---|
| POST /api/auth/register | auth | 13 | Assignment |
| POST /api/auth/login | auth | 13 | Assignment |
| POST /api/boards | boards | 4 | Assignment |
| GET /api/boards | boards | 4 | Assignment |
| GET /api/boards/<id> | boards | 4, 3 | Assignment |
| PATCH /api/boards/<id> | boards | 4 | Assignment |
| DELETE /api/boards/<id> | boards | 4 | Assignment |
| POST /api/boards/<id>/columns | columns | 5 | Assignment |
| PATCH /api/columns/<id> | columns | 5 | Assignment |
| DELETE /api/columns/<id> | columns | 5 | Assignment |
| PATCH /api/boards/<id>/columns/reorder | columns | 5 | Assignment |
| POST /api/columns/<id>/cards | cards | 6 | Assignment |
| PATCH /api/cards/<id> | cards | 6, 18 | Assignment |
| DELETE /api/cards/<id> | cards | 6 | Assignment |
| PATCH /api/cards/<id>/position | cards | 7 | Assignment |
| POST /api/cards/<id>/comments | comments | 8 | Assignment |
| GET /api/cards/<id>/comments | comments | 8, 3 | Assignment |
| PATCH /api/comments/<id> | comments | 8 | Assignment |
| DELETE /api/comments/<id> | comments | 8 | Assignment |
| GET /api/notifications | notifications | 9 | Assignment |
| PATCH /api/notifications/<id>/read | notifications | 9 | Assignment |
| GET /api/boards/<id>/analytics | analytics | 11 | Assignment |
| GET /api/users/me | users | 19 | Assignment |
| PATCH /api/users/me | users | 19 | Assignment |
| GET /api/health | app-level | 20 | Steering G-01 |
| GET /api/cards | cards | 10, 18 | Steering G-02 |
| POST /api/boards/<id>/members | boards | 12 | Steering G-04 |
| DELETE /api/boards/<id>/members/<user_id> | boards | 12 | Steering G-04 |
| GET /api/boards/<id>/members | boards | 12 | Added in V2 (OD-07) |
| PATCH /api/boards/<id>/members/<user_id> | boards | 12 | Added in V2 (OD-07) |
| POST /api/boards/<id>/invite-links | boards | 3 | Added in V2 (OD-07) |
| DELETE /api/boards/<id>/invite-links/<invite_id> | boards | 3 | Added in V2 (OD-07) |

## Appendix B: Original-to-New Requirement ID Mapping

| V1 Requirement | V2 Requirement | Change |
|---|---|---|
| 1 Board Access Isolation | 1 | Modified: V2 to V5 returned 403 for inaccessible and non-existent IDs; V6 returned 404 `<Entity> not found` for non-existent IDs and 403 `Access denied` for inaccessible IDs; V7 returns 404 and 403 with the single Generic_Denial_Body (OD-02, OD-17) |
| 2 Role-Based Permission Enforcement | 2 | Modified: added card delete rule, comment owner rule, permission table |
| 3 Guest Access via Invite Link | 3 | Modified: create and revoke endpoints, token entropy, header transport |
| 4 Board Management | 4 | Modified: endpoints, status codes, nested board response |
| 5 Column Management | 5 | Modified: integer Position replaced by FLOAT order; `is_done` added |
| 6 Card Management | 6 | Modified: FLOAT order, soft delete, model fields, assignee |
| 7 Drag-and-Drop Card Movement | 7 | Modified: position endpoint, order validation, rebalance, optimistic update |
| 8 Threaded Comments | 8 | Modified: explicit endpoints and status codes, edit, delete, tombstone |
| 9 Mention Notifications | 9 | Modified: polling 15 s to 30 s, pagination, mark-read ownership |
| 10 Card Search | 10 | Modified: shared endpoint `GET /api/cards`, 300 ms debounce |
| 11 Board Analytics | 11 | Modified: endpoint, completed this week and member activity added; completion split to 24 |
| 12 Team Member Management | 12 | Modified: endpoints defined |
| 13 Authentication | 13 | Modified: generic session or token replaced by JWT; register and login; Frontend auth state split to 21 |
| 14 Response Time | 14 | Modified: query count; criterion 14.2 (indexes) moved to 26 |
| 15 Concurrency Capacity | 15 | Retained with cross-reference to 7 |
| 16 Technology Constraints | 16 | Retained; envelope and Blueprints split to 20 |
| 17 Version 1 Scope Boundary | 17 | Modified: now the V2 scope boundary with added exclusions |
| (new) | 18 Card Assignment and My Tasks | Added |
| (new) | 19 User Profile | Added |
| (new) | 20 API Conventions and Health Check | Added |
| (new) | 21 Frontend Pages, Authentication State, and Navigation | Added |
| (new) | 22 Frontend Error Handling | Added |
| (new) | 23 Responsive Layout | Added |
| (new) | 24 Card Completion Tracking | Added |
| (new) | 25 Shared UI Components and Modal Interaction | Added |
| (new) | 26 Data Storage and Integrity | Added (includes V1 criterion 14.2) |
| (new) | 27 Deployment and Environment | Added in V9 |
| (new) | 28 Automated Testing | Added in V9 |
| (new) | 29 Repository and Documentation | Added in V9 |

V7 note: no requirement number was added, removed, or renumbered in V7. Criteria added in V7 are appended at the end of their lists: Requirement 3 criteria 14 and 15, Requirement 6 criterion 16, Requirement 8 criterion 19, Requirement 14 criteria 4 to 6, Requirement 21 criterion 17, Requirement 26 criteria 7 to 12.

V8 note: no requirement or criterion was added, removed, or renumbered in V8. The `[Proposed, OD-nn]` tags were removed from the criteria of OD-01, OD-05, OD-08, OD-13, OD-16, OD-17, OD-18, and OD-19, and the 11 decisions moved to Resolved decisions.

V9 note: Requirements 27 to 29 are new and have no V1 predecessor.
