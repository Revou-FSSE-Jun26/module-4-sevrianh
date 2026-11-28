# Sevy: Task Management Application

Sevy is a Trello-like task management web application built through a disciplined, spec-driven AI workflow. A **Team** owns **Boards**. Team members organise work as **Columns** and **Cards**, move Cards between Columns with drag-and-drop, discuss Cards in threaded Comments, get notified when they are `@mentioned`, and track the Cards assigned to them. Team Admins also manage membership and Invite Links and read Board analytics. An outsider can view one Board read-only through an Invite Link.

The project has two apps: a Flask + PostgreSQL API (`backend/`) and a Next.js frontend (`frontend/`). Both are designed for public deployment (Railway and Vercel).

## Status at a glance

| Item | Status |
|---|---|
| Spec set (`specs/`) and guidelines (`guidelines/`) | Written and kept in sync (requirements V11) |
| Backend API and frontend app | Implemented, verified locally (see [Verified results](#verified-results)) |
| Public API URL (Railway) | **Not deployed yet.** URL: _to be added after deployment_ |
| Public frontend URL (Vercel) | **Not deployed yet.** URL: _to be added after deployment_ |
| Playwright run against the live URL | **Not run**, because no live URL exists |
| NFR-01 latency on the deployed API | **Not measured** (one local run only, see [Non-functional requirements](#non-functional-requirements)) |
| Screenshots | **Not captured yet**, see [Screenshots](#screenshots) |

## Project brief

### User roles

| Role | Who | Can do |
|---|---|---|
| **Team Admin** | Team member with role `admin` (the owner of a personal Team is its Admin) | Everything a Member can do, plus: create, rename and delete Boards; rename, reorder and delete Columns; manage Team members and Invite Links; delete any Card; view Board analytics |
| **Team Member** | Team member with role `member` | Create Columns; create, edit, assign and move Cards; delete own Cards; comment and `@mention`; track own assigned tasks |
| **Guest** | Visitor with a valid, revocable Invite Link (`X-Invite-Token`) for one Board | Read that Board and its Comments only. No JWT, no writes |

The full permission table is Requirement 2 in `specs/requirements.md`.

### Core features

- JWT authentication (register, login, protected routes, logout) and profile (`/profile`)
- Teams and Boards, with a personal Team created at registration
- Columns and Cards with FLOAT `order`, drag-and-drop with optimistic update and rollback, and automatic two-phase rebalance when the gap between neighbours becomes too small
- Card search (title, case-insensitive, 300 ms debounce) and My Tasks (`/my-tasks`)
- Threaded Comments with edit, delete and tombstones
- `@mention` notifications with an unread badge and 30-second polling
- Admin-only Board analytics (`cards_per_column`, `completed_this_week`, `member_activity`, `activity_per_day`)
- Read-only Guest mode through Invite Links

### Non-functional requirements

- **NFR-01, performance.** Target: P95 response time of 300 ms or less with 200 concurrent users on one Board (5 Columns, 50 Cards), measured at the API server over 10 minutes. **Status: measured locally only, not on Railway.** One local run (Flask development server, local PostgreSQL, same machine as the load generator) gave P95 58.21 ms with 0 errors in 42,328 requests. That run says nothing about the deployed Gunicorn setup, so the production figure is still "not measured". Method, environment and result: `backend/tests/load/RESULTS.md`.
- **NFR-02, reliability and data integrity.** Every input is validated by Marshmallow before the service runs. Concurrent Card moves and edits are serialised with `SELECT ... FOR UPDATE`. Cards and Comments are soft-deleted. Every response is either `{ "data": ... }` or `{ "error": "<string>" }`.
- **NFR-03, security.** Passwords are hashed, tokens expire after 60 minutes, and every route except register, login, health and the two Guest read endpoints answers 401 without a valid token.
- **NFR-04, responsive layout.** Every page is designed to be usable at 375, 768 and 1280 px without horizontal page scroll.

## AI workflow summary

The project followed one order: brief, specs, guidelines, code, review, tests, deployment. Each step produced a file that the next step had to obey.

1. **Project brief.** The assignment brief was turned into a product definition (Sevy, roles, scope and out-of-scope list) and stored as steering files in `.kiro/steering/` (`product.md`, `tech.md`, `structure.md`). These are loaded into every Kiro session, so generated code starts from the same rules.
2. **Specification with Kiro.** Kiro generated `requirements.md`, `design.md` and `tasks.md`, which were refined in rounds. Every round is a `## V<N>` entry in `specs/CHANGELOG.md` with **Prompt**, **Before** and **After**. Requirements use acceptance criteria numbered `R<N>.<k>`. A script checks that every criterion appears in the design traceability table and in a task. Open decisions were listed explicitly and each was approved or changed by the project owner before code depended on it.
3. **Steering guidelines.** `guidelines/frontend.md`, `guidelines/backend.md` and `guidelines/database.md` hold rules with an ID, a Rule, a Rationale, an Example and a Verify check. Guidelines were written before the code that uses them. They are loaded automatically when Kiro edits matching files.
4. **Code generation and review.** Kiro generated the Blueprints (routes, services, schemas), models, migrations, pages, components and hooks task by task from `tasks.md`. Each result was reviewed against the guidelines and checked with `flake8`, `eslint`, `tsc` and the test suites.
5. **Violations.** Where generated code broke a guideline, the finding, the guideline ID, the file and line, and the fix were written to `guidelines/VIOLATIONS.md`. Fixed entries state how the fix was verified. Open entries are listed as open.
6. **Tests and documentation with Claude Code.** Claude Code was used to generate and refine the test suites (pytest, Jest, Playwright) and to write documentation such as this README, always checked against the guidelines and run before being accepted.
7. **Deployment.** Planned: Railway for the API and PostgreSQL, Vercel for the frontend, with `flask db upgrade` as the release step. Not done yet, see [Status at a glance](#status-at-a-glance).

## Features implemented

- **Authentication and users:** register and login with JWT (60-minute expiry), protected routes through `middleware.ts` and the `sevy_token` cookie, logout, profile update on `/profile`.
- **Boards, Teams and Invite Links:** personal Team created at registration, Board create, list, rename and delete, Team member management (API only), revocable Guest Invite Links.
- **Columns and Cards:** Column create, rename, reorder and delete; Card create, edit, assign, soft delete; drag-and-drop between Columns with the FLOAT `order` strategy, optimistic update and rollback; done Columns that mark Cards as completed.
- **Comments and notifications:** threaded Comments with edit and delete, `@mention` notifications (deduplicated, no self-notification), notification bell with unread badge and 30-second polling.
- **Search and My Tasks:** Card search with a 300 ms debounce, My Tasks grouped by Board.
- **Analytics:** Admin-only per-Board metrics for the last 7 days or a chosen range.
- **Guest mode:** read-only Board view at `/boards/<id>?invite=<token>`.
- **Tests:** pytest unit and API-flow suites, Jest + React Testing Library suites, and a Playwright E2E suite (4 auth scenarios, the 8-step Kanban journey, a page and mobile layout sweep).

## Technologies

| Area | Technology |
|---|---|
| Frontend | Next.js 15 (App Router), React 19, TypeScript (strict), Tailwind CSS 4, react-hot-toast |
| Backend | Python 3.12, Flask 3, SQLAlchemy 2 (Flask-SQLAlchemy), Flask-Migrate (Alembic), Flask-JWT-Extended, Marshmallow, flask-cors, python-dotenv, Gunicorn |
| Database | PostgreSQL 16 or newer (UUID keys, FLOAT ordering, partial unique indexes, `pg_trgm` trigram index) |
| Testing | pytest + pytest-cov, Jest + React Testing Library, Playwright |
| Code quality | Flake8, ESLint, Prettier, `tsc --noEmit` |
| Deployment (planned) | Railway (API + PostgreSQL), Vercel (frontend) |
| AI tools | Kiro (specs, guidelines, code), Claude Code (tests, documentation) |

## Repository layout

```
.kiro/steering/   product, tech, structure and workflow rules loaded by Kiro
.kiro/specs/      working copy of the specs
specs/            submission copy: requirements.md, design.md, tasks.md, CHANGELOG.md
guidelines/       frontend.md, backend.md, database.md, VIOLATIONS.md
backend/          Flask API (app/blueprints/<feature>/{routes,service,schema}.py, models, migrations, tests)
frontend/         Next.js app (app/, components/{shared,board,card,comments,notifications,layout}, hooks/, lib/, e2e/)
```

## Run locally

Requirements: Python 3.12, Node.js 22, PostgreSQL 16 or newer with permission to create databases and the `pg_trgm` extension.

### 1. Clone and create the databases

```bash
git clone <repository-url>
cd <repository-folder>
createdb sevy
createdb sevy_test
```

### 2. Backend (Flask API)

```bash
cd backend
python -m venv .venv
# Windows (PowerShell): .venv\Scripts\Activate.ps1
# macOS / Linux:        source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env        # Windows: Copy-Item .env.example .env
```

Edit `backend/.env` and set real values (never commit this file):

| Variable | Meaning |
|---|---|
| `FLASK_APP` | `app:create_app` |
| `FLASK_DEBUG` | `1` for local development |
| `DATABASE_URL` | e.g. `postgresql://user:password@localhost:5432/sevy` (hosted databases need `sslmode=require`) |
| `TEST_DATABASE_URL` | database for pytest; the name must end in `_test` |
| `JWT_SECRET_KEY` | a long random string |
| `CORS_ORIGINS` | `http://localhost:3000` locally; the exact Vercel URL in production, never `*` |

Apply the migrations and start the API:

```bash
flask db upgrade
flask run          # http://localhost:5000, check http://localhost:5000/api/health
```

### 3. Frontend (Next.js)

```bash
cd frontend
npm install
cp .env.example .env.local   # Windows: Copy-Item .env.example .env.local
```

Set `API_BASE_URL` and `NEXT_PUBLIC_API_BASE_URL` to the API address (`http://localhost:5000` locally), then:

```bash
npm run dev        # http://localhost:3000
```

## Run the tests

### Backend (pytest and flake8)

```bash
cd backend
pytest -v                                   # unit and API-flow tests
pytest -v --cov=app --cov-report=term       # with coverage (threshold 85%)
flake8 app tests                            # lint, must exit 0
```

The tests need the PostgreSQL database named in `TEST_DATABASE_URL`.

### Frontend (React Testing Library and static checks)

```bash
cd frontend
npm test                                    # Jest + React Testing Library
npm run lint -- --max-warnings 0
npx tsc --noEmit
```

### End-to-end (Playwright)

```bash
cd frontend
npx playwright install                      # once, downloads the browsers
PLAYWRIGHT_BASE_URL=https://<your-vercel-url> npx playwright test
npm run test:e2e                            # same suite, repeated 3 times to expose flaky tests
npx playwright show-report                  # opens the HTML report
```

On Windows PowerShell set the variable first: `$env:PLAYWRIGHT_BASE_URL = "https://<your-vercel-url>"`. Without `PLAYWRIGHT_BASE_URL` the suite targets `http://localhost:3000`, so start both apps locally first. The suite uses no `waitForTimeout`. The committed report in `frontend/playwright-report/` is not a result against a live URL until the deployment exists and the suite has been run against it.

## Verified results

Measured on the development machine on 2026-11-28. None of these runs used a deployed environment.

| Check | Result |
|---|---|
| `flake8 app tests` (backend) | 0 issues |
| `pytest` (backend) | 652 passed |
| Backend coverage | 99.06% (threshold 85%) |
| `npm test` (frontend) | 24 suites, 133 tests passed |
| `npx tsc --noEmit` | 0 errors |
| `npm run lint -- --max-warnings 0` | 0 problems |
| Load test, local only | P95 58.21 ms, 0 errors (not a production figure) |

Known open items are listed in [guidelines/VIOLATIONS.md](guidelines/VIOLATIONS.md).

## Deployment

| Part | Platform | Release step | Public URL |
|---|---|---|---|
| API + PostgreSQL | Railway | `flask db upgrade` (from `backend/Procfile`), then `gunicorn "app:create_app()" --workers 2` | _not deployed yet_ |
| Frontend | Vercel | `next build` | _not deployed yet_ |

Checks to run after deployment:

```bash
curl -s -o /dev/null -w "%{http_code}" https://<api-url>/api/health     # expect 200
```

Also confirm that `CREATE EXTENSION IF NOT EXISTS pg_trgm;` succeeds on the Railway database, because the title-search index depends on it and its availability there is not confirmed.

## Screenshots

Screenshots need the live apps, so none has been captured yet. Save each file under `specs/screenshots/` with the name below and replace "Not captured" with a link.

| Required screenshot | File | Status |
|---|---|---|
| Postman: all 8 Blueprints reachable on the public API URL (health, register, login, boards, columns, cards, comments, notifications, analytics, users) | `postman-blueprints.png` | Not captured |
| Register | `register.png` | Not captured |
| Login | `login.png` | Not captured |
| Dashboard | `dashboard.png` | Not captured |
| Board Detail with Columns and Cards | `board-detail.png` | Not captured |
| A Card being dragged between Columns | `drag-card.png` | Not captured |
| Card Detail Modal with Comments | `card-detail.png` | Not captured |
| My Tasks | `my-tasks.png` | Not captured |
| Profile | `profile.png` | Not captured |
| Notification bell with an unread count | `notification-bell.png` | Not captured |
| Mobile layout (375 px, DevTools device mode) | `mobile.png` | Not captured |
| Playwright HTML report with all tests passing against the live URL | `playwright-report.png` | Not captured |

## Documentation map

- [specs/requirements.md](specs/requirements.md): requirements with numbered acceptance criteria
- [specs/design.md](specs/design.md): design, route table and traceability to every criterion
- [specs/tasks.md](specs/tasks.md): implementation tasks
- [specs/CHANGELOG.md](specs/CHANGELOG.md): every refinement round with Prompt, Before and After
- [guidelines/](guidelines/): `frontend.md`, `backend.md`, `database.md`, and [VIOLATIONS.md](guidelines/VIOLATIONS.md)
