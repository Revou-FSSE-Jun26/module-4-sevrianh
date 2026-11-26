---
inclusion: always
---

# Sevy — Product Steering

Tells Kiro **what** Sevy is, **who** it serves, and **what is in or out of scope**.
Every rule has four parts (Rule, Rationale, Example, Verify). The Verify part names a test, a count, or a script that can check the rule; if a rule cannot be verified, it is not a rule.

**What this file owns:** product purpose, users and roles, core features, scope and exclusions, product invariants, business goals, non-functional targets, and brief gaps resolved.
**What this file does not own:** the acceptance criteria, permission table, route inventory and error texts (`.kiro/specs/task-management-app/requirements.md`, the source of truth for product behavior), backend rules (`guidelines/backend.md`), database rules (`guidelines/database.md`), frontend rules (`guidelines/frontend.md`), tools, deployment and process (`tech.md`), repository layout (`structure.md`). Where a rule needs one of these, a reference points to the owner and the text is not repeated here.

IDs: `PR-xx` product rules · `NFR-xx` non-functional requirements · `BG-xx` business goals · `G-xx` brief gaps resolved here · `F-xx` features · `R<N>.<k>` acceptance criterion k of Requirement N in `requirements.md`.

Status: no application code, design.md or tasks.md exists yet. None of the Verify checks in this file has been run.

---

## 1. Product Purpose

Sevy is a Trello-like task management web application. A **Team** owns **Boards**. Team members organise work on a Board as **Columns** and **Cards**, move Cards between Columns with drag-and-drop, discuss Cards in threaded Comments, are notified when they are mentioned, and track the Cards assigned to them. Team Admins additionally manage Team members and Invite Links and monitor Board activity through analytics. An outsider can view one Board read-only through an Invite Link.

Sevy ships as two deployed apps, an API and a web frontend (stack, hosting and tooling are in `tech.md`). It is built through a reviewed AI-driven workflow (`tech.md` TC-21). Functionality and design should feel similar to CaliStore, Noel's Fake Store, or the Pet Store API (clean, demo-able, API-first).

## 2. Users and Roles

Every registered user belongs to at least one Team (the personal Team, PR-10). Roles are held at Team level and apply to every Board of that Team. The assignment's wording maps to Sevy's roles as shown in the last column (requirements.md, Assignment Terminology Mapping).

| Role | Who | Summary | Assignment term |
|---|---|---|---|
| Team Admin | A Team member with the role `admin` (the owner of a personal Team is its Admin) | Everything a Team Member can do, plus: create Boards in the Team, rename and delete Boards, rename, reorder and delete Columns, manage Team members, manage Invite Links, delete any Card, view analytics | board administrator |
| Team Member | A Team member with the role `member` | Creates Columns, creates, edits, assigns and moves Cards, deletes own Cards, comments, tracks own assigned tasks | board member |
| Guest | A visitor who holds a valid Invite Link for one Board | Reads that Board and its Comments only; no JWT is needed; never writes | — |
| Non-member | An authenticated user who is not in the Team and holds no valid Invite Link | No access to the Board's data | — |

The authoritative permission table is `requirements.md` Requirement 2. Two of its cells follow decisions approved by the user in requirements.md V8: Column rename, reorder and delete by Admins only (OD-01), and Members deleting only their own Cards (OD-08); see PR-03.

## 3. Core Features (the complete in-scope list)

Anything not listed here or in `requirements.md` is out of scope (section 8).

