# Requirements Document

## Introduction

Sevy is a team task management web application similar to Trello. Team members organize work on Boards made of ordered Columns and Cards, move Cards between Columns as work progresses, discuss work in threaded Comments, and track activity. The goal is fast, shared visibility of who is doing what.

The frontend uses Next.js, React, TypeScript, and Tailwind CSS. The backend uses Flask and Python. The database is PostgreSQL accessed through SQLAlchemy.

Out of scope for version 1: file attachments, email digests, and third-party integrations.

## Glossary

- **Sevy**: The team task management web application described in this document.
- **API**: The Flask backend HTTP interface used by the Frontend.
- **Frontend**: The Next.js, React, TypeScript, and Tailwind CSS web client.
- **Database**: The PostgreSQL database accessed through SQLAlchemy.
- **Team**: A group of users that owns one or more Boards.
- **Board**: A workspace owned by exactly one Team, containing ordered Columns.
- **Column**: An ordered list of Cards within a Board, for example To Do, Doing, or Done.
- **Card**: A task that lives in exactly one Column, with a title and a description.
- **Position**: The zero-based index of a Column within its Board, or of a Card within its Column.
- **Comment**: A message on a Card. A Comment may be a reply to another Comment, forming a thread.
- **Mention**: A reference to a Member by username inside a Comment, written as `@username`.
- **Notification**: A record created for a Member when that Member is mentioned in a Comment.
- **Guest**: A user who views a Board through an Invite_Link and is not a Team member.
- **Member**: A Team member who can create and move work on the Team's Boards.
- **Admin**: A Team member with all Member permissions plus management permissions on the Team's Boards.
- **Invite_Link**: A URL token that grants a Guest read-only access to one Board.
- **Authorization_Service**: The API component that decides whether a user may perform an action on a Board.
- **Search_Service**: The API component that finds Cards by title keyword.
- **Analytics_Service**: The API component that computes per-board statistics.
- **Notification_Service**: The API component that creates and returns Notifications.
- **Activity_Event**: A record of a change on a Board (such as Card created, Card moved, or Comment added) with a timestamp and an acting user.

## Requirements

### Requirement 1: Board Access Isolation

**User Story:** As a Team member, I want my Board's data visible only to my Team, so that confidential work stays private.

#### Acceptance Criteria

1. IF a user who is not a member of a Board's Team and does not hold a valid Invite_Link for that Board requests any data of that Board, THEN THE Authorization_Service SHALL reject the request with HTTP status 403.
2. THE Authorization_Service SHALL evaluate Board membership on every API request that reads or modifies Board data.
3. FOR ALL Boards B and users U who are not members of B's Team, THE API SHALL return no Column, Card, Comment, Activity_Event, or analytics data of B to U, including in search results and Notifications.
4. WHEN a user is removed from a Team, THE Authorization_Service SHALL reject that user's subsequent requests to the Team's Boards with HTTP status 403.
5. IF a requested Board does not exist or the requester has no access to it, THEN THE API SHALL return the same error response body in both cases.

### Requirement 2: Role-Based Permission Enforcement

**User Story:** As a Team Admin, I want each role limited to its permitted actions, so that Guests and Members cannot change what only Admins may change.

#### Acceptance Criteria

1. THE Authorization_Service SHALL enforce permissions on the API for every request, independent of controls shown in the Frontend.
2. IF a Guest sends a request that creates, edits, deletes, or moves any Board, Column, Card, or Comment, THEN THE API SHALL reject the request with HTTP status 403 and leave stored data unchanged.
3. IF a Member sends a request to delete a Board or to manage Team members, THEN THE API SHALL reject the request with HTTP status 403 and leave stored data unchanged.
4. WHEN a Member sends a valid request to create a Column, Card, or Comment, or to move a Card, THE API SHALL perform the requested action.
5. WHERE the requester is an Admin, THE API SHALL allow every action permitted to a Member plus Column management, Team member management, Board settings changes, and analytics viewing.
6. IF an Admin sends a request for a Board owned by a Team to which that Admin does not belong, THEN THE API SHALL reject the request with HTTP status 403.
7. FOR ALL actions A and roles R, THE Authorization_Service SHALL return the same allow or deny decision for repeated evaluations of A by R on unchanged data (determinism).
8. FOR ALL actions permitted to a Guest, THE Authorization_Service SHALL also permit that action to a Member, and FOR ALL actions permitted to a Member, THE Authorization_Service SHALL also permit that action to an Admin of the same Team (role monotonicity).

