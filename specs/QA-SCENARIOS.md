# Sevy QA Test Scenarios

Priority: **P0** blocks release, **P1** core behavior, **P2** edge or polish.
Layer: **API** (pytest), **UI** (Jest), **E2E** (Playwright), **CI**, **deploy**, **load**.
Requirement references (`R<N>`) point to `requirements.md`.

## 1. Authentication (R13, R21)

| ID | Scenario | Expected | Pri | Layer |
|---|---|---|---|---|
| AUTH-01 | Register with a valid name, username, email and password | 201. A user, a personal Team and an Admin membership are created. No `password*` key in the response. | P0 | API |
| AUTH-02 | Registration fails midway, for example from a forced DB error | No user, Team or membership rows remain. | P1 | API |
| AUTH-03 | Register with a duplicate email, and with a duplicate username that differs only in case | 409 in the error envelope. | P1 | API |
| AUTH-04 | Register with a weak password, an invalid email, or an empty or over-long field | 400 with a single error string. | P1 | API |
| AUTH-05 | Log in with valid credentials | The token has `exp - iat == 3600`. | P0 | API |
| AUTH-06 | Log in with a wrong password, and with an unknown email | The same generic message in both cases. | P0 | API |
| AUTH-07 | Call any protected route with no token, an expired token, a tampered token, or a malformed `Authorization` header | 401 every time (sweep over `app.url_map`). | P0 | API |
| AUTH-08 | Open `/` while logged out | Redirect to `/login`. | P0 | E2E |
| AUTH-09 | Log out, then press the browser Back button | Redirect to `/login`, no cached board data shown. | P1 | E2E |
| AUTH-10 | The token expires while the user is on a page | The next request gives 401, a toast appears, and the user is redirected to `/login`. | P1 | UI |
| AUTH-11 | Visit `/login` while logged in | Redirect to `/`. | P2 | E2E |
| AUTH-12 | Register or update the profile with a whitespace-only `name` | **Open question:** the API accepts it today (201); the spec states the whitespace rule for Board, Column, Card and Comment fields only. Decide, then test. | P1 | API |

## 2. Access and permissions (R1, R2, R3)

| ID | Scenario | Expected | Pri | Layer |
|---|---|---|---|---|
| PERM-01 | Run every role (Admin, Member, Guest, Non-member, anonymous) against every action in the R2 table | Exactly the result the table says. | P0 | API |
| PERM-02 | A Member creates, renames or deletes a Board | 403. | P0 | API |
| PERM-03 | A Member renames, reorders or deletes a Column (OD-01) | 403. | P0 | API |
| PERM-04 | A Member deletes another member's Card | 403. | P0 | API |
| PERM-05 | A Member deletes their own Card | 200 with the deleted id. | P1 | API |
| PERM-06 | An Admin edits another user's Comment | 403 (R2.8). | P0 | API |
| PERM-07 | A Member requests analytics | 403 with no data. | P0 | API |
| PERM-08 | A user from Team B requests a Board of Team A: get, update, move, comment, search, My Tasks | 403 with no data leaked. A made-up UUID gives 404. | P0 | API |
| PERM-09 | Send a non-UUID path parameter | 400 or 404 in the envelope, never a 500. | P1 | API |
| PERM-10 | Use the UI as a Member | Admin-only controls (delete column, analytics panel) are hidden. | P1 | UI |
| PERM-11 | Hide the controls in the UI, then call the API directly | The API still refuses (R2.1). | P0 | API |

## 3. Invite links and Guests (R3)

| ID | Scenario | Expected | Pri | Layer |
|---|---|---|---|---|
| INV-01 | Open `/boards/<id>?invite=<token>` with no JWT | Read-only view of Columns, Cards and Comments, no edit controls, no redirect to `/login`. | P0 | E2E |
| INV-02 | A Guest tries POST, PUT or DELETE on the covered Board | Refused, no data changed. | P0 | API |
| INV-03 | A link for Board A is used on Board B | No access. | P0 | API |
| INV-04 | A revoked link, and an expired link | No Board data. | P0 | API |
| INV-05 | A valid link sent together with an invalid or expired JWT | Rejected, no fallback to Guest (R3.12). | P0 | API |
| INV-06 | A Team member opens a link | Their own role is kept (R3.9). | P1 | API |
| INV-07 | A Guest reaches search, notifications, analytics, My Tasks or the profile | Refused (R3.14). | P0 | API |
| INV-08 | Guess or modify a token | No access; the token has enough entropy. | P1 | API |
| INV-09 | A non-Admin creates, lists or revokes links | 403. | P1 | API |

