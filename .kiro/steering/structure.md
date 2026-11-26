---
inclusion: always
---

# Sevy — Structure Steering

Tells Kiro **where files go**, **what files and folders are called**, and **which direction imports run**.
Covers the steering types *architecture patterns* (file ownership, layering, import direction) and *naming conventions* (files, folders, functions, tests); tools, dependencies, deployment and testing thresholds live in `tech.md`; scope and roles live in `product.md`.

**What this file owns:** repository layout and file ownership · file and folder naming · import direction · size limits · test placement · document-file layout · repository hygiene.
**What this file does not own:** backend rules (`guidelines/backend.md`), database rules (`guidelines/database.md`), frontend behavior (`guidelines/frontend.md`), product behavior (`.kiro/specs/task-management-app/requirements.md`). Where a rule used to be repeated here, a one-line reference replaces it.

IDs: `ST-xx`. Every rule has Rule, Rationale, Example and a **Verify** line (command, script, or count). Run all Verify commands from the repository root unless stated otherwise. A Verify line is a specification of a check: no application code exists yet, and none of the Verify commands in this file has been run.

---

## 1. Repository Layout

A single monorepo with two separate projects. The `backend/` and `frontend/` prefixes are required because Flask and Next.js both use a folder called `app/`. The tree is the target layout; only `.kiro/`, `specs/`, `guidelines/` and root files exist today.

```
sevy/
├── .kiro/
│   ├── steering/              product.md  tech.md  structure.md  development-workflow.md  change-management.md
│   ├── specs/<feature>/       requirements.md  design.md  tasks.md  CHANGELOG.md   (working copy)
│   └── references/            assignment reference files
├── specs/                     requirements.md  design.md  tasks.md  CHANGELOG.md   (submission copy)
│                              (CONSISTENCY_AUDIT_REPORT.md is kept here as well)
├── guidelines/                frontend.md  backend.md  database.md  VIOLATIONS.md
├── backend/                   (Flask project root)
│   ├── app/
│   │   ├── __init__.py        create_app(), registers blueprints and error handlers
│   │   ├── config.py          reads environment variables
│   │   ├── extensions.py      db, migrate, jwt, cors instances
│   │   ├── exceptions.py      AppException + typed exceptions (BE-10)
│   │   ├── error_handlers.py  register_error_handlers(app), called from create_app() (BE-11)
│   │   ├── logging_config.py  JSON logger and log_handled_error() (BE-12)
│   │   ├── health.py          GET /api/health
│   │   ├── models/            user.py team.py team_membership.py board.py board_column.py card.py
│   │   │                      card_comment.py notification.py activity_event.py invite_link.py
│   │   ├── utils/             responses.py  ordering.py  auth.py  time.py
│   │   └── blueprints/
│   │       └── <feature>/     __init__.py  routes.py  service.py  schema.py
│   │                          (auth, boards, columns, cards, comments, notifications, analytics, users)
│   ├── migrations/
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── unit/<feature>/    test_<feature>_service.py  test_<feature>_routes.py
│   │   ├── e2e/               test_<flow>.py
│   │   └── load/              load-test script  RESULTS.md   (tech.md TC-23)
│   ├── requirements.txt  requirements-dev.txt  Procfile  .flake8  .env.example
├── frontend/                  (Next.js project root)
│   ├── app/                   layout.tsx  page.tsx  globals.css  login/  register/  boards/[id]/  my-tasks/  profile/
│   ├── components/
│   │   ├── shared/            BaseButton.tsx  BaseBadge.tsx  BaseModal.tsx
│   │   ├── board/             KanbanBoard.tsx  BoardColumn.tsx  ColumnHeader.tsx  CardDragHandle.tsx  BoardCard.tsx  BoardForm.tsx  ColumnForm.tsx
│   │   ├── card/              CardItem.tsx  CardDetailModal.tsx  CardForm.tsx  CardSearch.tsx  MyTaskRow.tsx
│   │   ├── comments/          CommentList.tsx  CommentItem.tsx  CommentForm.tsx
│   │   ├── notifications/     NotificationBell.tsx
│   │   └── layout/            Header.tsx
│   ├── context/               AuthContext.tsx
│   ├── hooks/                 useDragAndDrop.ts  useNotifications.ts  useErrorHandler.ts  useDebouncedValue.ts  useCardSearch.ts  useModalBehavior.ts
│   ├── lib/                   apiClient.ts  errors.ts  toast.ts  ordering.ts
│   ├── types/                 api.ts
│   ├── __tests__/             mirrors components/shared/ and hooks/
│   ├── e2e/                   auth.spec.ts  kanban.spec.ts  pages.spec.ts
│   ├── middleware.ts  playwright.config.ts  .env.example
├── README.md
└── .gitignore
```