| ID | Feature | Scope | Main screens |
|---|---|---|---|
| F-01 | Authentication | Register, log in, JWT with expiry, protected routes, log out (Requirements 13, 21) | `/register`, `/login`, `AuthContext` |
| F-02 | Boards | Create, list, view, rename and delete Boards owned by a Team (Requirement 4) | `/` (Dashboard), `/boards/[id]` |
| F-03 | Columns | Add, rename, delete and reorder Columns with FLOAT order; a Column can be marked as a done column (Requirements 5, 24). A Column reorder screen is not required in V1 (requirements.md A-03) | `/boards/[id]` |
| F-04 | Cards | Create, edit, delete and move Cards with FLOAT order; optimistic drag-and-drop with rollback (Requirements 6, 7) | `/boards/[id]`, `useDragAndDrop` |
| F-05 | Comments | Threaded replies; add, list, edit and delete by the author (Requirement 8) | `CardDetailModal`, `CommentList` |
| F-06 | Notifications | Notification when a user is mentioned in a Comment; paginated list, mark read, bell with unread count, 30-second polling (Requirement 9) | `NotificationBell`, `useNotifications` |
| F-07 | Analytics | Cards per Column, Cards completed this week, member activity, activity over time; Admin only (Requirement 11) | Admin-only panel on `/boards/[id]` |
| F-08 | Profile | View and update name and email (Requirement 19) | `/profile` |
| F-09 | My Tasks | Cards assigned to the signed-in user, grouped by Board (Requirement 18) | `/my-tasks` |
| F-10 | Card search | Card title, across every accessible Board or one chosen Board, 300 ms debounce (Requirement 10) | Search input on `/boards/[id]` |
| F-11 | Team member management and Invite Links | An Admin adds and removes Team members, changes roles, creates and revokes Invite Links. API-only in V1: no member panel and no invite screen (Requirements 3, 12; requirements.md OD-14) | — (no screen) |
| F-12 | Health check | Public check used to verify a deployment (Requirement 20) | — (no screen) |
| F-13 | Guest read-only view | A Guest opens one Board through an Invite Link and sees Columns, Cards and Comments with no edit controls (Requirements 3, 21) | `/boards/[id]?invite=<token>` |

## 4. Business Goals (measurable)

| ID | Goal | Measure |
|---|---|---|
| BG-01 | The core journey works on production | The 8-step Kanban Playwright journey (`tech.md` TG-02) passes on the live Vercel URL in 3 consecutive runs with 0 failures and 0 retries |
| BG-02 | Both apps are public and healthy | The health check answers 200 in ≤ 2 s (Requirement 14 criterion 3); all 7 screens (Register, Login, Dashboard, Board Detail, Card Detail Modal, My Tasks, Profile) render on the live URL |
| BG-03 | Drag-and-drop is trustworthy | A card moved to another column is still in that column after page reload in 100% of E2E runs |
| BG-04 | Specs are traceable | 100% of requirements have ≥ 1 numbered acceptance criterion `R<N>.<k>`; 100% of criterion IDs appear in the traceability table of `design.md` and in `tasks.md`; every requirement carries a `Routes/Pages:` line, and 100% of routes and pages have a task |
| BG-05 | AI output is critically reviewed | `specs/CHANGELOG.md` has ≥ 5 refinement entries (Prompt, Before and After each); the violation report lists ≥ 3 violations (guideline and fix each) (`tech.md` TC-21) |

---

## 5. Product Rules

### PR-01 — Every feature traces to a requirement
- **Rule:** Every API route and every frontend page maps to a requirement (`Requirement <N>`) that has ≥ 1 numbered acceptance criterion, identified as `R<N>.<k>` (Requirement N, criterion k). Kiro must not generate a route or page that no `R<N>.<k>` criterion covers.
- **Rationale:** The brief grades requirement → design → task → file traceability; untraceable code is unreviewable.
- **Example:** `POST /api/columns/<id>/cards` → `R6.1` (a Card is created at the end of the Column) → Requirement 6 → task `T-14` (example ID).
- **Verify:** The traceability table in `design.md` has 0 routes or pages without an `R<N>.<k>` criterion ID, and `grep -c "^### Requirement [0-9]*:" .kiro/specs/task-management-app/requirements.md` equals the number of requirement blocks that contain a numbered criterion under `#### Acceptance Criteria`. Not run: `design.md` does not exist yet.

### PR-02 — Scope lock to the route inventory
- **Rule:** The API exposes exactly the routes in `requirements.md` Appendix A. Any other route or feature, or anything listed in section 8, needs a `CHANGELOG.md` entry **before** code is generated (requirements.md OD-07, Requirement 17 criterion 4).
- **Rationale:** AI agents add "helpful" endpoints; every extra route is untested surface area.
- **Example:** Kiro proposing `POST /api/cards/<id>/labels` is rejected and logged as a violation.
- **Verify:** A script compares the method-and-path pairs of `flask routes` (excluding `static`, path parameter names normalised) with Appendix A; the two sets are equal and each route appears in the route table of `design.md`. Not run: no application code exists yet.