## 4. Boards and Columns (R4, R5)

| ID | Scenario | Expected | Pri | Layer |
|---|---|---|---|---|
| BRD-01 | Create a Board with no Team given | It lands in the personal Team. | P1 | API |
| BRD-02 | Create a Board with an empty, whitespace-only or over-limit name | 400. | P1 | API |
| BRD-03 | Delete a Board that has Columns, Cards and Comments | Everything is removed and the id is returned. | P1 | API |
| BRD-04 | The Dashboard has no Boards | An empty state is shown. | P2 | UI |
| COL-01 | Add Columns in sequence | Increasing FLOAT order values. | P1 | API |
| COL-02 | Reorder a Column between two neighbours 60 or more times | A rebalance happens; order stays strictly unique. | P0 | API |
| COL-03 | Reorder a Column to a position that conflicts with an existing one | Conflict handled or rebalance occurs (real PostgreSQL). | P1 | API |
| COL-04 | Mark a Column as done, then unmark it | Completion state follows R24. | P1 | API |
| COL-05 | Delete a Column that has Cards | Column and Cards are removed permanently. | P1 | API |
| COL-06 | Two users add a Column at the same moment | No duplicate order, no 500. | P1 | API |
| COL-07 | Add a Column in the UI | It appears at once with no reload and stays after reload. | P0 | E2E |

## 5. Cards and drag-and-drop (R6, R7, R24)

| ID | Scenario | Expected | Pri | Layer |
|---|---|---|---|---|
| CRD-01 | Create a Card at the end of a Column | 201. | P0 | API |
| CRD-02 | Create a Card with an empty, whitespace-only, 200-character and 201-character title | 400 for empty or over-limit titles. | P1 | API |
| CRD-03 | Edit a Card to a title with special characters (`<script>`, emoji) | Stored as plain text; the UI escapes it. | P0 | API/UI |
| CRD-04 | Assign a Card to a Team member, then to a non-member | 200, then 400; the Card keeps its assignee. | P1 | API |
| CRD-05 | Soft-delete a Card | Hidden from Board, search, My Tasks and analytics; Comments remain; `GET` gives 404. | P0 | API |
| DND-01 | Drag a Card to another Column and reload | The Card is still there (BG-03). | P0 | E2E |
| DND-02 | Drag a Card between two Cards | Order is correct after reload. | P0 | E2E |
| DND-03 | Drag a Card into an empty Column | It appears there. | P1 | E2E |
| DND-04 | The move request fails (500 or network down) | The Card rolls back and a toast shows. | P0 | UI |
| DND-05 | Drop a Card onto its own position | No request is sent. | P2 | UI |
| DND-06 | User A moves a Card that user B has deleted | 404 and the UI recovers. | P1 | API |
| DND-07 | Move a Card into a done Column, out again, and across the Sun 23:59 / Mon 00:00 UTC boundary | Completion state and "completed this week" are correct. | P0 | API |
| DND-08 | Create a Card directly in a done Column | It counts as completed. | P1 | API |
| DND-09 | Drag as a Guest | The Card is not draggable. | P1 | UI |

## 6. Comments and mentions (R8, R9)

