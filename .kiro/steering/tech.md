---
inclusion: always
---

# Sevy — Tech Steering

Tells Kiro **which runtime, packages and tools** to use, **how code is linted and formatted**, **how configuration, migrations, deployment and performance tests are handled**, **how tests are run and measured**, and the **process constraints** (commit prefixes, changelog evidence) that must never be broken.
Covers the steering types *code style* and *testing standards*. Folder layout, file ownership and naming live in `structure.md`; scope and roles live in `product.md`.

**What this file owns:** runtime and dependencies · linting and formatting tooling · environment and configuration · migrations workflow and test database · deployment and worker configuration · load-test tooling and the performance environment record · test tooling and coverage thresholds · process constraints.
**What this file does not own:** model, schema, route and service rules (`guidelines/backend.md`, `guidelines/database.md`), frontend page, component, state and API-client rules (`guidelines/frontend.md`), product behavior (`.kiro/specs/task-management-app/requirements.md`). Rules that used to live here and moved are kept as one-line forwarding stubs marked `(moved)` so existing references to the TC ID keep working; the owner holds the full text.

IDs: `TC-xx` technical rules · `TG-xx` brief gaps resolved here. Every rule has Rule, Rationale, Example and a **Verify** line (command, test, or count). A Verify line is a specification of a check: no application code, migration or deployment exists yet, and none of the Verify commands in this file has been run.

---

## 1. Stack Baseline

| Layer | Technology | Constraint |
|---|---|---|
| Runtime | Python 3.12, Node.js 22 LTS | Recorded in `runtime.txt`/`.nvmrc`; changing a major version needs a `CHANGELOG.md` entry |
| Backend | Flask 3, Flask-SQLAlchemy / SQLAlchemy 2, Flask-Migrate, Flask-JWT-Extended, Marshmallow, flask-cors, python-dotenv | Blueprints per feature; app factory `create_app()`; authorization and API rules are in `backend.md` (Team authorization: BE-09) |
| Database | PostgreSQL 16 | Only database allowed in dev, test and prod |
| Server | Gunicorn | Production entrypoint; `flask run` for local dev only |
| Frontend | Next.js 15 (App Router), React 19, TypeScript 5 (strict), Tailwind CSS 4 | Server Components by default (rules in `frontend.md`) |
| UI feedback | react-hot-toast | Only via `lib/toast.ts` (`frontend.md` FE-24) |
| Testing | pytest + pytest-cov, React Testing Library (Jest), Playwright | Three layers (backend, component, E2E) |
| Load testing | Development-only script in `backend/tests/load/` | TC-23; no runtime dependency |
| Linting / format | Flake8, Prettier, ESLint | Zero warnings |
| Deploy | Railway (Flask API + PostgreSQL), Vercel (Next.js) | Public URLs; migrations applied with `flask db upgrade` |
| AI tools | Kiro (specs, guidelines, code), Claude Code (tests, docs) | Output reviewed before commit (TC-21) |

---

## 2. Dependencies

### TC-01 — Pin every dependency
- **Rule:** Every line in `requirements.txt` uses `==`; every dependency in `package.json` uses an exact version (no `^`, `~`, `*`, `latest`); both lockfiles (`package-lock.json`) are committed.
- **Rationale:** Railway and Vercel rebuild from scratch; unpinned versions make a green local run a red deploy.
- **Example:** `Flask==3.1.0`, not `Flask>=3`; `"react-hot-toast": "2.5.1"`, not `"^2.5.1"`.
- **Verify:** `grep -vE "^(#|$)" backend/requirements.txt | grep -vc "=="` → 0; `grep -cE '"[~^]|"\*"|latest' frontend/package.json` → 0.

### TC-02 — Backend runtime dependency allowlist
- **Rule:** Runtime packages are limited to: `flask`, `flask-sqlalchemy`, `flask-migrate`, `flask-jwt-extended`, `flask-cors`, `marshmallow`, `psycopg2-binary`, `python-dotenv`, `gunicorn`. Dev-only (`requirements-dev.txt`): `pytest`, `pytest-cov`, `flake8`. Any other package, including a load-test tool (TC-23), needs a `CHANGELOG.md` entry first.
- **Rationale:** Prevents the AI from silently adding ORMs, auth libraries or validation libraries that duplicate the chosen ones.
- **Example:** `flask-restful`, `pydantic`, `bcrypt` (use Werkzeug hashing) are rejected.
- **Verify:** The set of package names in `requirements.txt` ⊆ the allowlist above (script diff returns 0 extra names).