Document copies: the working copy of the specs is `.kiro/specs/<feature>/` and `specs/` is the submission copy, so a spec change is made in the working copy first and then copied to `specs/` before it is committed.

Rule ownership by file (one line each, so a rule is looked up in one place): product behavior and the route inventory → `requirements.md` (Appendix A); backend → `guidelines/backend.md`; database → `guidelines/database.md`; frontend → `guidelines/frontend.md`; tools, configuration, deployment, tests, process → `tech.md`; layout and naming → this file. `guidelines/frontend.md` FE-02 must list `MyTaskRow` in `components/card/` (it still lists four `card/` components).

### ST-01 — Fixed top-level layout
- **Rule:** The repository root contains exactly: `.kiro/`, `specs/`, `guidelines/`, `backend/`, `frontend/`, `README.md`, `.gitignore` (plus `.git/`). No application code, `.env*` file, or build output at the root.
- **Rationale:** The brief requires a clean separation of specs, guidelines, backend and frontend.
- **Example:** `package.json` belongs in `frontend/`, never at the root.
- **Verify:** `ls -A | grep -vxE "\.git|\.kiro|specs|guidelines|backend|frontend|README\.md|\.gitignore" | wc -l` → 0.

---

## 2. Architecture Patterns — Backend

### ST-02 — One Blueprint per feature, fixed file set
- **Rule:** `backend/app/blueprints/` contains exactly 8 folders — `auth`, `boards`, `columns`, `cards`, `comments`, `notifications`, `analytics`, `users` — each containing exactly `__init__.py`, `routes.py`, `service.py`, `schema.py`. Each `__init__.py` defines `<feature>_bp = Blueprint('<feature>', __name__, url_prefix='/api')`; all 8 are registered in `create_app()`. Team member routes and Invite Link routes live in the `boards` blueprint; `GET /api/health` lives in `app/health.py`, not in a ninth blueprint. The route inventory is `requirements.md` Appendix A; no route count is fixed here.
- **Rationale:** Predictable structure lets Kiro and reviewers find any route in one hop; the brief grades this exact file set.
- **Example:** `cards_bp` serves `/api/columns/<id>/cards`, `/api/cards/<id>`, `/api/cards/<id>/position`, and `GET /api/cards`; `boards_bp` serves `/api/boards/<id>/members` and `/api/boards/<id>/invite-links`.
- **Verify:** `ls backend/app/blueprints | wc -l` → 8; `for d in backend/app/blueprints/*/; do ls $d | grep -cE "^(__init__|routes|service|schema)\.py$"; done` prints `4` eight times; `grep -c "register_blueprint" backend/app/__init__.py` → 8.