| ID | Scenario | Expected | Pri | Layer |
|---|---|---|---|---|
| CMT-01 | Add a Comment, a reply, and a reply to a reply | The thread nests as the spec says. | P1 | API |
| CMT-02 | Add an empty Comment | 400. | P1 | API |
| CMT-03 | A non-author edits or deletes a Comment | 403. | P0 | API |
| CMT-04 | Delete a Comment that has replies | It stays as an empty tombstone. | P1 | API |
| CMT-05 | Delete a Comment with no replies | It is hidden. | P1 | API |
| CMT-06 | Reply to a Comment that belongs to another Card | 400. | P1 | API |
| CMT-07 | Delete a Comment | Response is `{"data": {"id": "<uuid>"}}` (R8.10). | P1 | API |
| CMT-08 | A removed Team member edits or deletes their own earlier Comment | 403 and the Comment is unchanged (R1.1). Found on 2026-11-28, fixed, test added. | P0 | API |
| CMT-09 | Edit or delete a Comment whose Card was soft-deleted | 404 (R6.14). Verified. | P1 | API |
| NTF-01 | `@bob` mentioned once | One notification. | P0 | API |
| NTF-02 | `@bob @bob` in one Comment | One notification. | P1 | API |
| NTF-03 | A self-mention | None. | P1 | API |
| NTF-04 | A mention of a username outside the Team, and of an unknown username | None. | P0 | API |
| NTF-05 | `@Bob` (different case) | One notification (R9, OD-05). Verified. | P2 | API |
| NTF-10 | A Comment containing an email-style token such as `x@bob.com` where `bob` is a Team username | **Open question:** one notification is created today. This follows the spec text (`@` plus 3 to 30 characters, no word boundary), but it is probably unintended. Decide, then test. | P2 | API |
| NTF-06 | Page through the list | `page`, `per_page`, `total`, `total_pages`, `unread_count` are correct. | P1 | API |
| NTF-07 | `per_page=0`, `-1`, `51`, or `page` past the end | 400, or an empty page; never a 500. | P1 | API |
| NTF-08 | Mark a notification read; try another user's notification | 200, then 404. | P0 | API |
| NTF-09 | The bell polls every 30 seconds | Unread count updates; polling stops on unmount. | P2 | UI |

## 7. Search and My Tasks (R10, R18)

| ID | Scenario | Expected | Pri | Layer |
|---|---|---|---|---|
| SRC-01 | Search `DEPLOY` for the title "Deploy to Railway" | A match, ignoring case. | P1 | API |
| SRC-02 | Search with a blank, whitespace-only or over-long term | 400. | P1 | API |
| SRC-03 | Search with `%`, `_`, `'` or SQL injection strings | Treated as literal text; no error, no leak. | P0 | API |
| SRC-04 | Search a Board of another Team | 403; results never include inaccessible Cards. | P0 | API |
| SRC-05 | Type quickly in the box | One request, 300 ms after the last keystroke; none while empty. | P1 | UI |
| SRC-06 | Responses arrive out of order | The UI shows the latest query's results. | P1 | UI |
| MYT-01 | Open My Tasks | Only my non-deleted Cards, grouped by Board name. | P1 | API/UI |
| MYT-02 | I am removed from the Team | My assigned Cards on that Team's Boards are no longer shown (confirm against the spec). | P1 | API |
| MYT-03 | I have no tasks | An empty state is shown. | P2 | UI |

## 8. Analytics, team members, profile (R11, R12, R19)

| ID | Scenario | Expected | Pri | Layer |
|---|---|---|---|---|
| ANA-01 | A Board with a known set of Cards | Cards per Column, completed this week, member activity and activity over time match. | P1 | API |
| ANA-02 | The Board is empty | Zeros, not errors. | P2 | API |
| ANA-03 | Soft-deleted Cards exist | They are not counted. | P0 | API |
| MBR-01 | An Admin adds a member, changes a role, removes a member | Each succeeds. | P1 | API |
| MBR-02 | An Admin removes or demotes the last Admin | Refused (at-least-one-Admin invariant). | P0 | API |
| MBR-03 | A removed member's token | They lose access to that Team's Boards on the next request. | P0 | API |
| MBR-04 | An Admin adds a user who is already a member | A defined error, no duplicate row. | P1 | API |
| PRF-01 | Update name and email | Success. | P1 | API/UI |
| PRF-02 | Change email to one already taken | 409. | P1 | API |
| PRF-03 | Send `password`, `id` or `role` in the profile payload | Ignored or rejected (mass assignment). | P0 | API |

## 9. API conventions and security (R20, NFR-02, NFR-04)

| ID | Scenario | Expected | Pri | Layer |
|---|---|---|---|---|
| API-01 | Every route with a valid request, bad payload, missing token and unknown id | Exactly one of `data` or `error`; `error` is a non-empty string. | P0 | API |
| API-02 | Unknown route, wrong method, malformed JSON, empty body | JSON 404, 405 or 400, never HTML, never 500. | P0 | API |
| API-03 | An unhandled exception | 500 in the envelope, no stack trace; structured JSON log. | P1 | API |
| API-04 | `GET /api/health` | 200 in 2 seconds or less, no auth. | P0 | API/deploy |
| API-05 | A request from a disallowed `Origin` | No `Access-Control-Allow-Origin` header; `*` is not allowed in production. | P0 | deploy |
| API-06 | A response body from any user route | No password hash. | P0 | API |
| API-07 | Route inventory | `flask routes` matches Appendix A exactly (PR-02). | P1 | API |
| API-08 | A very large or deeply nested body | 413 or 400, not a crash. | P2 | API |