### TC-03 — Frontend dependency allowlist and forbidden list
- **Rule:** Runtime packages are limited to `next`, `react`, `react-dom`, `react-hot-toast`. Dev: `typescript`, `tailwindcss` (+ its PostCSS plugin), `eslint`, `eslint-config-next`, `prettier`, `prettier-plugin-tailwindcss`, `jest`, `@testing-library/react`, `@testing-library/jest-dom`, `@playwright/test` and their type packages. **Forbidden:** `axios`, `swr`, `react-query`, `redux`, `zustand`, `react-beautiful-dnd`, `@dnd-kit/*`, `react-dnd`, any UI kit (MUI, Chakra, Ant, shadcn).
- **Rationale:** The brief specifies native HTML5 drag-and-drop, a custom fetch wrapper, Context for auth, and in-house shared components.
- **Example:** Drag-and-drop is built in `hooks/useDragAndDrop.ts` with `draggable`, `onDragStart`, `onDragOver`, `onDrop`.
- **Verify:** `grep -cE "axios|swr|react-query|redux|zustand|dnd|@mui|chakra|antd|shadcn" frontend/package.json` → 0.

---

## 3. Code Style

### TC-04 — Python style
- **Rule:** PEP 8 enforced by Flake8 with `max-line-length = 100` and `max-complexity = 8` in `backend/.flake8`; no unused imports (F401), no bare `except:` (E722), no `print()` in `app/`; every public function in `service.py` has type hints on parameters and return.
- **Rationale:** Linter-checked rules cannot drift between generations.
- **Example:** `def move_card_service(card_id: str, data: dict, user_id: str) -> dict:`
- **Verify:** `cd backend && flake8 app tests` exits 0; `grep -rn "print(" backend/app | wc -l` → 0.

### TC-05 — TypeScript style
- **Rule:** Prettier with `singleQuote: true`, `tabWidth: 2`, `semi: true`, `printWidth: 100`; ESLint extends `next/core-web-vitals` plus `@typescript-eslint/no-explicit-any: error`; `tsconfig.json` has `"strict": true`; no `console.log` in committed code.
- **Rationale:** Strict types are what make the typed `ApiError` and API response types useful.
- **Example:** `const handleDrop = (cardId: string, columnId: string): Promise<void> => { ... }`
- **Verify:** from `frontend/`: `npx prettier --check .`, `npm run lint -- --max-warnings 0`, `npx tsc --noEmit` all exit 0; `grep -rn "console.log" app components hooks lib context | wc -l` → 0.

---

## 4. Backend Configuration, Migrations and Deployment

### TC-06 — Response envelope and status codes (moved)
- **Moved to:** `guidelines/backend.md` BE-04 (400 validation string), BE-07 (envelope, status codes, `success()`/`error()` helpers), BE-10 (status and body policy), BE-11 (global handler).

### TC-07 — Validate every input with Marshmallow (moved)
- **Moved to:** `guidelines/backend.md` BE-04 (validate before the service runs) and BE-05 (schema catalog, limits, query parameters).

### TC-08 — Authentication and password handling (moved)
- **Moved to:** `guidelines/backend.md` BE-13 (password hashing, JWT settings, login errors, `JWT_SECRET_KEY`) and BE-08 (guard decorators `@token_required` and `@board_access_required(allow_guest_read=True)`).

### TC-09 — Configuration and secrets
- **Rule:** All configuration is read from environment variables (`python-dotenv` locally, platform variables in production). Flask variables: `FLASK_APP`, `FLASK_DEBUG`, `DATABASE_URL`, `JWT_SECRET_KEY`, `CORS_ORIGINS`. Next.js variables: `NEXT_PUBLIC_API_BASE_URL`, `API_BASE_URL`. Both projects commit a `.env.example` listing every variable with a placeholder value; real `.env*` files are never committed.
- **Rationale:** Surfaces CORS and environment problems early and keeps secrets out of Git.
- **Example:** `.env.example`: `DATABASE_URL=postgresql://user:password@localhost:5432/sevy`.
- **Verify:** `git ls-files | grep -E "(^|/)\.env" | grep -v "\.env\.example$" | wc -l` → 0; every key read via `os.environ`/`os.getenv`/`process.env` appears in the matching `.env.example` (script diff → 0 missing).

