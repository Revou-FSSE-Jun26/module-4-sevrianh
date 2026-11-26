# Changelog

## V1 - Initial Release
- Initial requirements and design generated.
- Initial implementation scope established.
- 17 requirements: Board Access Isolation, Role-Based Permission Enforcement, Guest Access via Invite Link, Board Management, Column Management, Card Management, Drag-and-Drop Card Movement, Threaded Comments, Mention Notifications, Card Search, Board Analytics, Team Member Management, Authentication, Response Time, Concurrency Capacity, Technology Constraints, Version 1 Scope Boundary.
- Ordering used integer Positions (contiguous 0 to n-1). Notification polling interval was 15 seconds. Authentication was described as a generic session or token.
- Implementation status of V1 is not claimed; no V1 implementation was verified.

## V2 - 2026-11-25

### Changes

**Specification changes**
- Integrated the FSSE Module 4 assignment reference files (`backend-implementation.md`, `frontend-implementation.md`, `deliverables.md`, `grading-rubric.md`) with the V1 Sevy requirements. Sevy Teams, roles, Guests, and Invite_Links are kept.
- Rewrote `requirements.md` as 26 requirements: 17 V1 requirements kept under their V1 numbers (15 modified, 2 retained with cross-references) and 9 new requirements (18 to 26). No V1 requirement was removed.
- Replaced integer Positions with the FLOAT `order` strategy (ORDER_STEP 1024.0, MIN_GAP 1e-6, Rebalance, `ORDER BY order ASC`). The "contiguous 0 to n-1" invariants (V1 criteria 5.6, 6.5, 7.2) became "positive, unique, strictly increasing" invariants.
- Replaced the generic "session or token" (V1 13.1) with JWT: 60-minute expiry, identical 401 `Invalid credentials` for unknown email and wrong password, 401 on protected endpoints.
- Replaced the V1 rule "same error body for a non-existent Board and an inaccessible Board" (V1 1.5) with one rule: 403 `{"error": "Access denied"}` for both (OD-02).
- Changed notification polling from 15 seconds to 30 seconds (V1 9.5).
- Changed Card deletion to a soft delete (`deleted_at`); Column and Board deletion remain hard deletes with cascade.
- Moved the index requirement (V1 14.2) to the new Requirement 26. Moved the Frontend auth-state behavior to the new Requirement 21 and the response envelope and Blueprint structure to the new Requirement 20.
- Added Requirement 18 (Card Assignment and My Tasks), 19 (User Profile), 20 (API Conventions and Health Check), 21 (Frontend Pages, Authentication State, and Navigation), 22 (Frontend Error Handling), 23 (Responsive Layout), 24 (Card Completion Tracking), 25 (Shared UI Components and Modal Interaction), 26 (Data Storage and Integrity).
- Added the sections "Assumptions and Open Decisions" (OD-01 to OD-13, A-01 to A-05), Appendix A (route inventory), and Appendix B (V1-to-V2 ID mapping).
- Added a user `username` field at registration to support `@username` mentions (OD-05) and a personal Team created at registration (OD-06).
- Added the requirement that Frontend search sends a request after 300 ms of inactivity and no request for empty input.

**Design changes**
- No design file was edited in this revision. `design.md` is expected to change to match V2 (see Impact).

**Implementation changes**
- None. No application code, models, migrations, steering files, guideline files, or reference files were modified.

**Bug fixes**
- None.

**Breaking changes (relative to V1 requirements)**
- Integer Position fields are replaced by Float `order` fields.
- Notification polling interval changes from 15 s to 30 s.
- Non-existent and inaccessible Board-scoped IDs now return 403 with `{"error": "Access denied"}`.
- Card deletion is a soft delete.
- The route set grows to 32 routes, 4 beyond steering `product.md` PR-02 (28 routes). Per PR-02, a CHANGELOG entry is required before code for those routes is generated; this entry records the proposal (OD-07). The decision is pending.

### Reason
- The assignment reference files define mandatory endpoints, FLOAT ordering, My Tasks, Profile, JWT, response envelope, notification polling, search debounce, error handling, and responsive behavior that V1 did not contain or defined differently.
- V1 requirements that improve security, data integrity, or measurable NFRs and do not conflict with the assignment were kept.
- The user decided to keep the Sevy Team model and diverge from steering `product.md` (board_members table, 28-route lock, PR-03 matrix, G-03, G-04).

### Impact
- **Affected requirements:** 1 to 14 and 17 modified; 15 and 16 retained; 18 to 26 added.
- **Affected design components (to update in `design.md`):** Team, TeamMember, User (`username`), Board, Column (`order` Float, `is_done`), Card (`order` Float, `assignee_id`, `created_by_id`, `completed_at`, `deleted_at`), Comment (`parent_id`, `updated_at`, `is_deleted`), Notification (`comment_id`, `card_id`, `is_read`), InviteLink, ActivityEvent; the eight Blueprints; `ordering` utility; response helpers; Frontend pages, AuthContext, API_Client, Notification_Bell, Kanban_Board, Card_Detail_Modal, shared components; the traceability table.
- **Affected implementation tasks (to update in `tasks.md`):** tasks for ordering and Rebalance, soft delete, assignment and My Tasks, Profile, completion tracking, member and invite-link routes, Guest header handling, error handling mapping, 30-second polling, search debounce, responsive checks. `tasks.md` was not edited in this revision.
- **Pending decisions:** OD-01 to OD-13.

## V3 - 2026-11-25

### Changes

**Specification changes** (`requirements.md` only; no criterion was renumbered)
- Requirement 4, criterion 2: the personal-Team default for an omitted `team_id` is limited to `POST /api/boards` and applies to no other endpoint (OD-06 already names only `POST /api/boards`; unchanged).
- Requirement 6, criterion 7: a soft-deleted Card is also treated as non-existent for a direct request by Card ID. New criterion 14 states the response `403 {"error": "Access denied"}` for every Card-ID route (PATCH, DELETE, position, comments) and notes that the document has no `GET /api/cards/<id>` route. New criterion 15 applies the assignee rule to `POST /api/columns/<id>/cards` and `PATCH /api/cards/<id>`.
- Requirement 9, criterion 3: rephrased from an unconditional IF/THEN to a WHEN condition that applies after the Comment is stored.
- Requirement 11, criteria 5 and 7 and assumption A-02: analytics dates follow a both-or-neither rule. Neither provided: last 7 days (UTC). Only one provided: 400.
- Requirement 12, criteria 2, 3, and 9: a non-Admin requester receives 403 before the `email` lookup or the membership check. The 404 (unregistered email) and the 409 (already a member, well-formed request) apply to Admin requesters only. Criterion 9 now covers every non-Admin (Member or non-member).
- Requirement 13, new criterion 14: a valid, unexpired JWT that fails the Team membership or role check gets 403. 401 stays for a missing, invalid, or expired token.
- Requirement 18, criterion 2: a `assignee_id` UUID that is not an existing user returns the same `400 {"error": "Assignee must be a Team member"}` as an existing non-member.
- Requirement 1 (Validation Rules) and OD-02: wording "unregistered emails when adding a Team member" became "when an Admin adds a Team member", to stay consistent with Requirement 12 criterion 2.