## 10. Frontend, accessibility and responsive (R21 to R25, NFR-03, NFR-05)

| ID | Scenario | Expected | Pri | Layer |
|---|---|---|---|---|
| FE-01 | Visit all 6 routes at 375, 768 and 1280 px | `scrollWidth <= innerWidth`; Kanban scrolls inside its own container. | P1 | E2E |
| FE-02 | Open a modal, press Escape, press Tab repeatedly | Closes on Escape; focus moves in on open and returns to the trigger. | P1 | UI |
| FE-03 | Inspect the icon-only buttons | Each has an `aria-label`. | P2 | UI |
| FE-04 | The API returns 400, 401, 403, 404, 500, or the network drops | The right toast shows and the page stays usable. | P1 | UI |
| FE-05 | Double-click Submit on any form | One request; the button shows a loading state. | P1 | UI |
| FE-06 | Reload `/boards/[id]` with a bad id | A not-found or forbidden state, not a blank screen. | P1 | E2E |
| FE-07 | Check how the token is stored | `sevy_token` cookie; review `HttpOnly`, `Secure`, `SameSite` against the spec. | P0 | E2E |
| FE-08 | Log in from a fresh browser after visiting `/login` logged out | Lands on `/` on the first attempt (no stale cached redirect). | P0 | E2E |

## 11. Data integrity and non-functional (R14, R15, R26)

| ID | Scenario | Expected | Pri | Layer |
|---|---|---|---|---|
| DAT-01 | Load a Board of 5 Columns and 50 Cards | 3 SQL queries or fewer. | P1 | API |
| DAT-02 | `flask db upgrade` on an empty DB, then `flask db check` | 10 tables, 3 partial unique indexes and named CHECK constraints exist, no drift. | P0 | CI |
| DAT-03 | Insert duplicate order values directly | The partial unique index rejects them; soft-deleted rows are excluded. | P1 | API |
| DAT-04 | Delete a user who owns Cards or Comments | Defined behavior (FK rules); no orphans, no 500. | P1 | API |
| PERF-01 | 200 concurrent users on one Board for 10 minutes | P95 of 300 ms or less, measured at the server; record in `backend/tests/load/RESULTS.md`. | P0 | load |
| PERF-02 | The same load while 50 users move Cards | No ordering collisions or deadlocks; error rate under 1%. The script has no write mix yet. | P1 | load |
| PERF-03 | The first requests after a server start | Record cold-start latency separately. A 20-user smoke run gave P95 253.56 ms against 58.21 ms in the steady 10-minute run. | P2 | load |
| PERF-04 | PERF-01 on the deployed Railway API with the `Procfile` workers | Same target, recorded with Railway plan, worker class and count, database plan. Not done. | P0 | load |
| PERF-05 | The load script under failure | Errors and responses without `X-Server-Duration-Ms` are counted and reported, never folded into the P95 (script v2). | P1 | load |

## Status notes (2026-11-28)

Automated and passing on this machine:
- Backend: 652 pytest tests, 99% coverage, every `service.py` at least 90%. This includes the core flow test (register to analytics).
- Frontend: 127 Jest tests. Playwright: 20 tests, 60 of 60 with `--repeat-each=3`, against a local production build (not the live Vercel URL).
- Verified by probe on 2026-11-28 (not yet permanent tests): MBR-02 (removing or demoting the last Admin gives 409), PRF-03 (unknown profile fields give 400), SRC-02 and SRC-03 (`%`, `_`, quotes and SQL text are treated literally; 101 characters and blanks give 400), CMT-09.
- PERF-01 local run: P95 58.21 ms, 42,328 requests, 0 errors, 200 users, 10 minutes, Flask development server on Windows with local PostgreSQL. This is recorded in `backend/tests/load/RESULTS.md`. It does not verify the Railway target.

Open decisions: AUTH-12, NTF-10.

Not covered or not measured: PERF-02, PERF-04, API-05 and API-04 on a live URL, FE-07 cookie flag review, MYT-02.