### TC-10 — PostgreSQL, migrations, and test database
- **Rule:** Schema changes only through Flask-Migrate migration files committed in `backend/migrations/`; `db.create_all()` is forbidden outside test fixtures. Tests run against a separate PostgreSQL database (`sevy_test`), never SQLite. Hosted `DATABASE_URL` includes `sslmode=require` unless the provider documents otherwise. The model facts (UUID primary keys, FLOAT `order`, named constraints and indexes) are owned by `guidelines/database.md` DB-05, DB-08 and DB-09 and are not repeated here. The partial unique indexes (`uq_cards_column_id_order_active`, `uq_board_columns_board_id_order_active`, `uq_teams_owner_id_personal`) and the named CHECK constraints of DB-08 and DB-09 must appear in the migration files, so that `flask db upgrade` on an empty database creates them. The initial migration also runs `CREATE EXTENSION IF NOT EXISTS pg_trgm` before it creates the GIN index `ix_cards_title_lower_trgm` on `lower(title) gin_trgm_ops` (design.md D-07, approved V11; the index is a trigram index, not a partial unique index, so the partial-index count stays 3). First-deploy manual check: confirm that `pg_trgm` can be created on the Railway PostgreSQL database; its availability there is NOT confirmed. No migration is generated in the documentation round that wrote this rule; no application code exists yet.
- **Rationale:** UUID and Float behaviour, partial indexes and CHECK constraints differ between SQLite and PostgreSQL; SSL errors are the most common first-deploy failure; an index that exists only in a model and not in a migration does not exist in production.
- **Example:** `flask db upgrade` on an empty `sevy_test` database creates all ten tables of DB-01 and the three partial unique indexes above.
- **Verify:** on an empty database `flask db upgrade` exits 0 and `flask db check` reports no pending changes; `grep -rn "create_all" backend/app | wc -l` → 0; `grep -rn "sqlite" backend | wc -l` → 0; `grep -rhoE "uq_cards_column_id_order_active|uq_board_columns_board_id_order_active|uq_teams_owner_id_personal" backend/migrations | sort -u | wc -l` → 3; `grep -rlE "CREATE EXTENSION IF NOT EXISTS pg_trgm" backend/migrations | wc -l` → ≥ 1; `grep -rl "ix_cards_title_lower_trgm" backend/migrations | wc -l` → ≥ 1; after `flask db upgrade`, `psql "$DATABASE_URL" -tc "SELECT count(*) FROM pg_extension WHERE extname='pg_trgm'"` → 1 and `SELECT count(*) FROM pg_indexes WHERE indexname='ix_cards_title_lower_trgm'` → 1; on the first Railway deploy, run `CREATE EXTENSION IF NOT EXISTS pg_trgm;` manually against the Railway database and record the outcome. Not run: no migration exists and Railway availability of `pg_trgm` is NOT confirmed.

### TC-11 — FLOAT ordering strategy (columns and cards) (moved)
- **Moved to:** server allocation, conflict and rebalance: `guidelines/backend.md` BE-14; storage and unique indexes: `guidelines/database.md` DB-08; client computation (`lib/ordering.ts`): `guidelines/frontend.md` FE-27; rebalance refresh after a move: `guidelines/frontend.md` FE-26.

### TC-20 — Deployment and CORS
- **Rule:** `backend/Procfile` runs `gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --workers 2`, after a release step `flask db upgrade`. The worker class is not specified, so Gunicorn uses its default sync worker. No `Procfile` exists in the repository yet, so the worker configuration is a plan and not a deployed fact. `CORS_ORIGINS` is the exact Vercel production URL (plus `http://localhost:3000` locally); wildcard `*` is forbidden in production. Deploy early: the API and frontend must both be live before feature work reaches 50% of tasks in `tasks.md`.
- **Rationale:** CORS, env-var and PostgreSQL SSL issues only appear on real infrastructure; recording that the worker setup is a plan keeps the performance record (TC-23) honest.
- **Example:** `CORS_ORIGINS=https://sevy.vercel.app`.
- **Verify:** `curl -s -o /dev/null -w "%{http_code}" <api>/api/health` → `200`; `curl -sI -H "Origin: https://evil.example" <api>/api/health | grep -ic access-control-allow-origin` → `0`; `grep -c "gunicorn" backend/Procfile` → ≥ 1. Not run: no `Procfile` and no deployment exist yet.

