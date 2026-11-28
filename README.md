# Sevy — Task Management Application

Sevy is a collaborative Kanban task management web application with Team-based permissions, read-only Guest invite links, `@mention` notifications, threaded comments, and board analytics.

## Project Brief

### Overview
Sevy enables individuals and teams to organize work across Boards, Columns, and Cards with real-time drag-and-drop ordering, search, personal task tracking, and admin analytics.

### User Roles
- **Team Admin**: Full control over the Team, Boards, Columns (create, rename, delete, reorder), Cards, Team membership, Guest invite links, and Board analytics.
- **Team Member**: Can view Boards, create/edit/move Cards, delete own Cards, comment and `@mention` teammates, and view assigned tasks.
- **Guest**: Read-only access to a specific Board and its Card comments via a revocable `X-Invite-Token` link, with no write or analytics access.

### Core Features
- JWT authentication (`/register`, `/login`) and profile management (`/profile`)
- Personal and shared Team Boards (`/`, `/boards/[id]`)
- Drag-and-drop Kanban board with persistent gap-based ordering and automatic two-phase rebalancing
- Card search and My Tasks (`/my-tasks`)
- Threaded comments with tombstone preservation and `@mention` notifications
- Admin-only Board analytics (`cards_per_column`, `completed_this_week`, `member_activity`, `activity_per_day`)
- Read-only Guest mode via invite links

### Non-Functional Requirements
- **NFR-01 (Performance / Latency)**: API P95 latency target under load (200 virtual users on 1 Board with 5 Columns and 50 Cards over 10 minutes, measured via server `X-Server-Duration-Ms` header) — *target not measured*.
- **NFR-02 (Reliability & Data Integrity)**: Strict input validation, transactional row locking (`SELECT ... FOR UPDATE`) for concurrent card moves/edits, soft-delete retention, and uniform `{ "data" }` / `{ "error" }` response envelopes.

---

## AI Workflow Summary
This repository was built using a spec-driven, guideline-enforced AI engineering workflow:
1. **Specification & Design**: Requirements, domain invariants, API contracts, and ordered implementation tasks were defined in `.kiro/specs/task-management-app/`.
2. **Backend-First Incremental Delivery**: Models, migrations, and eight Flask Blueprints (`auth`, `users`, `boards`, `columns`, `cards`, `comments`, `notifications`, `analytics`) were implemented with strict route/service separation and verified with `pytest` and `flake8`.
3. **Frontend Implementation**: Next.js App Router pages, hooks, and components were built using shared primitives (`BaseButton`, `BaseModal`, `BaseBadge`), strict TypeScript, and Jest + React Testing Library tests.

---

## Features Implemented
- **Authentication & Users**: Registration, login, JWT session handling, `/profile` updates.
- **Boards, Teams & Invite Links**: Personal team auto-provisioning, board CRUD, team member management, revocable guest invite tokens.
- **Columns & Cards**: Column CRUD & reorder, Card CRUD, soft delete, move with two-phase rebalance, search, and `/my-tasks`.
- **Comments & Notifications**: Threaded comments with tombstones, `@mention` parsing and deduplicated unread notifications, notification bell polling.
- **Analytics**: Admin-only board metrics and 7-day / custom date-range activity breakdown.

---

## Technologies
- **Backend**: Python, Flask, SQLAlchemy, Flask-Migrate (Alembic), Marshmallow, Flask-JWT-Extended, PostgreSQL, Pytest, Flake8
- **Frontend**: TypeScript, Next.js (App Router), React, Tailwind CSS, Jest, React Testing Library, Playwright, ESLint

---

## Local Run Steps

### 1. Backend
1. Navigate to `backend/` and create/activate a Python virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure PostgreSQL and set environment variables (`DATABASE_URL`, `JWT_SECRET_KEY`, etc.).
4. Run database migrations:
   ```bash
   flask db upgrade
   ```
5. Start the Flask development server:
   ```bash
   flask run
   ```

### 2. Frontend
1. Navigate to `frontend/`:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Configure `.env.local` with `API_BASE_URL` and `NEXT_PUBLIC_API_BASE_URL` pointing to your local backend.
4. Start the Next.js development server:
   ```bash
   npm run dev
   ```

---

## Test Steps

### Backend (`pytest`)
```bash
cd backend
pytest
```

### Frontend Unit & Component Tests (`npm test`)
```bash
cd frontend
npm test
```

### End-to-End Tests (`Playwright`)
```bash
cd frontend
npm run e2e
```

---

## Screenshots to Capture
- [ ] **Postman — Auth Blueprint**: `[Placeholder: Register & Login responses]`
- [ ] **Postman — Users Blueprint**: `[Placeholder: GET/PATCH /api/users/me responses]`
- [ ] **Postman — Boards Blueprint**: `[Placeholder: Board CRUD, Members & Invite Links responses]`
- [ ] **Postman — Columns Blueprint**: `[Placeholder: Column CRUD & Reorder responses]`
- [ ] **Postman — Cards Blueprint**: `[Placeholder: Card CRUD, Move & Search responses]`
- [ ] **Postman — Comments Blueprint**: `[Placeholder: Comment CRUD & Tombstone responses]`
- [ ] **Postman — Notifications Blueprint**: `[Placeholder: List & Mark Read responses]`
- [ ] **Postman — Analytics Blueprint**: `[Placeholder: GET /api/boards/<id>/analytics response]`
- [ ] **UI — Login & Register Pages**: `[Placeholder: /login and /register screenshots]`
- [ ] **UI — Dashboard**: `[Placeholder: / boards list and Create Board modal]`
- [ ] **UI — Board Detail & Dragging a Card**: `[Placeholder: /boards/[id] showing a Card being dragged between Columns]`
- [ ] **UI — Card Detail Modal & Comments**: `[Placeholder: CardDetailModal with threaded comments]`
- [ ] **UI — My Tasks & Profile**: `[Placeholder: /my-tasks and /profile pages]`
- [ ] **Playwright Report**: `[Placeholder: HTML test report summary]`