### PR-03 — Role permissions are enforced and tested
- **Rule:** Permissions follow the roles of section 2; the authoritative table is `requirements.md` Requirement 2 and is not copied here. Product invariants:
  - A Team Admin can do everything a Team Member can do, and a Team Member everything a Guest can do (role monotonicity, R2.11).
  - A Team Member who lacks the role for an action is refused with 403, never 200 (R2.3, R2.5, R2.9). The Admin-only Column actions and the own-Cards-only delete for Members are approved decisions (requirements.md OD-01, OD-08, V8).
  - A request without a valid token is answered 401 (R13.8), a resource that does not exist 404 (R1.2), and an authenticated user without Team access 403 (R1.1).
  - A non-member learns no Board data, including through search, My Tasks and analytics (R1.4; see Requirement 1 for the response texts).
  - A Guest never writes (R2.2) and never reaches search, notifications, analytics, My Tasks or the profile (R3.14).
  - Only the author edits or deletes a Comment, including when the requester is an Admin (R2.8).
  - Permissions are enforced by the API independently of the controls the frontend shows (R2.1).
- **Rationale:** The brief separates "manage and collaborate" (Team Members) from "oversee and monitor" (Team Admins).
- **Example:** A Team Member requesting a Board's analytics is refused with 403 and no analytics data.
- **Verify:** The test suite contains ≥ 1 pytest per allow or deny cell of the Requirement 2 table for each role column; `pytest -v -k permission` passes. The number of tests follows from the table and is not fixed here. Not run: no tests exist yet.

### PR-04 — "Completed" has one definition
- **Rule:** A Column can be marked as a done column (Requirement 24). A Card that is moved into a done column, or created in one, is completed from that moment. A Card that is moved from a done column into a non-done column stops being completed. "Completed this week" counts non-deleted completed Cards whose completion time is on or after Monday 00:00 UTC of the current ISO week.
- **Rationale:** The brief asks for "cards completed this week" but never defines "completed"; a name-based guess ("Done") is fragile.
- **Example:** Moving a Card into a done column on Wednesday makes it count in that week's analytics; moving it back removes it.
- **Verify:** pytest cases for (a) move into a done column, (b) move out of a done column, (c) completed on the previous Sunday not counted, (d) soft-deleted Card not counted all pass (R24.2, R24.4, R24.8, R24.7).

### PR-05 — Notifications are for mentions only
- **Rule:** A user is notified when another Team member mentions them (`@username`) in a Comment on a Board of the shared Team. No user is notified of their own action. A user gets at most one notification per mentioned Comment, however often the Comment mentions them. Other triggers are deferred (R9.15, requirements.md OD-04). A notification list is paginated and reports `page`, `per_page`, `total`, `total_pages` and `unread_count` (Requirement 9).
- **Rationale:** An open-ended "notify on important things" leads to inconsistent generation and untestable behavior.
- **Example:** Member A writes "@bob please review" on a Card; Bob gets one notification and A gets none. A mention of a username that is not in the Team creates none.
- **Verify:** pytest asserts the exact notification count for (a) a single mention (1), (b) a repeated mention in one Comment (1), (c) a self-mention (0), (d) a username outside the Team (0) (R9.1 to R9.4); a list request returns ≤ `per_page` items together with the five pagination fields (R9.7).

### PR-06 — Assignment and My Tasks
- **Rule:** A Card has at most one assignee, who must be a member of the Team that owns the Card's Board; any other assignee is rejected with 400 (R18.2). `/my-tasks` lists the signed-in user's non-deleted assigned Cards, grouped by Board name (R18.5, R18.9, R18.10).
- **Rationale:** "Track their assigned tasks" requires an assignee concept that the brief implies but does not model.
- **Example:** Assigning a Card to a user outside the Team is rejected with 400 and the Card keeps its previous assignee.
- **Verify:** pytest for assign to a Team member (success), assign to a non-member (400), and the assignee=me list returning only the requester's own non-deleted Cards (Requirement 18); a frontend test shows the assigned Card under its Board heading on `/my-tasks`.