### TC-23 — Load-test script and performance environment record
- **Rule:** The target "95th percentile response time ≤ 300 ms with 200 concurrent users on one Board" (requirements.md Requirement 14) is measured, never assumed. A repeatable load-test script lives in `backend/tests/load/` as a development-only tool: it adds no runtime dependency, is not listed in `requirements.txt`, and defaults to the Python standard library; any extra package goes to `requirements-dev.txt` only after the TC-02 changelog entry. The script takes the target API URL as an argument (no new environment variable, TC-09), runs a 10-minute window with 200 concurrent virtual users on one Board with 5 Columns and 50 Cards against a deployed or staging API, and computes the P95 from durations measured at the API server (client-side timings alone do not count). Every run appends an environment block to `backend/tests/load/RESULTS.md` with these five fields and the result: **Railway plan**, **Gunicorn worker class and worker count** (as configured in the Procfile, TC-20), **Database plan**, **Script name and version**, **Date**, and the measured **P95 (ms)**. Until a run is recorded the status is "not measured"; a value that was not measured is never written as achieved, and a run that shows more than 300 ms is recorded as "not met".
- **Rationale:** A latency target without a method, a window and an environment cannot be checked, and the number depends on the Railway plan, the worker class and the database plan.
- **Example:** Template line in `RESULTS.md` before any run: `| Date: NOT RECORDED | Script name and version: NOT RECORDED | Railway plan: NOT RECORDED | Gunicorn worker class and worker count: NOT RECORDED | Database plan: NOT RECORDED | P95 (ms): NOT MEASURED | Status: not measured |`.
- **Verify:** `test -f backend/tests/load/RESULTS.md` and `for f in "Railway plan" "Gunicorn worker class" "Database plan" "Script name" "Date" "P95"; do grep -q "$f" backend/tests/load/RESULTS.md || echo "MISSING $f"; done` prints nothing; `grep -ciE "locust|k6|wrk" backend/requirements.txt` → 0. Not run: this check is only meaningful once a measurement exists, and no script or results file exists yet.

---

## 5. Frontend Technical Rules (moved)

### TC-12 — Server vs Client Components and token transport (moved)
- **Moved to:** `guidelines/frontend.md` FE-22 (Server Component pages, `sevy_token` cookie, `middleware.ts`), FE-30 (Guest mode exception) and FE-06 (general `'use client'` rule).

### TC-13 — One API client and typed errors (moved)
- **Moved to:** `guidelines/frontend.md` FE-23 (API client and `ApiError`) and FE-24 (error-to-toast mapping, `lib/toast.ts`).

### TC-14 — Drag-and-drop with optimistic update and rollback (moved)
- **Moved to:** `guidelines/frontend.md` FE-26.

### TC-15 — Notification polling (moved)
- **Moved to:** `guidelines/frontend.md` FE-28.

### TC-16 — Search debounce (moved)
- **Moved to:** `guidelines/frontend.md` FE-29.

---

## 6. Testing Standards

### TC-17 — Backend tests (pytest)
- **Rule:** Every `*_service` function has ≥ 1 success test and ≥ 1 failure test; every route has tests for its success status and, where applicable, `400`, `401`, `403`, `404`. Comments routes must include `201` success, `400` missing content, `401` unauthenticated, `403` non-owner edit/delete. The pytest suite contains the table-driven tests that `backend.md` BE-08 (Access Resolution Table, `401` sweep over `app.url_map`), BE-09 (permission matrix), BE-14 (ordering, conflict, rebalance on PostgreSQL) and `database.md` DB-08/DB-09 (schema, constraint and partial-index tests) require; the test content is owned by those guidelines, this rule only requires the suite to contain it. API-level end-to-end flows (register → login → board → column → card → move → comment) live in `tests/e2e/`. Coverage: ≥ 85% overall and ≥ 90% on every `service.py`.
- **Rationale:** Untested generated code is the main way AI regressions slip through.
- **Example:** `test_create_comment_returns_403_for_non_member`.
- **Verify:** `cd backend && pytest -v --cov=app --cov-fail-under=85` passes; `coverage report --include="app/blueprints/*/service.py" --fail-under=90` passes.

### TC-18 — Component and hook tests (React Testing Library)
- **Rule:** Each file in `components/shared/` has a test covering every variant (`BaseButton`: primary/secondary/destructive; `BaseBadge`: each color; `BaseModal`: open, Escape close, focus return); each hook in `hooks/` has a test; run with `npm test`.
- **Rationale:** Shared components are reused everywhere, so one regression multiplies.
- **Example:** `BaseButton.test.tsx` renders `variant="destructive"` and asserts the destructive class is present.
- **Verify:** `npm test -- --coverage` passes; every `components/shared/*.tsx` and `hooks/use*.ts` has a matching file under `frontend/__tests__/` (script diff → 0 missing).