**Clarifications already present and left unchanged**
- Requirement 11, criterion 4 (daily Activity_Event counts): it states only the content of the counts and no status code. The HTTP 200 stays in criterion 1.
- Requirement 4, criterion 2 and OD-06: the `POST /api/boards` scope was already named in criterion 1 and OD-06; only criterion 2 was made explicit.
- Requirement 1 criterion 2 and OD-02 already return 403 `Access denied` for a soft-deleted Card; Requirement 6 criterion 14 restates the rule for Card-ID routes without changing it.
- Requirement 13, criteria 8 and 13 (401 for a missing or invalid JWT) are unchanged.

**Design changes**
- None made. `design.md` is expected to change (see Impact).

**Implementation changes**
- None. No application code, steering, reference, `design.md`, or `tasks.md` file was modified.

**Bug fixes**
- None.

**Breaking changes**
- None to the route set (still 32 routes). Behavior now fixed where it was open: 403 before 404/409 for non-Admin member management, 400 for a single analytics date, 403 for a soft-deleted Card ID, 403 for a valid JWT that fails the membership or role check.

### Reason
- A requirements analysis found ambiguity in these criteria. The user answered the open questions and the answers are recorded as the new source of truth.

### Impact
- **Affected requirements:** 4, 6, 9, 11, 12, 13, 18 (plus OD-02, A-02, and the Requirement 1 Validation Rules wording).
- **Affected design components (to update in `design.md`):** boards service `create_board_service` (`team_id` default), Authorization_Service check order for the members routes (role check before email lookup and duplicate check), cards service and Card-ID route lookup for soft-deleted Cards (403), analytics `AnalyticsQuerySchema` (both-or-neither dates), notifications service (Mention parsing after Comment storage), assignee validation shared by cards create and update (non-existent user UUID), JWT and permission error mapping (401 vs 403), traceability table.
- **Affected implementation tasks (to update in `tasks.md`):** tasks for boards, members, cards, analytics, notifications, authentication, and the matching pytest cases (non-Admin 403 before 404/409, single-date 400, soft-deleted Card ID 403, non-existent assignee UUID 400, valid JWT without membership 403). `tasks.md` was not edited in this revision.
- **Pending decisions:** OD-01 to OD-13 (unchanged).

## V4 - 2026-11-25

### Changes

**Specification changes** (`requirements.md` only; no criterion was renumbered; the Introduction line "Version 2 (V2)" was left unchanged to keep the history unambiguous)
- Requirement 2, criterion 7: the 403 for a cross-Team Admin request now names Board, Column, Card, and Comment IDs, includes non-existent IDs and soft-deleted Cards, states the body `{"error": "Access denied"}`, and states that existence is not disclosed beyond that body (OD-02, Requirement 1 criterion 2).
- Requirement 3, criterion 3: cross-reference added; the criterion applies when the request carries no JWT. New criterion 9 (appended): when a valid JWT and a valid `X-Invite-Token` bound to the same Board are both present on `GET /api/boards/<id>` or `GET /api/cards/<id>/comments`, the JWT takes precedence, the Team role and permissions apply, and the invite token is ignored.
- Requirement 5, criterion 8 and Requirement 7, criterion 6: the 409 for an `order` equal to a sibling's `order` carries only the standard error envelope, with no suggested order, range, or remediation hint; the client computes a new `order`. The Requirement 5 criterion 8 edit is a consistency edit.
- Requirement 13, criterion 9: the exempt endpoints (`register`, `login`, `health`, and the Guest read endpoints) never require a JWT; `register`, `login`, and `health` are processed whether or not an `Authorization` header is present. The Guest read endpoints accept either a valid JWT or a valid `X-Invite-Token` and do not require a JWT when a valid token is present. The exemption list is unchanged.
- Requirement 18, criterion 7: the `assignee` value rule is scoped to `GET /api/cards` requests; it does not apply to any other request or to the `assignee_id` body field.
- Requirement 21, criterion 16 and Glossary (ApiError): when no HTTP response is received (network failure, timeout, CORS block), the API_Client throws an ApiError with `statusCode` 0. Requirement 22, criterion 5: that case shows the Toast "Something went wrong. Try again." like a status of 500 or higher.

**Clarifications already present and left unchanged**
- Requirement 4, criterion 6: the WHEN condition already limits the 200 response to a Member or Admin. Non-members are covered by Requirement 1 criterion 1 (403). No conflict with the Guest read path (Requirement 3 criterion 3).
- Appendix A (route inventory), Appendix B, Open Decisions, and Validation Rules tables: no inconsistency was introduced, so none was edited.

**Design changes**
- None made. `design.md` is expected to change (see Impact).

**Implementation changes**
- None. No application code, steering, reference, `design.md`, or `tasks.md` file was modified.

**Bug fixes**
- None.

**Breaking changes**
- None to the route set (still 32 routes). Behavior now fixed where it was open: JWT precedence over `X-Invite-Token`, a bodiless 409 hint rule, `statusCode` 0 for a missing HTTP response.

### Reason
- A requirements analysis found ambiguity in these criteria. The user answered the open questions and the answers are recorded as the new source of truth.

### Impact
- **Affected requirements:** 2, 3, 5, 7, 13, 18, 21, 22 (plus the Glossary entry for ApiError).
- **Affected design components (to update in `design.md`):** Authorization_Service (cross-Team 403 body for all Board-scoped IDs; JWT-over-invite-token resolution on the two Guest read endpoints), auth middleware (per-endpoint JWT-required flag, `Authorization` header ignored on register, login, and health), cards and columns services (409 body without hints), `GET /api/cards` query schema (`assignee` validation), `lib/apiClient.ts` and `lib/errors.ts` (`ApiError` with `statusCode` 0), `useErrorHandler` mapping (status 0 to the 500 toast), traceability table.
- **Affected implementation tasks (to update in `tasks.md`):** tasks for authorization and the Guest read endpoints, auth decorators, ordering conflict responses, the cards query schema, API_Client and error-handler hook, and the matching tests (cross-Team 403 for non-existent IDs, JWT plus invite token, exempt endpoints with and without `Authorization`, 409 body shape, `assignee=foo` 400, status 0 toast). `tasks.md` was not edited in this revision.
- **Pending decisions:** OD-01 to OD-13 (unchanged).