### Requirement 3: Guest Access via Invite Link

**User Story:** As a Member, I want to share a Board through an invite link, so that outsiders can view progress without joining the Team.

#### Acceptance Criteria

1. WHEN an Admin requests creation of an Invite_Link for a Board, THE API SHALL generate a unique, unguessable Invite_Link bound to that Board.
2. WHEN a user opens a valid Invite_Link, THE Frontend SHALL display the Board's Columns, Cards, and Comments in read-only form with the Guest role.
3. IF a user opens an Invite_Link that is invalid or revoked, THEN THE API SHALL reject the request with HTTP status 404.
4. WHEN an Admin revokes an Invite_Link, THE API SHALL reject all subsequent requests that use that Invite_Link.
5. THE API SHALL limit access granted by an Invite_Link to the single Board that the Invite_Link is bound to.

### Requirement 4: Board Management

**User Story:** As a Member, I want to work on Boards owned by my Team, so that the Team shares one workspace.

#### Acceptance Criteria

1. WHEN an Admin submits a Board name of 1 to 100 characters, THE API SHALL create a Board owned by the Admin's Team.
2. IF a submitted Board name is empty or longer than 100 characters, THEN THE API SHALL reject the request with HTTP status 400 and a validation error message.
3. WHEN a Member requests the list of Boards, THE API SHALL return only the Boards owned by Teams to which that Member belongs.
4. WHEN an Admin changes Board settings, THE API SHALL persist the changes and return the updated Board.
5. WHEN an Admin deletes a Board, THE API SHALL delete the Board together with all of its Columns, Cards, Comments, Notifications, and Activity_Events.
6. WHEN a Member opens a Board, THE Frontend SHALL display the Board's Columns in Position order, each containing its Cards in Position order.

### Requirement 5: Column Management

**User Story:** As an Admin, I want to manage ordered Columns on a Board, so that the workflow stages match how my Team works.

#### Acceptance Criteria

1. WHEN a Member submits a Column name of 1 to 100 characters, THE API SHALL create the Column at the last Position of the Board.
2. IF a submitted Column name is empty or longer than 100 characters, THEN THE API SHALL reject the request with HTTP status 400 and a validation error message.
3. WHEN an Admin renames a Column, THE API SHALL persist the new name.
4. WHEN an Admin reorders a Column, THE API SHALL persist the new Column order.
5. WHEN an Admin deletes a Column, THE API SHALL delete the Column and its Cards and renumber the remaining Columns.
6. FOR ALL Boards, THE API SHALL maintain Column Positions as the contiguous sequence 0 to n-1 with no duplicates after any create, reorder, or delete operation (invariant).
7. IF a Member sends a request to rename, reorder, or delete a Column, THEN THE API SHALL reject the request with HTTP status 403.

### Requirement 6: Card Management

**User Story:** As a Member, I want to create and edit Cards, so that I can record tasks for my Team.

#### Acceptance Criteria

1. WHEN a Member submits a Card title of 1 to 200 characters and a description of up to 5000 characters for a Column, THE API SHALL create the Card at the last Position of that Column.
2. IF a submitted Card title is empty or longer than 200 characters, or the description is longer than 5000 characters, THEN THE API SHALL reject the request with HTTP status 400 and a validation error message.
3. WHEN a Member edits the title or description of a Card, THE API SHALL persist the change and return the updated Card.
4. WHEN a Member deletes a Card, THE API SHALL delete the Card with its Comments and renumber the remaining Cards in that Column.
5. FOR ALL Columns, THE API SHALL maintain Card Positions as the contiguous sequence 0 to n-1 with no duplicates after any create, move, or delete operation (invariant).
6. FOR ALL Cards, THE API SHALL store the Card in exactly one Column of exactly one Board (invariant).
7. FOR ALL valid Card inputs, creating a Card and then retrieving it SHALL return a Card with the same title and description (round-trip property).

### Requirement 7: Drag-and-Drop Card Movement

**User Story:** As a Member, I want to drag Cards between Columns, so that the Board reflects work progress and the order stays as I left it.

#### Acceptance Criteria