### PR-07 — Card search behavior
- **Rule:** Search matches the Card title only, ignoring letter case. A term alone searches every Board the user can access; an optional Board narrows the search, and a Board the user cannot access is refused. A blank, whitespace-only or over-long term is rejected with 400. Results exclude soft-deleted Cards and Cards on inaccessible Boards. The frontend sends a request only after 300 ms without typing (Requirement 10).
- **Rationale:** Search is a graded demo step but has no endpoint in the brief.
- **Example:** The term `DEPLOY` finds a Card titled "Deploy to Railway".
- **Verify:** pytest cases for case-insensitivity, blank term (400), cross-Board isolation, and soft-deleted exclusion pass (R10.1, R10.5, R10.6); a frontend test asserts one request after 300 ms of silence and none while the input is empty (R10.10, R10.11).

### PR-08 — Delete semantics
- **Rule:** Deleting a Card is a soft delete: the Card and its Comments are kept but hidden from every read, search, My Tasks result and analytics count (R6.7, R6.16). Deleting a Comment keeps its row: a Comment with replies stays visible as an empty tombstone, a Comment without replies is hidden (R8.10, R8.11). Deleting a Column or a Board is permanent and removes its contents (R5.10, R4.9). Every delete returns the id of the deleted item (R20.5).
- **Rationale:** The brief requires a soft delete for Cards; other entities do not need it, and mixed semantics must be explicit.
- **Example:** After deleting Card X, the Board view omits X and a request for X answers 404, while its Comments still exist.
- **Verify:** pytest asserts that a soft-deleted Card is absent from the Board, search, My Tasks and analytics responses and that its Comments still exist; a Column delete removes its Cards, and a Board delete removes its Columns, Cards and Comments.

### PR-09 — Guest access through an Invite Link
- **Rule:** An Invite Link gives read-only access to one Board and its Comments. The link is unguessable (R3.2), scoped to one Board (R3.5), revocable (R3.6, R3.7), and never extends access to anything else (R3.14). A Team member's own role is never reduced by a link (R3.9). An invalid, malformed or expired JWT is never accepted as a Guest, even when a valid link is present (R3.12, see the Access Resolution Table in Requirement 3).
- **Rationale:** Outsiders need to see progress without joining the Team; the access must stay narrow and revocable.
- **Example:** After an Admin revokes a link, the next request that uses it gets no Board data.
- **Verify:** One pytest per step of the Access Resolution Table of Requirement 3 (table-driven); a revoked-link test; a test that a link bound to Board A gives no access to Board B; a test that a Guest write attempt changes no data.

### PR-10 — Personal Team
- **Rule:** Registration creates the user, a personal Team and the user's Admin membership in it, as one all-or-nothing step (R13.2). A Board created without choosing a Team belongs to the requester's personal Team (R4.2).
- **Rationale:** Boards are owned by Teams, so a new user needs a Team before the first Board can exist.
- **Example:** A new user registers and creates a Board without naming a Team; the Board belongs to the user's personal Team and the user is its Admin.
- **Verify:** pytest asserts that registration creates exactly one user, one personal Team and one Admin membership, that a failed registration leaves none of them, and that a Board created without a Team lands in the personal Team.

---

## 6. Non-Functional Requirements

### NFR-01 — Performance
- **Rule:** Target: the 95th percentile response time is ≤ 300 ms while 200 users are concurrently active on one Board of 5 Columns and 50 Cards, measured at the API server over a 10-minute window with the repeatable load-test method of `tech.md` TC-23 (Requirement 14 criteria 1, 4, 5; Requirement 15). This is a target, not a result: its status is "not measured" until a recorded run exists, and a run above 300 ms is recorded as "not met" (R14.6). Product expectation: a Board loads its Columns and Cards in at most 3 SQL queries (R14.2).
- **Rationale:** The Kanban board is the primary screen and slowness is felt immediately; a target without a method and a record cannot be checked.
- **Example:** A Board load that runs one query per Column breaks the 3-query expectation.
- **Verify:** A pytest asserts the query count ≤ 3 for a Board load; a load-test run is recorded in `backend/tests/load/RESULTS.md` (`tech.md` TC-23). Not run: no code and no measurement exist; current status "not measured".

