# Guideline Violations Report

This document records real guideline violations discovered during implementation and review.

## Violation Entry Template

```markdown
### V-nn
- **Guideline ID**: `<ID>`
- **File and Line**: `<path/to/file>:<line>`
- **What the AI Produced**: `<description of the violation>`
- **The Fix**: `<description of how it was resolved>`
```

---

## Findings

### V-01
- **Guideline ID**: `TC-04`
- **File and Line**: `backend/tests/unit/auth/test_app_factory.py:5`
- **What the AI Produced**: An unused `rules` local variable remained in the app-factory test, producing a Flake8 `F841` violation.
- **The Fix**: The unused variable and its route-comprehension expression were removed; the test now asserts the health view through `app.view_functions` directly.

### V-02
- **Guideline ID**: `TC-04`
- **File and Line**: `backend/tests/unit/auth/test_route_inventory.py:29`
- **What the AI Produced**: A route-inventory tuple was 101 characters long, exceeding the 100-character PEP 8 limit and producing Flake8 `E501`.
- **The Fix**: The tuple was moved onto its own line and the route inventory was kept within the configured line limit.

### V-03
- **Guideline ID**: `ST-05`
- **File and Line**: `frontend/app/register/page.tsx:1`
- **What the AI Produced**: The `/register` page contains 145 lines, exceeding the guideline limit of 120 lines for a `page.tsx`.
- **The Fix**: Pending. Extract the registration form state and fields into a feature component, keeping the page as a thin route composition.

### V-04
- **Guideline ID**: `ST-11`
- **File and Line**: `backend/tests/unit/comments/`
- **What the AI Produced**: The comments service and routes have implementation files, but the required mirrored test files `test_comments_service.py` and `test_comments_routes.py` are absent.
- **The Fix**: Pending. Add the required comments service and route suites under `backend/tests/unit/comments/` and cover 201, 400, 401, 403, tombstones and soft-deleted Cards.

### V-05
- **Guideline ID**: `ST-11`
- **File and Line**: `backend/tests/unit/notifications/`
- **What the AI Produced**: The notifications implementation exists, but the required mirrored `test_notifications_service.py` and `test_notifications_routes.py` files are absent.
- **The Fix**: Pending. Add mention, pagination, ownership, mark-read and cleanup coverage under `backend/tests/unit/notifications/`.

### V-06
- **Guideline ID**: `ST-11`, `TC-19`
- **File and Line**: `frontend/e2e/`
- **What the AI Produced**: Only `frontend/e2e/helpers/viewport.ts` exists. Playwright configuration, API helpers, and `auth.spec.ts`, `kanban.spec.ts`, and `pages.spec.ts` required by tasks 21.1–21.4 are missing.
- **The Fix**: Pending. Add `playwright.config.ts`, the API helper, the three spec files, and the `test:e2e` npm script.

### V-07
- **Guideline ID**: `ST-12`, `TC-21`
- **File and Line**: `README.md`, `backend/tools/`, `specs/`
- **What the AI Produced**: The README, documentation checker scripts, and submission copies of the final spec files were not present.
- **The Fix**: Pending. Create the README and checker scripts, then copy requirements, design, tasks and changelog into `specs/` unchanged.

---

## Before / After Metrics

| Metric | Before | After |
| :--- | :--- | :--- |
| Total guideline violations | 7 | 4 |
| Backend Flake8 issues | 2 | 0 |
| Backend test coverage (%) | 95.64% | 95.64% |
| Frontend ESLint errors | 0 | 0 |
| Frontend TypeScript errors | 0 | 0 |
| Frontend files > 200 lines | 0 | 0 |
| Frontend pages > 120 lines | 1 | 1 |
| Jest test suites passing | 23/23 | 23/23 |
| Jest tests passing | 127/127 | 127/127 |
| Backend pytest tests passing | 571/571 | 571/571 |