1. WHEN a Member drops a Card at a target Column and Position, THE API SHALL move the Card to that Column and Position.
2. WHEN a Card is moved, THE API SHALL update the Positions of Cards in the source Column and the target Column so that each remains a contiguous sequence 0 to n-1.
3. WHEN a Card is moved, THE API SHALL persist the new order before returning a success response.
4. WHEN a Member reloads the Board after a Card move, THE Frontend SHALL display the Cards in the same Columns and order as after the move (order persistence).
5. FOR ALL Boards and valid moves, THE API SHALL keep the total number of Cards on the Board unchanged by the move (invariant).
6. FOR ALL Cards moved from Column X Position p to Column Y Position q, moving the Card back to Column X Position p SHALL restore the original order of Cards in both Columns (round-trip property).
7. FOR ALL moves, sending the same move request twice SHALL produce the same Board state as sending it once (idempotence).
8. IF a move request names a target Column that is on a different Board than the Card, THEN THE API SHALL reject the request with HTTP status 400 and leave stored data unchanged.
9. IF a move request names a Position outside the range 0 to the number of Cards in the target Column, THEN THE API SHALL reject the request with HTTP status 400 and leave stored data unchanged.
10. IF the API rejects or fails a move request, THEN THE Frontend SHALL restore the Card to its previous Column and Position and display an error message.
11. WHEN two Members move Cards in the same Board at the same time, THE API SHALL serialize the moves so that the resulting Positions in each affected Column are contiguous with no duplicates.

### Requirement 8: Threaded Comments

**User Story:** As a Member, I want to discuss a Card in threaded Comments, so that decisions stay attached to the work.

#### Acceptance Criteria

1. WHEN a Member submits a Comment of 1 to 2000 characters on a Card, THE API SHALL store the Comment with the author and a creation timestamp.
2. WHEN a Member submits a reply to an existing Comment, THE API SHALL store the reply as a child of that Comment on the same Card.
3. IF a submitted Comment is empty or longer than 2000 characters, THEN THE API SHALL reject the request with HTTP status 400 and a validation error message.
4. IF a reply names a parent Comment that belongs to a different Card, THEN THE API SHALL reject the request with HTTP status 400.
5. WHEN a Member opens a Card, THE Frontend SHALL display its Comments as threads, with each reply under its parent Comment, ordered by creation timestamp.
6. FOR ALL valid Comment inputs, creating a Comment and then retrieving it SHALL return a Comment with the same text, author, and parent (round-trip property).

### Requirement 9: Mention Notifications

**User Story:** As a Member, I want to be alerted when someone mentions me in a Comment, so that I can respond promptly.

#### Acceptance Criteria

1. WHEN a Comment containing a Mention of a Member who belongs to the Board's Team is stored, THE Notification_Service SHALL create one unread Notification for that Member.
2. WHEN a Comment mentions the same Member more than once, THE Notification_Service SHALL create exactly one Notification for that Member for that Comment (idempotence).
3. IF a Comment contains a Mention of a username that does not match a Member of the Board's Team, THEN THE Notification_Service SHALL create no Notification for that Mention.
4. WHEN a Member authors a Comment that mentions the same Member, THE Notification_Service SHALL create no Notification for that Member.
5. WHILE a Member is signed in, THE Frontend SHALL poll the API for new Notifications every 15 seconds.
6. WHEN the API receives a Notification poll request, THE Notification_Service SHALL return only that Member's Notifications.
7. WHEN a Member marks a Notification as read, THE Notification_Service SHALL persist the read state, and marking it read again SHALL leave the state unchanged (idempotence).
8. FOR ALL Notifications, THE Notification_Service SHALL reference a Comment on a Board that the recipient belongs to (invariant).

### Requirement 10: Card Search

**User Story:** As a Member, I want to search Cards by title keyword across my Boards, so that I can find work quickly.

#### Acceptance Criteria

1. WHEN a Member submits a search keyword of 1 to 100 characters, THE Search_Service SHALL return all Cards whose title contains the keyword, ignoring letter case, on Boards of the Member's Teams.
2. THE Search_Service SHALL include the Board name, Column name, and Card title in each search result.
3. IF a search keyword is empty or longer than 100 characters, THEN THE API SHALL reject the request with HTTP status 400.
4. FOR ALL search results, THE Search_Service SHALL return only Cards on Boards that the requesting Member belongs to (invariant).
5. FOR ALL keywords K, a search for K SHALL return every accessible Card whose title contains K, and each returned Card's title SHALL contain K (soundness and completeness).
6. FOR ALL keywords K, a search for K with unchanged data SHALL return the same result set when repeated (idempotence).
7. IF a search matches no Cards, THEN THE API SHALL return an empty result list with HTTP status 200.

### Requirement 11: Board Analytics