### NFR-02 — Security
- **Rule:** Passwords are stored only as hashes; no response body contains password data; access tokens expire 60 minutes after issue; every route except register, login, health and the two Guest read endpoints answers 401 without a valid token (R13.6, R13.8, R13.9, R13.10, R13.11). The two Guest read endpoints are decided by the Access Resolution Table of Requirement 3.
- **Rationale:** Credentials and session handling are the highest-impact failure area.
- **Example:** `GET /api/users/me` returns `id`, `name`, `username`, `email` and `created_at` only (R19.1).
- **Verify:** pytest iterates the registered routes and asserts 401 for every protected route without a token; a test asserts no JSON key beginning with `password` in the `me`, register and login responses; the decoded login token has `exp - iat == 3600`.

### NFR-03 — Responsive layout
- **Rule:** Each of the six routes (`/register`, `/login`, `/`, `/boards/[id]`, `/my-tasks`, `/profile`) and the Card Detail Modal is usable at 375 px, 768 px and 1280 px widths with no horizontal page scroll and no clipped or overlapping content (Requirement 23).
- **Rationale:** The brief requires verification at mobile size.
- **Example:** The Kanban board scrolls horizontally inside its own container; the page body does not (R23.3).
- **Verify:** Playwright asserts `document.documentElement.scrollWidth <= window.innerWidth` on all 6 routes at each of the 3 widths.

### NFR-04 — API consistency
- **Rule:** Every API response, including 401, 404 and 500, is either `{ "data": ... }` or `{ "error": "<non-empty string>" }`, never both; `error` is always one string, never a nested object (Requirement 20 criterion 1).
- **Rationale:** The frontend API client unwraps one shape; any deviation becomes a runtime bug.
- **Example:** An unknown route returns a 404 in the error envelope, not the framework's default HTML page.
- **Verify:** A parametrised pytest hits every route (authorised, unauthorised, invalid payload, unknown id) and asserts exactly one of `data` / `error` is present and that `error` is a non-empty string.

### NFR-05 — Accessible interaction
- **Rule:** `BaseModal` closes on `Escape`, moves focus into the modal on open and returns it to the trigger on close; every icon-only button has an `aria-label` (Requirement 25).
- **Rationale:** Modals wrap every form, so one accessibility defect repeats everywhere.
- **Example:** Closing `CardDetailModal` with Escape returns focus to the card that opened it.
- **Verify:** React Testing Library tests for `BaseModal` assert Escape-close and focus return; `grep -rn "<BaseButton" frontend/components | grep -v "aria-label\|>[A-Za-z]"` flags icon-only buttons without labels (expected 0).

---

## 7. Brief gaps resolved

| ID | Gap in the brief | Resolution in this steering |
|---|---|---|
| G-01 | A health check is required for verification but belongs to no feature | A public health check (F-12) |
| G-02 | `/my-tasks` and search need a Card list that the brief does not define | One cards list supports `assignee=me` and search (F-09, F-10) |
| G-03 | The "board administrator" role has no data model or permissions | Roles are held at Team level (Team Admin, Team Member); the permission table is `requirements.md` Requirement 2 (section 2, PR-03) |
| G-04 | Admins "manage member access" but no endpoint exists | A Team Admin adds and removes Team members and changes roles; API-only in V1 (F-11, requirements.md OD-14) |
| G-05 | Notification triggers undefined | Mentions only (PR-05) |
| G-06 | "Completed this week" undefined | One definition of completed (PR-04) |
| G-07 | Outsiders cannot view a Board without joining | Guest read-only access through an Invite Link (PR-09, F-13) |
| G-08 | A Board needs an owning Team before a user has created one | Every user gets a personal Team at registration (PR-10) |

## 8. Out of Scope (must not be generated)

Real-time sync (WebSockets/SSE), email digests, push notifications, file attachments, third-party integrations, labels, due dates and reminders, password change or reset, OAuth/social login, board templates, activity-log pages, touch-based drag-and-drop, i18n (Requirement 17 criteria 2 and 3 cover part of this list).
- **Verify:** `git diff` against the route inventory in PR-02 shows 0 added routes; `grep -rniE "websocket|attachment|due_date|\blabels?\b" backend/app frontend/app frontend/components | grep -vE "aria-label|</?label|htmlFor"` returns 0 lines. The `grep -v` filter exists because the required `aria-label` attributes (NFR-05) and the HTML `<label>` element with `htmlFor` for form fields contain the word "label" but are not the labels feature. Not run: no application code exists yet.