### ST-03 — Strict layering: routes → service → models
- **Rule:** `routes.py` parses input with a schema, calls one `*_service` function and returns the envelope, with no `db.session`, no `.query` and no model imports; `service.py` holds the business rules and the database access and has no `flask` imports (user id and parsed data are passed in as arguments); `schema.py` holds Marshmallow schemas only and has no database access. The detailed rules (handler length, service contents, validation) are owned by `backend.md` BE-02, BE-03 and BE-04.
- **Rationale:** Services that do not know about HTTP are unit-testable without a request context; thin routes keep AI-generated handlers reviewable.
- **Example:** `create_card_route` → `CardCreateSchema().load(...)` → `create_card_service(column_id, data, user_id)` → `success(CardSchema().dump(card), 201)`.
- **Verify:**
  `grep -rnE "db\.session|\.query\b|^from app\.models" backend/app/blueprints/*/routes.py | wc -l` → 0;
  `grep -rnE "^(from|import) flask" backend/app/blueprints/*/service.py | wc -l` → 0;
  `grep -rnE "db\.|^from app\.models" backend/app/blueprints/*/schema.py | wc -l` → 0;
  `flake8 --max-complexity=8 backend/app` exits 0.

### ST-04 — Dependency direction and cross-feature calls
- **Rule:** Allowed imports run one way: `routes → schema, service, utils` · `service → models, exceptions, utils, other blueprints' service.py` · `utils/auth.py` also imports `models` (it loads the user, resolves Team membership and the invite token) · `models → extensions` and `utils/time.py` only (`utc_now`, `database.md` DB-05). A blueprint never imports another blueprint's `routes.py` or `schema.py`. Cross-feature side effects go through the other feature's service function.
- **Rationale:** Prevents circular imports and hidden coupling.
- **Example:** `comments/service.py` calls `notifications.service.create_mention_notifications_service(...)` when a Comment mentions a Team member.
- **Verify:** `grep -rnE "from app\.blueprints\.[a-z_]+\.(routes|schema)" backend/app/blueprints/*/service.py | wc -l` → 0; `grep -rnE "^from app\.(blueprints|exceptions)" backend/app/models | wc -l` → 0; `cd backend && python -c "from app import create_app; create_app()"` exits 0.

### ST-05 — Size limits
- **Rule:** Any `.py` file under `backend/app/` ≤ 250 lines; any `.ts`/`.tsx` file under `frontend/` ≤ 200 lines; each `page.tsx` ≤ 120 lines. When exceeded, extract a function or component.
- **Rationale:** Short files are reviewable and fit a single AI context window.
- **Example:** `KanbanBoard.tsx` delegates a column to `BoardColumn.tsx` and a card to `CardItem.tsx`; `BoardCard.tsx` is the board summary tile on the Dashboard.
- **Verify:** `find backend/app -name "*.py" | xargs wc -l | awk '$1>250 && $2!="total"' | wc -l` → 0; `find frontend/app frontend/components frontend/hooks frontend/lib frontend/context \( -name "*.ts" -o -name "*.tsx" \) | xargs wc -l | awk '$1>200 && $2!="total"' | wc -l` → 0; `wc -l frontend/app/**/page.tsx frontend/app/page.tsx | awk '$1>120 && $2!="total"' | wc -l` → 0.

---

## 3. Architecture Patterns — Frontend

### ST-06 — App Router pages are fixed
- **Rule:** `frontend/app/` contains exactly these routes: `/` (`page.tsx`), `/login`, `/register`, `/boards/[id]`, `/my-tasks`, `/profile`. Card Detail is a modal (`CardDetailModal.tsx`), not a route. Each `page.tsx` composes components and holds no business logic.
- **Rationale:** Matches the brief's page list and keeps pages thin.
- **Example:** `app/my-tasks/page.tsx` fetches `GET /api/cards?assignee=me` and renders `MyTaskRow` rows grouped by board name.
- **Verify:** `find frontend/app -name "page.tsx" | wc -l` → 6.

