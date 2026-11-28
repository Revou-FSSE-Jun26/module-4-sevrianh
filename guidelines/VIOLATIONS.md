# Guideline Violations Report

This report lists guideline violations found in AI-generated code and documents, with the guideline each one breaks and the fix. Status is stated per entry. Checks were run on 2026-11-28 on the development machine; a "Fixed" entry names how the fix was verified. Entries V-08 to V-10 were found during the V10 and V11 design review of the spec and guideline files, so their file references point at documents, not code.

Guideline IDs: `TC-nn` and `ST-nn` are in `.kiro/steering/tech.md` and `structure.md`; `FE-nn`, `BE-nn`, `DB-nn` are in this folder.

## Entry template

```markdown
### V-nn
- **Guideline ID**: `<ID>`
- **File and Line**: `<path>:<line>`
- **What the AI Produced**: <what was wrong>
- **The Fix**: <what was changed>
- **Status**: Fixed | Pending (and how it was verified, or why it is open)
```

---

## Findings

### V-01
- **Guideline ID**: `TC-04`
- **File and Line**: `backend/tests/unit/auth/test_app_factory.py:5`
- **What the AI Produced**: An unused `rules` local variable remained in the app-factory test, producing Flake8 `F841`.
- **The Fix**: The variable and its route-comprehension expression were removed; the test asserts the health view through `app.view_functions` directly.
- **Status**: Fixed. `flake8 app tests` exits 0 with no output.

### V-02
- **Guideline ID**: `TC-04`
- **File and Line**: `backend/tests/unit/auth/test_route_inventory.py:29`
- **What the AI Produced**: A route-inventory tuple was 101 characters long, above the 100-character limit, producing Flake8 `E501`.
- **The Fix**: The tuple was moved onto its own line within the configured limit.
- **Status**: Fixed. `flake8 app tests` exits 0.

### V-03
- **Guideline ID**: `ST-05`, `FE-05`
- **File and Line**: `frontend/app/register/page.tsx:1`
- **What the AI Produced**: The `/register` page was 145 lines with form state, validation and the submit handler inline, above the 120-line limit for a `page.tsx` and against FE-05 (stateful logic belongs in a hook).
- **The Fix**: State, validation and submit moved to `frontend/hooks/useRegisterForm.ts`. The page now maps a `FIELDS` list to inputs and is 60 lines. A new test file `frontend/__tests__/useRegisterForm.test.tsx` covers validation boundaries, the trimmed-name request, redirect to `/login`, and the error path.
- **Status**: Fixed. Every `page.tsx` is at most 114 lines (`login`); Jest 24 suites and 133 tests pass, including the existing `auth-pages.test.tsx`; `tsc --noEmit` and ESLint report 0 problems.

### V-04
- **Guideline ID**: `ST-11`
- **File and Line**: `backend/tests/unit/comments/`
- **What the AI Produced**: The comments service and routes existed without the mirrored test files `test_comments_service.py` and `test_comments_routes.py`.
- **The Fix**: Both files were added. The route tests assert 201 (2 assertions), 400 (3), 401 (6) and 403 (5), which are the cases the rubric names.
- **Status**: Fixed. Both files exist and the backend suite passes (652 tests).

### V-05
- **Guideline ID**: `ST-11`
- **File and Line**: `backend/tests/unit/notifications/`
- **What the AI Produced**: The notifications implementation existed without `test_notifications_service.py` and `test_notifications_routes.py`.
- **The Fix**: Both files were added (mention, pagination, ownership, mark-read).
- **Status**: Fixed. Both files exist and the backend suite passes.

### V-06
- **Guideline ID**: `ST-11`, `TC-19`
- **File and Line**: `frontend/e2e/`
- **What the AI Produced**: Only `helpers/viewport.ts` existed. The Playwright config and the three spec files were missing.
- **The Fix**: `playwright.config.ts`, `e2e/auth.spec.ts`, `e2e/kanban.spec.ts`, `e2e/pages.spec.ts`, the API helpers and the `e2e` and `test:e2e` npm scripts were added.
- **Status**: Fixed for the files. `waitForTimeout` appears 0 times in `frontend/e2e`. **Not yet verified against a live URL**, because no deployment exists; the suite has not been run against Vercel.

### V-07
- **Guideline ID**: `ST-12`, `TC-21`
- **File and Line**: `README.md`, `backend/tools/`, `specs/`
- **What the AI Produced**: The README, the checker scripts and the submission copy of the spec files were missing.
- **The Fix**: The README was written, `backend/tools/` holds `check_changelog.py`, `check_guidelines.py` and `check_traceability.py`, and `specs/` was synchronised from `.kiro/specs/task-management-app/` (all four files are byte-identical on 2026-11-28).
- **Status**: Fixed. The README still marks deployment, live E2E and screenshots as not done.