**User Story:** As an Admin, I want per-board analytics, so that I can see workload distribution and team activity.

#### Acceptance Criteria

1. WHEN an Admin requests analytics for a Board of the Admin's Team, THE Analytics_Service SHALL return the number of Cards in each Column.
2. WHEN an Admin requests analytics for a Board, THE Analytics_Service SHALL return the number of Activity_Events per day over the requested date range.
3. IF a Member or Guest requests analytics, THEN THE API SHALL reject the request with HTTP status 403.
4. IF the requested date range has an end date earlier than its start date, THEN THE API SHALL reject the request with HTTP status 400.
5. FOR ALL Boards, THE sum of the per-Column Card counts returned by THE Analytics_Service SHALL equal the total number of Cards on the Board (invariant).
6. FOR ALL Boards, THE sum of the per-day Activity_Event counts returned by THE Analytics_Service SHALL equal the number of Activity_Events in the requested date range (invariant).
7. WHEN a Card, Comment, or Card move changes a Board, THE API SHALL record an Activity_Event with the acting user and a timestamp.

### Requirement 12: Team Member Management

**User Story:** As an Admin, I want to manage Team members and their roles, so that the right people have the right access.

#### Acceptance Criteria

1. WHEN an Admin adds a registered user to the Team with the role Member or Admin, THE API SHALL store the membership with that role.
2. WHEN an Admin changes a Team member's role, THE API SHALL persist the new role and apply it to that member's subsequent requests.
3. WHEN an Admin removes a Team member, THE API SHALL delete the membership and retain the Comments and Cards authored by that user.
4. IF an Admin attempts to remove or demote the last Admin of a Team, THEN THE API SHALL reject the request with HTTP status 409 and leave the membership unchanged.
5. FOR ALL Teams, THE API SHALL keep at least one Admin in the Team (invariant).

### Requirement 13: Authentication

**User Story:** As a user, I want to sign in securely, so that only I can act under my identity.

#### Acceptance Criteria

1. WHEN a user submits valid credentials, THE API SHALL return an authenticated session or token identifying that user.
2. IF a request to a protected endpoint lacks a valid session or token, THEN THE API SHALL reject the request with HTTP status 401.
3. THE API SHALL store passwords only as salted hashes produced by a password hashing algorithm designed for password storage.
4. IF a user submits invalid credentials, THEN THE API SHALL return HTTP status 401 with an error message that does not reveal whether the username or the password was wrong.

### Requirement 14: Response Time

**User Story:** As a Member, I want Sevy to respond quickly, so that I can keep working without waiting.

#### Acceptance Criteria

1. WHILE the load is at most 200 concurrent users on one Board, THE API SHALL return responses in under 300 ms for at least 95% of requests, measured at the API server over a 10-minute window.
2. THE Database SHALL have indexes on the columns used for Board membership lookups, Card Position ordering, and Card title search.

### Requirement 15: Concurrency Capacity

**User Story:** As a Team lead, I want many people to work on one Board at once, so that large Teams can collaborate without slowdown.

#### Acceptance Criteria

1. WHILE 200 users are concurrently active on one Board, THE API SHALL keep the 95th percentile response time within 300 ms.
2. WHILE 200 users are concurrently active on one Board, THE API SHALL return no HTTP 5xx responses caused by Database contention.
3. WHEN two users edit the same Card at the same time, THE API SHALL apply the edits in a defined order so that the stored Card equals one of the submitted versions.

### Requirement 16: Technology Constraints

**User Story:** As a developer, I want a fixed technology stack, so that the codebase stays consistent.

#### Acceptance Criteria

1. THE Frontend SHALL be implemented with Next.js, React, TypeScript, and Tailwind CSS.
2. THE API SHALL be implemented with Flask in Python.
3. THE Database SHALL be PostgreSQL, accessed from the API through SQLAlchemy.
4. THE API SHALL exchange data with the Frontend as JSON over HTTP.
5. WHEN the API serializes a Board, Column, Card, Comment, or Notification to JSON, THE API SHALL produce JSON that deserializes to an equivalent object (round-trip property).

### Requirement 17: Version 1 Scope Boundary

**User Story:** As a product owner, I want a defined v1 scope, so that the team delivers the core features first.

#### Acceptance Criteria

1. THE Sevy v1 release SHALL provide Boards, Columns, Cards, Comments, drag-and-drop, Notifications, Search, and Analytics.
2. THE Sevy v1 release SHALL exclude file attachments, email digests, and third-party integrations.