### ST-07 — Component folders and import boundaries
- **Rule:** `components/shared/` holds only domain-free building blocks (`BaseButton`, `BaseBadge`, `BaseModal`). Files in `shared/` never import `lib/apiClient`, any hook that performs requests, or another `components/` folder. Feature components live in `board/`, `card/` (including `MyTaskRow.tsx`), `comments/`, `notifications/`, `layout/`. Use the `@/` alias for imports; no relative path may climb more than one level (`../../` is forbidden).
- **Rationale:** Shared components stay reusable and testable in isolation.
- **Example:** `CardDetailModal` imports `@/components/shared/BaseModal`, not `../../shared/BaseModal`.
- **Verify:** `grep -rnE "apiClient|from '@/(components/(board|card|comments|notifications|layout)|hooks)" frontend/components/shared | wc -l` → 0; `grep -rn "\.\./\.\./" frontend --include=*.ts --include=*.tsx --exclude-dir=node_modules --exclude-dir=.next | wc -l` → 0; `ls frontend/components | wc -l` → 6.

### ST-08 — Shared components are the only way to render buttons, badges and modals
- **Rule:** The raw `<button` element appears only in `BaseButton.tsx`. `BaseButton` accepts `variant: 'primary' | 'secondary' | 'destructive'`; `BaseBadge` accepts a `color` variant (`'gray' | 'green' | 'yellow' | 'red' | 'blue'`); every form (`BoardForm`, `ColumnForm`, `CardForm`) and `CardDetailModal` renders inside `BaseModal`. Member management and Invite Links are API-only in V1 (requirements.md OD-14), so no member form exists. `/my-tasks` and `/profile` use `BaseButton`.
- **Rationale:** One-off buttons drift in style and accessibility; the brief grades usage on My Tasks and Profile.
- **Example:** Profile save: `<BaseButton variant="primary" type="submit">Save</BaseButton>`; delete card: `variant="destructive"`.
- **Verify:** `grep -rn "<button" frontend/app frontend/components --include=*.tsx | grep -v "components/shared/BaseButton.tsx" | wc -l` → 0; `grep -c "BaseButton" frontend/app/my-tasks/page.tsx frontend/app/profile/page.tsx` → both ≥ 1 (or in their direct child components, for example `components/card/MyTaskRow.tsx`); `grep -L "BaseModal" frontend/components/*/*Form.tsx frontend/components/card/CardDetailModal.tsx` → no output.

### ST-09 — Hooks, context, lib, and types placement
- **Rule:** `hooks/` contains only custom hooks (`use*.ts`); `context/` only React Context providers; `lib/` only framework-free helpers (`apiClient.ts`, `errors.ts`, `toast.ts`, `ordering.ts`); `types/` only TypeScript types (`api.ts`). API response types keep the API's `snake_case` keys unchanged (`frontend.md` FE-25). Required hooks: `useDragAndDrop`, `useNotifications`, `useErrorHandler`, `useDebouncedValue`, `useCardSearch`, `useModalBehavior`.
- **Rationale:** Predictable placement; no mapping layer means one fewer place for bugs.
- **Example:** `hooks/useCardSearch.ts` composes `useDebouncedValue` with the search request (`frontend.md` FE-29).
- **Verify:** `ls frontend/hooks | grep -vE "^use[A-Z][A-Za-z0-9]*\.tsx?$" | wc -l` → 0; `ls frontend/hooks | wc -l` ≥ 6; `ls frontend/hooks | grep -c "useCardSearch"` → 1; `grep -rnE "camelCase|columnId\b" frontend/types | wc -l` → 0.

---

## 4. Naming Conventions

### ST-10 — Naming table
- **Rule:** Names follow this table everywhere; no exceptions without a `CHANGELOG.md` entry. Database naming (model classes, tables, columns, constraints, indexes) is owned by `database.md` DB-01 to DB-04 and is not repeated here.