### V-08
- **Guideline ID**: `FE-02`, `ST-07`
- **File and Line**: `guidelines/frontend.md:32`, `.kiro/steering/structure.md:124`
- **What the AI Produced**: The design placed an admin-only `AnalyticsPanel` in `components/board/`, but FE-02 did not list it. `structure.md` also carried a stale note that FE-02 still listed four `card/` components, so the three documents disagreed about folder contents.
- **The Fix**: FE-02 and the `structure.md` tree and ST-07 now list `AnalyticsPanel.tsx` in `board/`, the stale note was removed, and the rule for when it renders is the new `FE-33` (`guidelines/frontend.md:444`).
- **Status**: Fixed. The guideline checker reports every `FE-`, `BE-` and `DB-` heading with Rule, Rationale and Example (60 headings, 0 incomplete).

### V-09
- **Guideline ID**: `DB-09`
- **File and Line**: `guidelines/database.md:175`
- **What the AI Produced**: While syncing the V11 index changes, the `cards` row of the DB-09 schema table was merged into the `card_comments` row (a row ending in "and x |"), leaving the Card table definition incomplete.
- **The Fix**: The rows were split, the `cards` row was completed (partial unique index per DB-08 and the trigram index `ix_cards_title_lower_trgm`), and schema-test bullets were added for the 12 foreign-key indexes and the `pg_trgm` extension.
- **Status**: Fixed in the document. The matching schema tests are specified in task 3.4 and have not been shown to pass for the trigram index in this report.

### V-10
- **Guideline ID**: `DB-09`, `BE-05` (requirement R26.3)
- **File and Line**: `.kiro/specs/task-management-app/design.md:346`
- **What the AI Produced**: The design listed R26.3 (an index to support title search) as "Not covered" and proposed no index. Case-insensitive substring search with `LIKE '%term%'` cannot use a B-tree index.
- **The Fix**: Decision D-07 (approved V11) adds the GIN trigram index `ix_cards_title_lower_trgm` on `lower(title)`, created by the initial migration after `CREATE EXTENSION IF NOT EXISTS pg_trgm`. BE-05 requires `lower(title) LIKE` with `\`, `%` and `_` escaped so characters match literally.
- **Status**: Fixed in the spec and guidelines. **Open at deployment:** whether `pg_trgm` can be created on the Railway database is not confirmed and must be checked at the first deploy (`tech.md` TC-10).

### V-11
- **Guideline ID**: `TC-21`, `ST-12`
- **File and Line**: `specs/CHANGELOG.md` (entries V2 to V5)
- **What the AI Produced**: The V2 to V5 entries were written in a Changes/Reason/Impact form without the labels `**Prompt**`, `**Before**` and `**After**`.
- **The Fix**: None applied. Rewriting approved history was rejected; V6 to V11 carry all three labels.
- **Status**: Pending. `py backend\tools\check_changelog.py` reports 10 refinement rounds (5 needed) and lists V2, V3, V4 and V5 as missing labels, so the check exits 1. Fixing it needs an explicit decision to add the labels to those entries.

### V-12
- **Guideline ID**: `TC-22`
- **File and Line**: `git log` (commits `9a2a964`, `f01fdf5`, `aa7b59f`, `83b4cea`, `ef2bf40`, `b2f0ab8`)
- **What the AI Produced**: Several commit messages contain the pasted shell command (`git add ... git commit -m "..."`) instead of a phase-prefixed message. No `test:`, `docs:` or `chore(deploy):` commit exists yet, and `feat(frontend):` is not used.
- **The Fix**: None applied. Rewriting pushed history was not done.
- **Status**: Pending. New commits should use the prefixes of TC-22 (`spec:`, `guidelines:`, `feat(backend):`, `feat(frontend):`, `test:`, `docs:`, `chore(deploy):`). The `chore(deploy):` prefix can only be satisfied once a deployment exists.

---

## Before / after metrics

"Before" values are the figures recorded in the previous version of this report. "After" values were measured on 2026-11-28.

| Metric | Before | After |
| :--- | :--- | :--- |
| Violations recorded | 7 | 12 |
| Violations fixed | 2 | 10 |
| Violations pending | 5 | 2 (V-11, V-12) |
| Backend Flake8 issues | 2 | 0 |
| Backend pytest tests passing | 571 | 652 |
| Backend test coverage | 95.64% | 99.06% |
| Frontend ESLint problems | 0 | 0 |
| Frontend TypeScript errors | 0 | 0 |
| Frontend `.ts`/`.tsx` files over 200 lines | 0 | 0 |
| Frontend `page.tsx` files over 120 lines | 1 | 0 |
| Jest suites passing | 23 of 23 | 24 of 24 |
| Jest tests passing | 127 | 133 |
| Guideline headings missing Rule, Rationale or Example | not recorded | 0 of 60 |

Not shown here: a comparison of AI output quality before and after the guidelines existed. That comparison has not been recorded, so no number is claimed.