### TC-19 — Playwright E2E against production
- **Rule:** The suite runs against the live Vercel URL (`PLAYWRIGHT_BASE_URL`). `e2e/auth.spec.ts` covers 4 scenarios: successful login redirect, invalid credentials error, unauthenticated redirect to `/login`, post-logout redirect. Optional fifth scenario in the same file (requirements.md R3.8, R21.11, R21.17; `frontend.md` FE-30): a valid invite link, created through the API, opens `/boards/<id>?invite=<token>` read-only without a redirect to `/login`. `e2e/kanban.spec.ts` covers 8 steps (TG-02). `e2e/pages.spec.ts` visits every route (`/register`, `/login`, `/`, `/boards/[id]`, `/my-tasks`, `/profile`) at desktop and mobile widths. **`waitForTimeout` is forbidden**; use web-first assertions (`expect(locator).toBeVisible()`), `page.waitForResponse`, or `expect.poll`. Each test creates its own user via the API (unique email and unique username) and shares no data. Mobile project runs only `pages.spec.ts` (HTML5 drag-and-drop does not support touch). The HTML report (`playwright-report/`) is committed.
- **Rationale:** Fixed sleeps cause flaky tests; independent data allows repeat runs.
- **Example:** `await expect(page.getByRole('heading', { name: 'To Do' })).toBeVisible()`.
- **Verify:** `grep -rn "waitForTimeout" frontend/e2e | wc -l` → 0; `npx playwright test --repeat-each=3` passes 100%; the report shows all tests passed.

---

## 7. Process Constraints

### TC-21 — AI output is reviewed and the evidence is committed
- **Rule:** Guidelines are written **before** the code that uses them. `specs/CHANGELOG.md` has at least 5 refinement rounds. A round is every entry after the V1 baseline; its heading is the change-management form `## V<N> - YYYY-MM-DD` (the V1 baseline is `## V1 - Initial Release`), and each round carries the labels `**Prompt**`, `**Before**` and `**After**`. The older heading form `## [Round N] — YYYY-MM-DD` is no longer used. `guidelines/VIOLATIONS.md` has ≥ 3 entries, each with: guideline ID, file and line, what the AI produced, the fix. At least one before/after comparison reports a number (e.g. "violations found: 9 → 2").
- **Rationale:** The brief grades critical review, not generation speed; one heading format lets a script count rounds and labels.
- **Example:** "BE-07 broken: `jsonify` used in `cards/routes.py:41` → replaced with `success()`."
- **Verify:** this command counts the rounds and lists any round without the three labels; it exits 0 only if there are ≥ 5 refinement rounds and none is missing a label (not run):
  ```bash
  python -c "import re,sys;t=open('specs/CHANGELOG.md',encoding='utf-8').read();b=[x for x in re.split(r'(?m)^(?=## V\d+ - )',t)[1:] if not x.startswith('## V1 - ')];bad=[x.splitlines()[0] for x in b if not all(l in x for l in ('**Prompt**','**Before**','**After**'))];print(len(b),'refinement rounds; missing labels:',bad);sys.exit(0 if len(b)>=5 and not bad else 1)"
  ```
  `grep -c "^### V-" guidelines/VIOLATIONS.md` ≥ 3; the first commit touching `guidelines/` is earlier than the first commit touching `backend/app/` (`git log --reverse`).

### TC-22 — Commit history reflects the phases
- **Rule:** Commit messages start with a phase prefix: `spec:`, `guidelines:`, `feat(backend):`, `feat(frontend):`, `test:`, `docs:`, `chore(deploy):`. The history contains ≥ 1 commit of each prefix, and no commit message is shorter than 10 characters.
- **Rationale:** The brief grades a meaningful commit history across all phases.
- **Example:** `feat(backend): add cards blueprint with float order positioning`.
- **Verify:** `git log --oneline | grep -cE "^[0-9a-f]+ (spec|guidelines|feat\((backend|frontend)\)|test|docs|chore\(deploy\)):"` equals the commit count; each of the 7 prefixes appears at least once.

---

## 8. Brief Gaps Resolved

| ID | Gap in the brief | Resolution |
|---|---|---|
| TG-01 | JWT is stored in `AuthContext`, but Dashboard and Board Detail are Server Components that cannot read Context | Token transport is owned by `guidelines/frontend.md` FE-22 (the `sevy_token` cookie) |
| TG-02 | "The complete Kanban board journey across all 8 steps" is not enumerated | Steps: (1) log in; (2) create a board; (3) add column "To Do"; (4) add column "Done"; (5) create a card in "To Do"; (6) drag the card to "Done"; (7) reload the page; (8) assert the card is still in "Done" |
| TG-03 | HTML5 drag-and-drop has no touch support | Mobile requirement is layout only (requirements.md Requirement 23); touch dragging is out of scope |