| Layer | Item | Convention | Example |
|---|---|---|---|
| Python | Modules / folders | `snake_case` | `team_membership.py` |
| Python | Service functions | `<verb>_<noun>_service` | `create_card_service`, `move_card_service` |
| Python | Route functions | `<verb>_<noun>_route` | `move_card_route` |
| Python | Input schemas / output schemas | `<Noun><Action>Schema` / `<Noun>Schema` | `RegisterSchema`, `CardPositionSchema` / `CardSchema` |
| Python | Blueprint variables | `<feature>_bp` | `comments_bp` |
| Python | Constants | `UPPER_SNAKE_CASE` | `ORDER_STEP`, `MIN_GAP` |
| Database | Model classes, tables, columns, constraints, indexes | see `database.md` DB-01 to DB-04 | — |
| API | JSON keys and URL paths | see `backend.md` BE-06 and `requirements.md` Appendix A | — |
| TypeScript | Component files and components | `PascalCase.tsx`, file name = default export | `CardDetailModal.tsx` |
| TypeScript | Hooks | `camelCase`, `use` prefix | `useDragAndDrop.ts` |
| TypeScript | `lib/` files, functions, variables | `camelCase` | `apiClient.ts` |
| TypeScript | Types / interfaces | `PascalCase`, no `I` prefix | `Card`, `ApiError` |
| TypeScript | Constants | `UPPER_SNAKE_CASE` | `SEARCH_DEBOUNCE_MS` |
| Next.js | Route folders | lowercase kebab-case (dynamic `[id]`) | `my-tasks` |
| Env vars | All | `UPPER_SNAKE_CASE`; `NEXT_PUBLIC_` only for values the browser must read | `NEXT_PUBLIC_API_BASE_URL` |
| Tests | pytest | `test_<function>_<outcome>` in `test_<feature>_service.py` / `_routes.py` | `test_create_card_service_rejects_unknown_column` |
| Tests | RTL / Playwright | `<Name>.test.tsx` / `<area>.spec.ts` | `BaseButton.test.tsx`, `kanban.spec.ts` |

- **Rationale:** A reader can predict any name without looking it up; each layer keeps its own idiom.
- **Example:** The route `move_card_route` calls `move_card_service`, which updates the card's position; the model file for Team membership is `team_membership.py`.
- **Verify:**
  `grep -rnP "^def (?!_)(?![a-z0-9_]+_service\()" backend/app/blueprints/*/service.py | wc -l` → 0;
  `grep -rnP "^def (?!_)(?![a-z0-9_]+_route\()" backend/app/blueprints/*/routes.py | wc -l` → 0 (route functions are module-level; decorators sit above them);
  `find frontend/components -name "*.tsx" | grep -vE "/[A-Z][A-Za-z0-9]*\.tsx$" | wc -l` → 0;
  `find frontend/lib -type f | grep -vE "/[a-z][A-Za-z0-9]*\.ts$" | wc -l` → 0;
  `find frontend/app -type d | grep -E "[A-Z]" | wc -l` → 0.

---

## 5. Test Placement

### ST-11 — Tests mirror the source tree
- **Rule:** Every `backend/app/blueprints/<feature>/service.py` has `backend/tests/unit/<feature>/test_<feature>_service.py` and a `test_<feature>_routes.py`; API-level flows live in `backend/tests/e2e/`; the load-test script and its `RESULTS.md` live in `backend/tests/load/` (`tech.md` TC-23); every file in `components/shared/` and `hooks/` has a matching file under `frontend/__tests__/`; every `page.tsx` route is visited by a spec in `frontend/e2e/`.
- **Rationale:** A missing test file is the cheapest signal of untested generated code.
- **Example:** `notifications/service.py` → `tests/unit/notifications/test_notifications_service.py`.
- **Verify:** `for f in backend/app/blueprints/*/service.py; do n=$(basename $(dirname $f)); test -f backend/tests/unit/$n/test_${n}_service.py || echo MISSING $n; done` prints nothing; `ls backend/tests/unit | wc -l` → 8; `ls backend/tests/load | wc -l` ≥ 2; `ls frontend/e2e | wc -l` ≥ 3.

---

## 6. Specs, Guidelines, and Traceability Layout