## V5 - 2026-11-25

### Changes

**Specification changes** (`requirements.md` only; no criterion was renumbered; the Introduction line "Version 2 (V2)" was left unchanged to keep the history unambiguous)
- Requirement 3: the access-resolution rule for the two Guest read endpoints (`GET /api/boards/<id>`, `GET /api/cards/<id>/comments`) is stated once as the six-row Access Resolution Table in the Validation Rules and as EARS criteria. Principle: an invite token can only add access, never reduce it; a JWT decides access only when its user is a Team member of the Board's Team, otherwise a valid invite token bound to the Board applies.
  - Criteria 3, 4, 5, 7, and 9 edited in place: 3 is row 2 (Guest read-only access, also for no, expired, or invalid JWT and for a valid JWT of a non-member); 4 is row 3 (404 for an invalid or revoked token); 5 is row 4 (403 `Access denied` for a token bound to another Board); 7 refers to criterion 4; 9 is row 1 (a Team member's JWT applies and any token is ignored, with no 404 or 403 caused by the token).
  - New criteria 10 (row 5: valid JWT of a non-member, no token, 403), 11 (row 6: no valid JWT and no token, 401), 12 (rows are evaluated in order, first match applies, expired or invalid JWT treated as absent, table takes precedence over Requirements 1, 2, and 13 on these endpoints), and 13 (`X-Invite-Token` is evaluated only on the two Guest read endpoints).
  - Validation Rules: added the principle, the table, the combination rules (expired or invalid JWT with an invalid or revoked token is row 3; with a token bound to another Board is row 4), the rule that an empty or malformed token is invalid, the rule that a non-existent Board or Card or a soft-deleted Card counts as having no bound Board (row 4, same 403 body as OD-02), the Frontend note that `/boards/<id>?invite=<token>` still forwards the JWT, and the rule that Guest 403 results on other endpoints apply to a request with a valid JWT while a request with no valid JWT gets 401. The bullet "A Guest holds no JWT" was replaced because a Guest may also carry a valid JWT of a non-member.
  - Criterion 8 (Frontend) unchanged.
- Requirement 1, criterion 1: the clause "without a valid Invite_Link" was replaced by an exception that points to rows 2 to 4 of the Access Resolution Table (a non-member with an invalid token on a Guest read endpoint gets 404, not 403). Criteria 2 to 6 and Validation Rules unchanged.
- Requirement 2, criterion 2: added that a Guest write request with no valid JWT gets 401 (Requirement 13 criterion 8). Permission table (Guest and Non-member columns) unchanged and consistent.
- Requirement 13, criteria 8, 9, and 14: criterion 8 defines "protected endpoint"; criterion 9 states that the Guest read endpoints are decided by the Access Resolution Table (row 6 gives 401, row 5 gives 403, row 2 needs no JWT); criterion 14 adds that on a Guest read endpoint the table decides and 401 applies only to row 6. Criteria 13 and the others unchanged.
- Requirement 21, criterion 11: added an exception so that an unauthenticated visit to `/boards/[id]` with the `invite` query parameter is served and not redirected to `/login`; without it criterion 11 contradicted Requirement 3 criterion 8.
- Open decision OD-12: default text now names the two Guest read endpoints, the resolution order, the principle, and the JWT forwarding on invite pages.
- Glossary: added "Access Resolution Table".

**Clarifications already present and left unchanged**
- Requirement 22 (Frontend error handling): the 401 redirect to `/login` does not conflict with rows 2 and 6. A Guest with an expired JWT cookie and a valid invite token gets 200 (row 2), so no 401 and no redirect occurs; a 401 on these endpoints occurs only in row 6, where the redirect is correct.
- Requirement 1 criteria 2 to 6, Requirement 2 permission table, Requirement 8 criterion 5, Appendix A, and Appendix B: not edited. Requirement 8 criterion 5 (401 without a valid JWT on any Comment endpoint) is overridden for `GET /api/cards/<id>/comments` by Requirement 3 criterion 12.

**Design changes**
- None made. `design.md` is expected to change (see Impact).

**Implementation changes**
- None. No application code, steering, reference, `design.md`, or `tasks.md` file was modified.

**Bug fixes**
- None.

**Breaking changes (relative to V4 requirements)**
- A Team member's request to a Guest read endpoint with an invalid, revoked, or other-Board `X-Invite-Token` is no longer rejected: the token is ignored (row 1). Under V4 criteria 4 and 5 this request got 404 or 403.
- A valid JWT of a non-member together with a valid token bound to the Board now gets Guest read-only access (row 2); V4 criterion 9 covered only a Team member's JWT with a token bound to the same Board.
- An expired or invalid JWT together with a valid bound token now gets Guest access (row 2).
- A request to a Guest read endpoint with no valid JWT and no token returns 401, and with a valid non-member JWT and no token returns 403 (rows 6 and 5).
- `X-Invite-Token` is ignored on every other endpoint, so criteria 4, 5, and 7 no longer apply to them.
- The route set is unchanged (32 routes).

### Reason
- The user resolved three gaps left open by V4: a signed-in non-member who opens an invite link, a request with no or expired credentials, and a JWT sent with a token bound to another Board. The user also added the case of a Team member who sends an invalid or revoked token.

### Impact
- **Affected requirements:** 1 (criterion 1), 2 (criterion 2), 3 (criteria 3, 4, 5, 7, 9 edited; 10 to 13 added; Validation Rules), 13 (criteria 8, 9, 14), 21 (criterion 11), OD-12, Glossary. Checked and unchanged: 22 and Appendices A and B.
- **Affected design components (to update in `design.md`):** Authorization_Service with a single access-resolver function that takes the JWT state, the Team membership of the user, and the `X-Invite-Token` state and returns one of the six rows; the boards and comments services and routes for the two Guest read endpoints; auth middleware (JWT-required flag false on the Guest read endpoints, `X-Invite-Token` read only there); Invite_Link lookup (valid, revoked, bound Board); Next.js middleware and the Board Detail page for `/boards/[id]?invite=<token>` (no redirect to `/login`, JWT and token both forwarded); the traceability table.
- **Affected implementation tasks (to update in `tasks.md`):** a task for the access-resolver function with a six-row table-driven test plus the combination cases (expired or invalid JWT with each token state, Team member with an invalid, revoked, or other-Board token, non-existent Board or Card with a valid token, empty token); tasks for the two Guest read routes, the auth decorators, the Frontend middleware exception, and the Frontend Board Detail invite handling; tests that a Guest write request without a JWT returns 401 and with a non-member JWT returns 403. `tasks.md` was not edited in this revision.
- **Pending decisions:** OD-01 to OD-13 (unchanged; OD-12 default text updated).

## V6 - 2026-11-26

**Prompt**: The user asked for the requirements to be analysed against the steering files, the guidelines, and the grading rubric, and then revised in place (no criterion renumbered). Decisions D1 to D3: D1 reverts OD-02 (404 `<Entity> not found` for non-existent Board-scoped IDs and soft-deleted Cards, 403 `Access denied` for existing resources the requester cannot access, existence evaluated first); D2 sets the criterion ID scheme `R<N>.<k>`; D3 fixes the Notification recipient field name as `user_id`. The analysis result was applied as the requirement-side fixes F1 to F11.

**Before** (V5):
- OD-02, Requirement 1 criteria 1 and 2 and Validation Rules, Requirement 2 criterion 7, Requirement 6 criteria 7 and 14, Requirement 3 Validation Rules (row 4 note), and the Glossary entry "Soft Delete": a non-existent Board-scoped ID and a soft-deleted Card returned 403 `{"error": "Access denied"}`.
- Introduction named the document Version 2 (V2). No criterion ID scheme. Error envelope: `{"error": "<non-empty string>"}` for every error. Login response had no `user`. Requirement 8 criterion 5 gave 401 on every Comment endpoint. `GET /api/cards` items had two different field lists (Requirement 10 criterion 4 and Requirement 18 criterion 5). Requirement 11 listed response keys without element shapes. Requirement 14 had no verification method. No "Routes and Pages" line in any requirement. Open decisions: OD-01 to OD-13.

**After** (V6):
- Gaps found: 20 requirement, guideline, and steering conflicts in the analysis; requirement-side fixes applied: 13 items (D1 to D3 and F1 to F10; F11 needs no edit), touching all 26 requirements (at least the new "Routes and Pages" line) plus the Introduction, Document Conventions, Glossary, OD-02, Appendix B, and 2 new open decisions.
- Non-existent Board-scoped IDs and soft-deleted Cards return 404 in the 8 places that had the 403 rule (OD-02, Requirement 1 criterion 2 and Validation Rules, Requirement 2 criterion 7, Requirement 3 Validation Rules, Requirement 6 criterion 14, the Glossary entry "Soft Delete", Appendix B); 4 criteria were appended (Requirement 1 criterion 7, Requirement 8 criterion 18, Requirement 19 criterion 9, Requirement 20 criterion 13). 26 of 26 requirements now have a "Routes and Pages" line. Open decisions: OD-01 to OD-15 (OD-14 and OD-15 added; none approved).

### Changes

**Specification changes** (`requirements.md`; no criterion was renumbered; new criteria are appended at the end of a list)
- OD-02 renamed "Access-denied and not-found response rule" and rewritten (D1). New default: for a Board-scoped ID in the URL path (Board, Column, Card, Comment, Invite_Link), non-existence or a soft-deleted Card gives 404 `{"error": "<Entity> not found"}`; an existing resource on a Board the requester cannot access gives 403 `{"error": "Access denied"}`; existence is evaluated first; permission failures stay 403; a Notification not owned by the requester stays 404 `{"error": "Not found"}`. Justification: matches steering TC-06 and the guideline exception catalog, with fewer special cases. A note records that V2 to V5 used 403 for non-existent IDs and V6 reverts it.
- Requirement 1: criteria 1 and 2 edited; new criterion 7 (evaluation order; 401 before existence on protected endpoints, existence before the Access Resolution Table on Guest read endpoints); Validation Rules rewritten.
- Requirement 2: criterion 7 edited (403 only for existing resources of another Team); note added under the permission table.
- Requirement 3: criterion 12 edited and the Validation Rules note that mapped a missing Board or Card to row 4 replaced (404 evaluated before the table); Invite_Link 404 rule for `DELETE .../invite-links/<invite_id>`; API-only note (F7, OD-14).
- Requirement 6: criteria 7 and 14 edited (soft-deleted Card is 404 `{"error": "Card not found"}` on every Card-ID route).
- Requirement 7: Validation Rules state 404 for a missing path Card ID and keep 400 for a body `column_id` that does not exist (criterion 4 unchanged).
- Requirement 8: criterion 5 edited (F3: `GET /api/cards/<id>/comments` is decided by the Access Resolution Table, 401 only in row 6); new criterion 18 (404 for a missing Card or Comment ID).
- Requirement 10: criterion 3 edited (403 for an existing inaccessible Board, 404 `Board not found` for a missing `board_id`, tagged Proposed); criterion 4 refers to the shared Card list item; Validation Rules add the `q` and `board_id` relation and the Card list item `id`, `title`, `column_id`, `column_name`, `board_id`, `board_name`, `assignee_id` (F4).
- Requirement 18: criterion 5 refers to the Card list item of Requirement 10 (F4).
- Requirement 11: Validation Rules add element shapes for `cards_per_column`, `completed_this_week`, `member_activity`, `activity_per_day`, `start_date`, `end_date`, tagged Proposed (F5).
- Requirement 12: Validation Rules add the 404-before-Admin-check note and the API-only note (F7, OD-14).
- Requirement 13: criterion 5 adds `user` (`id`, `name`, `username`, `email`) to the login response (F2).
- Requirement 14: Validation Rules add the verification method for the 300 ms target (F6); numbers unchanged.
- Requirement 19: new criterion 9 (AuthContext operation that replaces the stored user) (F2).
- Requirement 20: criterion 1 allows a field-keyed object `error` for a 400 validation failure; new criterion 13 (single cross-reference for every "validation error message" in the document); Validation Rules add error shapes, 405, and not-found bodies (F1).
- Requirement 21: criterion 8 stores the JWT and the `user` in AuthContext (F2).
- Requirement 22: criterion 4 shows the ApiError `message` (field messages joined as `field: message`, separated by "; ") (F1).
- Requirement 9: Validation Rules state that the recipient field is `user_id` (D3); criterion 6 unchanged.
- Introduction (F8): the "Version 2 (V2)" sentence replaced by a statement that the document is at V6, built from the V2 refinement of V1, with changes in `CHANGELOG.md`.
- Document Conventions (D2): criterion IDs `R<N>.<k>` added.
- Glossary: "Soft Delete" and "ApiError" updated.
- "Routes and Pages" line added under Related Areas of Requirements 1 to 26 (F9).
- Open decisions: OD-14 (API-only member and Invite_Link management; conflicts with steering `product.md` F-11) and OD-15 (Comments and Notifications of a soft-deleted Card; conflicts with guideline `database.md` DB-06) added (F7, F10). OD-01, OD-03 to OD-13 unchanged and not approved (F11).
- Appendix B: row for Requirement 1 updated.

**Clarifications already present and left unchanged**
- Requirement 7 criterion 4 (a body `column_id` that does not exist is 400), Requirement 1 criterion 5 (a removed Team member gets 403), Requirement 9 criterion 12 (Notification not owned: 404 `Not found`), and the Requirement 20 status-code list (405 was already listed). Requirements 12 and 18 did not cite the old rule and have no 403-for-missing-ID text.

**Design changes**
- None made. `design.md` is expected to change (see Impact).

**Implementation changes**
- None. No application code, steering, guideline, reference, `design.md`, or `tasks.md` file was modified.

**Bug fixes**
- None.

**Breaking changes (relative to V5 requirements)**
- Non-existent Board-scoped IDs (Board, Column, Card, Comment, Invite_Link) and soft-deleted Cards change from 403 `{"error": "Access denied"}` to 404 `{"error": "<Entity> not found"}`.
- The login response gains `user`.
- 400 validation errors may be field-keyed objects (`{"error": {"<field>": "<message>"}}`) instead of strings.
- A `board_id` query value on `GET /api/cards` that names a non-existent Board changes from 403 to 404 `{"error": "Board not found"}` (tagged Proposed).
- The route set is unchanged (32 routes).

### Reason
- The user decided to align the not-found rule with steering TC-06 and the guideline exception catalog (D1), to fix the criterion ID scheme for traceability (D2) and the Notification recipient field name (D3), and to apply the requirement-side fixes found in the gap analysis (F1 to F11).

### Impact
- **Affected requirements:** Introduction, Document Conventions, Glossary, OD-02, OD-14 and OD-15 (new), Appendix B, and Requirements 1, 2, 3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 18, 19, 20, 21, 22 (criteria or Validation Rules changed). Requirements 4, 5, 15, 16, 17, 23, 24, 25, and 26 changed only by the "Routes and Pages" line.
- **Guideline files that need sync:** `backend.md` BE-05, BE-07, BE-08, BE-09, BE-10 (404 `<Entity> not found` and 403 `Access denied`, evaluation order, field-keyed 400 body, login `user`); `database.md` DB-08, DB-09, DB-06 (DB-06 conflicts with OD-15: it physically removes the Comments and Notifications of a soft-deleted Card); `frontend.md` FE-19 (ApiError `message` and `fieldErrors`, 404 toast).
- **Steering files that need sync:** `tech.md` TC-12 (AuthContext stores the user), TC-13 (ApiError `fieldErrors`), TC-06 (400 object `error`); `product.md` PR-02 (route total of 32), PR-03 (404 before 403 for non-existent IDs), PR-05 (mention-only notifications, OD-04), PR-07 (title-only search, OD-09, and the Card list item), NFR-02 (Guest read endpoints without a JWT); `structure.md` ST-12 (criterion IDs `R<N>.<k>` instead of `REQ-`/`AC-`).
- **Affected design components (to update in `design.md`):** Authorization_Service existence-then-role order and the access resolver (404 before the six rows), `NotFoundError` per entity (`<Entity> not found`) and `AccessDeniedError`, error handlers and the response envelope (field-keyed 400 `error`), login response schema with `user`, `lib/apiClient.ts` and `lib/errors.ts` (`message` join, `fieldErrors`), `useErrorHandler`, AuthContext (`user` and an operation to replace the stored user), `GET /api/cards` Card list item schema and `board_id` handling, analytics response schemas, the traceability table keyed by `R<N>.<k>` with the "Routes and Pages" lines.
- **Affected implementation tasks (to update in `tasks.md`):** tasks for the exception and error-handler layer, Board, Column, Card, Comment, and Invite_Link lookups (404 then 403), the access resolver, login and AuthContext, `GET /api/cards`, analytics schemas, API_Client and error-handler hook, and the matching pytest and Jest cases (404 for every Board-scoped path ID, 403 for another Team's existing resource, soft-deleted Card 404 on all Card-ID routes, field-keyed 400, login `user`). `tasks.md` was not edited in this revision.
- **Pending decisions:** OD-01 to OD-15 (OD-02 rewritten; OD-14 and OD-15 new; none approved).

## V7 - 2026-11-26

**Prompt**: The user asked for a controlled consistency refinement of `requirements.md` (V6 to V7) that applies the decision contract in `specs/CONSISTENCY_AUDIT_REPORT.md` section 2 (findings 1 to 20 and refinements R1 to R7): preserve every valid requirement, criterion, and decision the contract does not change; do not renumber criteria; edit in place and append new criteria at the end of a list; keep the structure, EARS wording, `R<N>.<k>` IDs, and the [Proposed, OD-nn] convention; for `requirements.md` the editing step did not touch steering, guideline, reference, design, tasks, or code files. The same round then applied the contract to `database.md`, `backend.md`, `frontend.md`, `tech.md`, `structure.md` and `product.md` in separate steps (see Impact), and added `specs/CONSISTENCY_AUDIT_REPORT.md`.

**Before** (V6):
- Open decisions: 15 (OD-01 to OD-15) and 5 assumptions (A-01 to A-05), none resolved in a separate list; [Proposed, OD-nn] tags also pointed to OD-02, OD-03, OD-06, OD-09, OD-11, and OD-12.
- Guest read endpoints used a six-row Access Resolution Table in which an expired or invalid JWT was "treated as absent" and fell back to Guest access; the Frontend still forwarded the JWT on invite pages.
- 400 validation errors were a field-keyed object, and ApiError had an optional `fieldErrors`.
- Not-found bodies were per entity (`Card not found`, `Board not found`, and so on); the 403 body was `Access denied`.
- Notifications stored `user_id` and `card_id`; a Comment tombstone was a stored `is_deleted`; a Card soft delete left its Comments hidden by the 404 rule only (OD-15 open).
- Requirement 14 had a verification method but no repository script, no recorded environment, and no "not measured" status.
- Requirement 26 had 6 criteria; Requirement 13 gave no username normalization; 26 of 26 requirements used "Routes and Pages:".

**After** (V7):
- Conflicts resolved: 20 contract findings and 7 refinements (R1 to R7). Criteria edited in place: 54 (in Requirements 1, 2, 3, 4, 6, 8, 9, 10, 13, 18, 19, 20, 21, 22, 24, and 26); criteria appended: 14 (Requirement 3 criteria 14 and 15, Requirement 6 criterion 16, Requirement 8 criterion 19, Requirement 14 criteria 4 to 6, Requirement 21 criterion 17, Requirement 26 criteria 7 to 12); criteria renumbered: 0; requirements added or removed: 0 (still 26).
- Decisions: 9 resolved (OD-02, OD-03, OD-04, OD-06, OD-07, OD-09, OD-11, OD-12, OD-15) and 11 open with question, impact, options, recommended default, and reason unresolved (OD-01, OD-05, OD-08, OD-10, OD-13, OD-14, OD-16, OD-17, OD-18, OD-19, OD-20); 5 assumptions kept (A-01 to A-05). Tags remain only on criteria that depend on an open decision: 19 [Proposed, OD-nn] occurrences (OD-01, OD-05, OD-08, OD-13, OD-16, OD-17, OD-18, OD-19) and 1 [Inactive; deferred, OD-04] marker on Requirement 9 criterion 15.
- Access Resolution Table has 8 ordered steps (was 6 rows); an invalid, malformed, or expired JWT is always 401.
- 26 of 26 requirements carry a `Routes/Pages:` line; 8 are marked "cross-cutting" (Requirements 1, 2, 13, 14, 15, 16, 20) or "database" (Requirement 26).

### Changes

**Specification changes** (`requirements.md`; no criterion was renumbered)
- W1 Version and conventions: Introduction states V7 and that the contract applies where it differs from an earlier decision; Document Conventions add the `Routes/Pages:` rule and the [Inactive; deferred] marker; all 26 "Routes and Pages:" lines renamed "Routes/Pages:".
- W2 Access policy (findings 7 and 8): OD-02 rewritten as resolved; Generic_Denial_Body `{"error": "Not found or access denied"}` for 403 and 404 on Board, Column, Card, and Comment resources and for a soft-deleted Card; invalid or revoked Invite_Link token 404 `{"error": "Not found"}`; Requirement 1 criteria 1, 2, 5, 6, 7 and Validation Rules; Requirement 2 criterion 7 and the notes under the permission table; Requirement 3 criteria 1, 3 to 5, 7 to 12 edited, 14 and 15 appended, six-row table replaced by the eight-step table, purpose-specific access check, Guests cannot reach Search, Notifications, Analytics, My Tasks, Profile, or any write; Requirement 6 criteria 7 and 14; Requirement 7 Validation Rules; Requirement 8 criteria 5, 6, 18; Requirement 10 criterion 3; Requirement 12 Validation Rules; Requirement 13 criteria 9 and 14; Requirement 20 Validation Rules; Glossary ("Soft Delete", "Access Resolution Table", new "Generic_Denial_Body", "Guest_Read_Endpoint", "Guest_Mode").
- W3 Username (finding 2): Requirement 13 criteria 1 and 3 and Validation Rules (3 to 30 characters, lowercase normalization, case-insensitive uniqueness, 409); Requirement 9 criterion 1 lowercases the mentioned name; OD-05 stays open.
- W4 Notifications (findings 3 and 10): Requirement 9 criteria 6, 7, 13 and Validation Rules (`recipient_id`, `comment_id`, six pagination keys, `total_pages`, `unread_count`, item shape with derived `card_id` and `board_id`); OD-19 created.
- W5 Activity_Event (finding 4): Requirement 6 criterion 13 (one `card_deleted` event per successful soft delete, none for a rejected delete).
- W6 Comments (findings 5 and 20): Requirement 8 criteria 7, 10, 11, 19 and Validation Rules (`deleted_at` tombstone, derived `is_deleted`); Requirement 6 criterion 16 (Card soft delete keeps Comments); OD-03 and OD-15 resolved; Glossary "Tombstone".
- W7 Database outcomes (findings 6 and 16): Requirement 26 criteria 2 to 4 edited and 7 to 12 appended; Requirement 4 criterion 2 and Requirement 13 criterion 2 (personal Team, one transaction); OD-06 resolved.
- W8 Error format and AuthContext (findings 11, 14, 15): Requirement 20 criteria 1 and 13 and Validation Rules (single string, deterministic 400 format); Glossary "ApiError" (`statusCode`, `message` only) and "AuthContext" (`updateUser`); Requirement 22 criterion 4; Requirement 13 criterion 5; Requirement 19 criteria 1, 2, 8, 9; Requirement 21 criteria 11, 16, 17 (Guest_Mode sends only `X-Invite-Token`); OD-16 and OD-18 created.
- W9 Search (finding 12): Requirement 10 criterion 3 and Validation Rules (title only, `board_id` verified, OD-09 resolved).
- W10 Request fields: Requirement 11, 12, 3, and 8 Validation Rules state analytics dates, member role update, Invite_Link create, and Comment create fields.
- W11 Limits and shapes (finding 1, R1): Requirements 4, 5, 6 already state 100, 100, 200, and 5000 and no 255; shapes added for the Board detail nested Card (Requirement 4), the Card list item, Search result item, and My Tasks item (Requirement 10), and the Notification item (Requirement 9); unsourced shapes tagged [Proposed].
- W12 Comment read access (R2): Requirement 8 criteria 5, 7, and 19.
- W13 Performance (R3): Requirement 14 criteria 4 to 6 and Validation Rules (repeatable load-test script, API-server measurement, 10-minute window, recorded environment, current configuration from `tech.md` TC-20, status "not measured").
- W14 Decision cleanup (R5): the section is split into Resolved decisions, Open Decisions, and Assumptions; OD-04, OD-07, OD-09, OD-11, OD-12 resolved; OD-17 and OD-20 created; tags removed from criteria whose decision is resolved (Requirement 4 criterion 2, Requirement 8 criterion 11, Requirement 10 criterion 3, Requirement 13 criterion 2, Requirement 24 criterion 1, and others).
- W15 API-only management (R6): Requirement 3 and Requirement 12 Validation Rules and OD-14 state that Invite_Link and Team member management have no Frontend screen in V1.
- W16 Appendices: Appendix A unchanged (32 routes); Appendix B row for Requirement 1 updated and a V7 note added.

**Clarifications already present and left unchanged**
- Requirements 5 and 7 criteria (409 on equal `order`, rebalance, 400 for a non-existent body `column_id`), Requirement 15, Requirement 17, Requirements 23 and 25 (other than the `Routes/Pages:` label), and Appendix A.

**Design changes**
- None made. `design.md` does not exist and is to be written to match V7 (see Impact).

**Implementation changes**
- None. No application code, migrations, `design.md`, or `tasks.md` was created or modified. Guideline and steering files were edited in this same round (see Impact); they are documentation, not implementation.

**Bug fixes**
- None.

**Breaking changes (relative to V6 requirements)**
- 400 validation errors become a single string; the V6 field-keyed object and the ApiError `fieldErrors` are removed.
- An expired, invalid, or malformed JWT no longer falls back to Guest access; the request is answered 401 (step 1).
- Notification fields are `recipient_id` and `comment_id`; `user_id` and `card_id` are no longer stored.
- 403 and 404 bodies for Board, Column, Card, and Comment resources are the single Generic_Denial_Body; the per-entity V6 bodies are removed.
- A Card soft delete retains its Comments; Comment delete sets `deleted_at`, and `is_deleted` is derived.
- Guest mode omits the JWT and sends only `X-Invite-Token`.
- The route set is unchanged (32 routes).

### Reason
- The user asked for the contract of the consistency audit (20 findings and 7 refinements) to be applied to the requirements so that requirements, steering, and guidelines can be brought to one set of names, bodies, tables, and shapes.

### Impact
- **Affected requirements:** Introduction, Document Conventions, Glossary, the decisions section, Appendix B, and Requirements 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 18, 19, 20, 21, 22, 24, and 26 (criteria or Validation Rules changed); the `Routes/Pages:` label changed in all 26.
- **Guideline and steering files changed in the same V7 round (details and verification status in `specs/CONSISTENCY_AUDIT_REPORT.md`):** `database.md` (username, teams `is_personal` and `owner_id`, `recipient_id` and `comment_id`, Comment `deleted_at`, partial unique `order` indexes, DB-06 Card soft delete); `backend.md` (access decorator and eight-step table, Generic_Denial_Body, 400 string, Notification pagination, request shapes); `frontend.md` (ApiError without `fieldErrors`, Guest_Mode, `updateUser`); `tech.md` (TC-06 error shape, TC-12 AuthContext, TC-13 ApiError, TC-20 worker configuration); `structure.md` (ST-12 ID scheme); `product.md` (Team ownership, mention-only notifications, title-only search, route inventory owned by Appendix A).
- **Design and tasks:** `design.md` and `tasks.md` do not exist and are to be written to match V7.
- **Pending decisions:** OD-01, OD-05, OD-08, OD-10, OD-13, OD-14, OD-16, OD-17, OD-18, OD-19, OD-20 (none approved).

## V8 - 2026-11-27

**Prompt**: The user approved the recommended defaults of the 11 open decisions OD-01, OD-05, OD-08, OD-10, OD-13, OD-14, OD-16, OD-17, OD-18, OD-19, and OD-20, and asked for them to be recorded as V8 in `requirements.md` and this changelog only. No steering, guideline, reference, design, tasks, code, or audit-report file was edited.

**Before** (V7):
- Open decisions: 11 (OD-01, OD-05, OD-08, OD-10, OD-13, OD-14, OD-16, OD-17, OD-18, OD-19, OD-20); resolved decisions: 9 (OD-02, OD-03, OD-04, OD-06, OD-07, OD-09, OD-11, OD-12, OD-15).
- `[Proposed, OD-nn]` tags: 19 occurrences (17 in criteria and Validation Rules, 2 in the Glossary entries Guest_Mode and Generic_Denial_Body).
- The decisions section said open decisions were not approved; OD-02 and OD-12 described OD-17 and OD-16 as open.

**After** (V8):
- Open decisions: 0 (the "Open Decisions" part states "None"); resolved decisions: 20 (OD-01 to OD-20, each listed once).
- `[Proposed, OD-nn]` tags: 0 (the only remaining occurrence of the text `[Proposed, OD-nn]` is the explanatory sentence in Document Conventions and in the V8 note of Appendix B). `[Proposed, A-nn]` tags: 4 (A-02 in Requirement 11 criterion 5, A-05 in Requirement 9 criterion 5, and the two mentions in Document Conventions); the `[Inactive; deferred, OD-04]` marker on Requirement 9 criterion 15 is kept.
- Criteria added, removed, or renumbered: 0. Requirements: 26.

### Changes

**Specification changes** (`requirements.md`)
- Introduction: "currently at Version 7 (V7)" became V8, with a sentence that V8 records the user's approval of the 11 decisions.
- Decisions section: the 11 decisions moved to "Resolved decisions" in OD number order, each with the decision, "Alternatives considered", and `*Source*: user approval of the recommended default (V8)`. The "Open Decisions" part is replaced by one line stating that none is open. The intro paragraph of the section was rewritten to match. Assumptions A-01 to A-05 are unchanged. OD-02 and OD-12 no longer call OD-17 and OD-16 open.
- Criteria tags: `[Proposed, OD-nn]` removed from criteria and Validation Rules of Requirements 1, 2, 3, 5, 7, 9, 13, 20, and 21 and from the Glossary entries Guest_Mode and Generic_Denial_Body. Criterion text and IDs are unchanged.
- Document Conventions: the tag bullet now says OD tags no longer occur and that `[Proposed, A-nn]` and `[Inactive; deferred, OD-04]` remain; a new bullet defines the bare **[Proposed]** label (response shapes of Requirements 4, 9, 10, and 11 that no source defines; not separately approved, design.md may refine them). Those labels are kept.
- Appendix B: a V8 note was added. Requirement 9 criterion 15 stays inactive (OD-04).

**Design changes**
- None. `design.md` does not exist.

**Implementation changes**
- None.

**Bug fixes**
- None.

**Breaking changes**
- None. The decisions were already the behavior stated in V7; only their status changed.

### Reason
- The user approved all 11 recommended defaults.

### Impact
- **Affected requirements:** Introduction, Document Conventions, Glossary (Guest_Mode, Generic_Denial_Body), the decisions section, Appendix B, and the tags in Requirements 1, 2, 3, 5, 7, 9, 13, 20, and 21. Requirements 4, 6, 12, 19, 22, and 24 were checked; their text states no open or pending status and is unchanged.
- **Design and tasks:** `design.md` and `tasks.md` do not exist; they are to be written to V8 with the bare **[Proposed]** shapes treated as design choices.
- **Guideline and steering lines to synchronise later (not edited in this round):**
  - `.kiro/steering/product.md` line 36: "Two of its cells are not yet approved: Column rename, reorder and delete by Admins only (OD-01), and Members deleting only their own Cards (OD-08)". Both are approved.
  - `.kiro/steering/product.md` line 87: "The Admin-only Column actions and the own-Cards-only delete for Members are proposals (requirements.md OD-01, OD-08)". Both are approved.
  - `guidelines/frontend.md` line 421: "(requirements.md OD-16 default)". OD-16 is now an approved decision, not a default.
  - Lines that cite these ODs without calling them open or proposed need no wording change: `guidelines/backend.md` 113, `guidelines/frontend.md` 254 and 439, `.kiro/steering/product.md` 54 and 182, `.kiro/steering/structure.md` 131.
- **Pending decisions:** none.

## V9 - 2026-11-27
**Prompt**: The user asked for Requirements 27 (Deployment and Environment), 28 (Automated Testing), and 29 (Repository and Documentation) to be added to `requirements.md`, aligned to what was already approved: no new open decision, no new assumption, no `[Proposed` tag, and every number, name, path, status code, and process rule taken from the current requirements, the steering files, the guidelines, or the user text. Only `requirements.md` and this changelog were edited.
**Before** (V8):
- Requirements: 26. Acceptance criteria: 281. Routes/Pages lines: 26. Open decisions: 0. New OD or A entries: 0.
- No requirement stated deployment, the test suite, or the repository and documentation deliverables, and no table linked criteria to the grading rubric or the deliverables.
**After** (V9):
- Requirements: 29. Acceptance criteria: 307 (+26: 9 in Requirement 27, 8 in Requirement 28, 9 in Requirement 29). Routes/Pages lines: 29. Open decisions: 0. New OD or A entries: 0. Routes: 32 (Appendix A unchanged).
- Each of Requirements 27 to 29 has a "Rubric traceability" table that maps every criterion to a checklist item of `.kiro/references/grading-rubric.md` or a deliverable of `.kiro/references/deliverables.md`, or to "none in the rubric" with the approved rule.
### Changes
**Specification changes** (`requirements.md`)
- Introduction: states that V9 adds Requirements 27 to 29 and that they are new in V9; no other sentence changed.
- Requirements 27 (9 criteria), 28 (8 criteria), and 29 (9 criteria) added after Requirement 26 and before Appendix A, each with Priority Mandatory, Source Assignment, User Story, Acceptance Criteria, Validation Rules, Related Areas, and a `Routes/Pages:` line.
- Appendix B: one V9 note added (Requirements 27 to 29 have no V1 predecessor).
- Requirement 17 and Appendix A checked: no statement contradicts the new requirements; both unchanged.
- Alignment of the user text to approved rules (differences):
  - Requirement 27: the health body and status are referenced to Requirement 20 criterion 7 and the 2000 ms limit to Requirement 14 criterion 3, instead of being repeated; the envelope to Requirement 20 criterion 1; the CORS rule is kept with Requirement 20 criterion 10; "desktop and mobile width" is stated as the 375 px, 768 px, and 1280 px of Requirement 23; the `auth` Blueprint request is the login request; the Gunicorn worker class and count and the plans are not stated and refer to Requirement 14 criterion 5; no URL and no achieved status is stated.
  - Requirement 28: "the debounce hook" is `useDebouncedValue`, and the drag and notification hooks are named `useDragAndDrop` and `useNotifications`; "each test creates its own user" follows steering `tech.md` TC-19 (through the API, unique email and unique username, OD-05); the eight Kanban steps refer to Requirement 7 criterion 15 and steering `tech.md` TG-02; the unrun status is "not run". No coverage threshold, mobile project rule, or optional Guest scenario is added.
  - Requirement 29: the CHANGELOG labels are Prompt, Before, and After (steering `tech.md` TC-21), where the user text names Before and After only; the criterion IDs are `R<N>.<k>`; the violation report is `guidelines/VIOLATIONS.md` with `### V-nn` entries, each with guideline ID, file and line, what the AI produced, and the fix; the guideline IDs are `FE-nn`, `BE-nn`, and `DB-nn`; `.gitignore` also lists `.venv/` and `venv/` (steering `structure.md` ST-13); the commit prefixes are the seven of steering `tech.md` TC-22, where the user text lists six areas; the project brief location stays "`README.md` or `/specs`".
  - Rubric items without a criterion in the user text and therefore without a criterion in V9: `design.md` lists register, login, and a Card model with a Float `order` column (kept in Requirement 29 only through the mapping of criterion 2 of the user text); every requirement has an acceptance criterion; the live-app demonstration of comments, search, and the bell with an unread count (Rubric, Complete Implementation); the Card model fields and the shared components rubric items, which Requirements 6, 25, and 26 already cover.
**Design changes**
- None.
**Implementation changes**
- None.
**Bug fixes**
- None.
**Breaking changes**
- None.
### Reason
- The user wanted the assignment's deployment, testing, and repository deliverables stated as requirements that can be traced to the grading rubric, without any new decision or assumption.
### Impact
- **Affected requirements:** Introduction, Requirements 27 to 29, Appendix B.
- **design.md and tasks.md:** neither exists. `design.md` must map R27.1 to R27.9, R28.1 to R28.8, and R29.1 to R29.9 to routes, pages, or deliverables; `tasks.md` must contain deployment, test, and documentation tasks.
- **Steering and guidelines:** no approved rule found that the new requirements contradict. Steering `tech.md` TC-17 (coverage thresholds) and TC-19 (optional fifth Guest scenario, mobile project for `pages.spec.ts`) hold rules that Requirement 28 does not restate; they are not changed.
- **Not yet existing in the repository (facts, not requirements):** no `Procfile`, no `.env.example`, no `README.md`, no `guidelines/VIOLATIONS.md`, no `design.md` or `tasks.md`, no `/specs` copy of the four files, no deployment, and no test suite. The CHANGELOG entries V2 to V5 lack the labels Prompt, Before, and After in the form of steering `tech.md` TC-21. The repository has one commit, `initial commit`, without a phase prefix. No criterion of Requirements 27 to 29 is claimed as met.
- **Pending decisions:** none.