### ST-12 — Document structure and IDs
- **Rule:**
  - `specs/requirements.md`: each requirement is `### Requirement <N>: <Name>` followed by `#### Acceptance Criteria` with ≥ 1 numbered criterion; criterion IDs are `R<N>.<k>` (Requirement N, criterion k).
  - `specs/design.md`: a table mapping every `R<N>.<k>` criterion ID to a Flask route or Next.js page; it also lists `POST /api/auth/register`, `POST /api/auth/login`, and the Card model (`CardEntity`) with its FLOAT `order` column (`database.md` DB-08).
  - `specs/tasks.md`: every task is `T-<NN>` and references ≥ 1 `R<N>.<k>` criterion ID and the file it creates.
  - `specs/CHANGELOG.md`: the V1 baseline is `## V1 - Initial Release`; each later entry is `## V<N> - YYYY-MM-DD` with `**Prompt**`, `**Before**`, `**After**` (the older `## [Round N]` form is no longer used).
  - `guidelines/*.md`: each guideline carries an ID (`FE-nn`, `BE-nn`, `DB-nn`) and RULE, RATIONALE and EXAMPLE labels in any letter case; no rule text appears in more than one file; `guidelines/VIOLATIONS.md` entries are `### V-nn`.
- **Rationale:** IDs make every link in the requirement → design → task → file chain checkable by script.
- **Example:** `T-14: Implement POST /api/columns/<id>/cards (R6.1) → backend/app/blueprints/cards/routes.py`.
- **Verify:** every `R<N>.<k>` criterion ID of `requirements.md` (the kth numbered criterion of Requirement N, listed by script) appears in `design.md` and `tasks.md` (`comm -23` of the sorted ID lists → empty); `grep -c "^## V[0-9]" specs/CHANGELOG.md` ≥ 6 (the V1 baseline plus at least 5 refinement rounds; the label check is the command in `tech.md` TC-21); the guideline checker below prints one `OK` or `MISSING` line per `### FE-nn`, `### BE-nn` and `### DB-nn` heading and exits 0 only when none is missing (copy and paste it as one line; ASCII only; not run by this file):
  ```bash
  python -c "import re,sys;L=lambda b,k:re.search(r'\*\*'+k,b,re.I) is not None;R=[(f,h,[k for k in ('RULE','RATIONALE','EXAMPLE') if not L(b,k)]) for f in ('frontend','backend','database') for t in [open('guidelines/'+f+'.md',encoding='utf-8').read()] for h,b in [(m.group(1),t[m.end():(re.search(r'(?m)^#{1,3} ',t[m.end():]) or re.search(r'\Z',t[m.end():])).start()+m.end()]) for m in re.finditer(r'(?m)^### ((?:FE|BE|DB)-\d{2})',t)]];[print(f,h,'OK' if not x else 'MISSING '+','.join(x)) for f,h,x in R];print(len(R),'headings');sys.exit(1 if any(x for _,_,x in R) else 0)"
  ```

---

## 7. Repository Hygiene

### ST-13 — `.gitignore` and committed example env files
- **Rule:** `.gitignore` ignores `.env`, `.env.*` (with `!.env.example`), `__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `.next/`, `node_modules/`. `backend/.env.example` and `frontend/.env.example` are committed with every variable from `tech.md` TC-09 and placeholder values only. `playwright-report/` is committed.
- **Rationale:** Real secrets or build output in Git is a permanent leak or noise.
- **Example:** `frontend/.env.example`: `NEXT_PUBLIC_API_BASE_URL=http://localhost:5000` and `API_BASE_URL=http://localhost:5000`.
- **Verify:** `git ls-files | grep -E "(^|/)(\.env($|\.)|__pycache__|\.next/|node_modules/)" | grep -v "\.env\.example$" | wc -l` → 0; `git check-ignore backend/.env frontend/.env.local backend/app/__pycache__ frontend/.next frontend/node_modules | wc -l` → 5; `git ls-files backend/.env.example frontend/.env.example | wc -l` → 2.
