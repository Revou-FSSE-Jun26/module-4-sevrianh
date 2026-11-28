---
inclusion: fileMatch
fileMatchPattern: "frontend/{app,components,hooks,context,lib,types}/**/*"
---

# Sevy Frontend Guidelines (Next.js + React + TypeScript + Tailwind)

Frontend guidelines for **Sevy**: Next.js 15 App Router, React 19, TypeScript (strict), Tailwind CSS 4.
Six sections: **Component Structure · Naming Conventions · Styling Standards · State Management · Pages, Token Transport and API Client · Board and Feature Interactions**.
Every guideline has **RULE**, **RATIONALE**, and **EXAMPLE**; FE-22 to FE-33 (and the test line added to FE-19) also have a **VERIFY** line (command, test, or count, run from the repository root). IDs are `FE-nn` (FE-01 to FE-33).
Ownership: this file owns Next.js pages, components, client state, UI interactions, the frontend API client (`lib/apiClient.ts`, `lib/errors.ts`, `lib/toast.ts`, `lib/ordering.ts`), token transport (cookie `sevy_token`), route protection (`middleware.ts`), `AuthContext`, drag-and-drop, polling, debounce, error-to-toast mapping, the TypeScript API types, and responsive behavior. FE-22 to FE-31 absorb the frontend rules formerly in `tech.md` TC-11 (client part) and TC-12 to TC-16; `tech.md` is to be reduced to a reference for them, and until then this file is the owner.
Complements `tech.md` (runtime, dependencies, style tooling, deployment, environment, test tooling), `structure.md` (repository layout, import boundaries, size limits, naming), `backend.md` (API contracts: response shapes, status and body policy, the Access Resolution Table, the 400 error string, FLOAT order allocation) and `database.md` (tables and constraints). Those rules are referenced here, not repeated.

---

## 1. Component Structure

### FE-01 — TypeScript function components with an explicit props interface
- **RULE:** Every component is a TypeScript function declaration with an explicit `<Name>Props` interface when it takes props. No class components, no `React.FC`, no `any` (for example `props: any`).
- **RATIONALE:** The props interface is the component's contract. It lets Kiro and teammates compose components without guessing.
- **EXAMPLE:**
```tsx
// components/card/CardItem.tsx
interface CardItemProps {
  card: Card;
  onCardOpen: (cardId: string) => void;
}

function CardItem({ card, onCardOpen }: CardItemProps) { /* ... */ }
```

### FE-02 — Fixed folder structure
- **RULE:** `frontend/components/` has exactly six folders, and a component lives in the folder of the feature that owns it:
  `board/` (KanbanBoard, BoardColumn, ColumnHeader, CardDragHandle, BoardCard = a board's summary tile on the Dashboard, BoardForm, ColumnForm, AnalyticsPanel = the admin-only analytics panel, `components/board/AnalyticsPanel.tsx`, FE-33) ·
  `card/` (CardItem = a card inside a column, CardDetailModal, CardForm, CardSearch, MyTaskRow = one assigned-Card row on `/my-tasks`) ·
  `comments/` (CommentList, CommentItem, CommentForm) ·
  `notifications/` (NotificationBell) ·
  `layout/` (Header) ·
  `shared/` (BaseButton, BaseBadge, BaseModal).
  A component imported from two or more feature folders moves to `shared/` and must become domain-free. A seventh folder, or a new file in `shared/`, needs a `CHANGELOG.md` entry first.
- **RATIONALE:** A reviewer, or Kiro, finds any component in one hop; shared primitives never depend on features (see ST-07).
- **EXAMPLE:** `CardDragHandle.tsx` lives in `board/` because it only exists to make cards draggable between board columns; `BaseBadge.tsx` stays in `shared/` because Dashboard, Board Detail and My Tasks all use it.

### FE-03 — Fixed component anatomy
- **RULE:** Every component file reads in the same order: imports → props interface → component function → `export default <FileName>;` as the **last line**. Components use a default export; hooks and `lib/` files use named exports.
- **RATIONALE:** When every file has the same shape, a reviewer (and the agent) knows exactly where to look.
- **EXAMPLE:**
```tsx
// components/board/BoardCard.tsx
import type { Board } from '@/types/api';

/** Renders one board's summary tile. */
interface BoardCardProps {
  board: Board;
}

function BoardCard({ board }: BoardCardProps) {
  return (
    <article className="rounded-lg bg-surface p-4 shadow-sm">
      <h3 className="text-lg font-semibold text-ink">{board.name}</h3>
    </article>
  );
}

export default BoardCard;
```

### FE-04 — Single responsibility
- **RULE:** One component owns one job.
  1. One top-level component function per file.
  2. A one-line JSDoc directly above the props interface (or above the function if there are no props) states the job in one sentence that does **not** contain the word "and".
  3. Max 200 lines (see ST-05).
  4. Drag-source attributes (`draggable`, `onDragStart`, `onDragEnd`) appear only in `CardDragHandle.tsx`; drop-target attributes (`onDragOver`, `onDrop`) appear only in `BoardColumn.tsx`; drag logic and state live only in `hooks/useDragAndDrop.ts`.
  
  The moment a component both renders data and manages a complex interaction, split it.
- **RATIONALE:** If a component's job cannot be said in one sentence without "and", it is doing too much, and AI-generated components drift toward doing everything.
- **EXAMPLE:** "CardItem renders a card, handles its drag, and opens the modal" becomes three components: `CardItem` (`/** Renders one card inside a column. */`), `CardDragHandle` (`/** Makes its child draggable between columns. */`), and the modal opening wired through `onCardOpen` to `CardDetailModal`.

### FE-05 — Reusable logic goes in a custom hook
- **RULE:** Anything stateful and reused, or involving effects, timers or event listeners, lives in `frontend/hooks/`: drag-and-drop → `useDragAndDrop`, polling → `useNotifications`, error toasts → `useErrorHandler`, search debounce → `useDebouncedValue`, the debounced Card search request → `useCardSearch` (FE-29), Escape key and focus handling → `useModalBehavior`. Files in `app/` and `components/` contain no `useEffect`, `setInterval`, `setTimeout`, or `addEventListener`.
- **RATIONALE:** Copy-pasted `useState`/`useEffect` blocks drift apart and leak timers; a hook is written, cleaned up, and tested once.
- **EXAMPLE:** `NotificationBell` calls `const { notifications, unreadCount } = useNotifications();` and only renders the badge.

### FE-06 — Server Components by default
- **RULE:** Default to Server Components. Add `'use client'` only when the component needs interactivity (`onClick`, `onChange`, form state) or a browser API (`useState`, `useEffect`, `window`, `localStorage`). Every file that starts with `'use client'` must contain at least one of those triggers; `app/page.tsx` and `app/boards/[id]/page.tsx` never contain it (see FE-22).
- **RATIONALE:** Server Components ship no JavaScript and fetch data next to where it is rendered; a stray `'use client'` silently moves a whole subtree to the browser.
- **EXAMPLE:** `BoardCard` (a static summary tile) stays a Server Component; `KanbanBoard` starts with `'use client'` because it holds drag state.

---

## 2. Naming Conventions

### FE-07 — File and identifier names
- **RULE:** Component files are PascalCase `.tsx`, and the file name equals the function name equals the default export (`CardDetailModal.tsx`). Hook files are camelCase with a `use` prefix and a named export of the same name (`useDragAndDrop.ts`). Pages are `app/<route>/page.tsx` and their function is `<Route>Page` (`DashboardPage`, `BoardDetailPage`, `MyTasksPage`, `ProfilePage`, `LoginPage`, `RegisterPage`). Mirrors ST-10.
- **RATIONALE:** A reader can predict a name without opening a file, and search-by-name always lands on the right one.
- **EXAMPLE:** `app/boards/[id]/page.tsx` contains `async function BoardDetailPage(...)` and ends with `export default BoardDetailPage;`.

### FE-08 — Props interface = component name + `Props`
- **RULE:** The props interface is named `<ComponentName>Props`, is declared in the component file, and is the only interface declared in a component file. Domain types (`Board`, `Column`, `Card`, `Comment`, `Notification`, `User`) live in `types/api.ts`.
- **RATIONALE:** Local props stay private to the component, and domain types have exactly one definition shared by all components.
- **EXAMPLE:** `BoardCardProps` in `BoardCard.tsx`; `Board` in `types/api.ts`.

### FE-09 — Event handler names
- **RULE:** Handler **props** are named `on<Subject><Verb>`: `onCardMove`, `onCommentAdd`, `onNotificationRead`, `onBoardCreate`. Handler **functions** inside a component are named `handle<Subject><Verb>`. JSX attributes receive a `handle*` function or a forwarded `on*` prop; inline arrow functions in JSX attributes are forbidden.
- **RATIONALE:** The prefix tells a reader whether a function is passed in or defined here; named handlers are testable and show up in stack traces.
- **EXAMPLE:** `<BoardColumn column={column} onCardMove={handleCardMove} />`

---

## 3. Styling Standards

### FE-10 — Tailwind utilities only
- **RULE:** Styling is Tailwind utility classes only — never inline `style={{ }}`, CSS modules, or CSS-in-JS. `app/globals.css` is the only stylesheet; it contains `@import "tailwindcss";` and one `@theme` block.
- **RATIONALE:** One styling system means one place to look and a consistent bundle.
- **EXAMPLE:** `<section className="w-72 shrink-0 rounded-lg bg-surface-muted p-3">` instead of `style={{ width: 288 }}`.

### FE-11 — No magic numbers or arbitrary values
- **RULE:** Use the Tailwind spacing and size scale (`mt-3`, `w-72`, `gap-4`); arbitrary values (`mt-[13px]`, `w-[347px]`, `text-[17px]`, `bg-[#fff]`) are forbidden.
- **RATIONALE:** Arbitrary values bypass the design system and are the first thing AI-generated UI reaches for.
- **EXAMPLE:** Kanban column width is `w-72` (18 rem), never `w-[290px]`.

### FE-12 — Sevy palette: semantic tokens only
- **RULE:** All colors are defined once in the `@theme` block of `app/globals.css` and used through the semantic utilities below (`bg-primary`, `text-ink`, `border-line`, …). The default Tailwind palette (`bg-blue-600`, `text-slate-500`) and raw hex values are forbidden in `app/` and `components/`. Solid fills that carry white text must meet WCAG AA (≥ 4.5:1).

  **Brand palette** (the nine Sevy swatches; each token is the swatch's start color, the swatch end color is used only as a gradient end stop):

  | Token | Hex | Swatch gradient |
  |---|---|---|
  | `brand-violet` | `#8A8DFB` | `#8A8DFB → #7A87F2` |
  | `brand-periwinkle` | `#6D7BEC` | `#6D7BEC → #748DD3` |
  | `brand-sky` | `#7BAAD6` | `#7BAAD6 → #97C6D7` |
  | `brand-mint` | `#B8E2D8` | `#B8E2D8 → #D8EDE5` |
  | `brand-mist` | `#F2FAF5` | `#F2FAF5 → #F4F5EE` |
  | `brand-linen` | `#F1EFEB` | `#F1EFEB → #DFE7F3` |
  | `brand-ice` | `#CEDDF7` | `#CEDDF7 → #ABC4F8` |
  | `brand-cornflower` | `#97B3F8` | `#97B3F8 → #7692F1` |
  | `brand-blue` | `#5876EC` | `#5876EC → #6F8BF0` |

  **Semantic tokens** (what components use):

  | Token | Hex | Use |
  |---|---|---|
  | `canvas` | `#F2FAF5` | Page background (`brand-mist`) |
  | `surface` | `#FFFFFF` | Cards, modals, inputs |
  | `surface-muted` | `#DFE7F3` | Kanban column background (end of the `brand-linen` swatch) |
  | `line` | `#CEDDF7` | Borders and dividers (`brand-ice`) |
  | `ink` | `#1E2352` | Primary text |
  | `ink-muted` | `#55608A` | Secondary text |
  | `primary` | `#4A68E0` | Primary buttons, links, focus ring (`brand-blue` darkened for AA contrast) |
  | `primary-hover` | `#3F5BD6` | Primary hover |
  | `secondary` | `#CEDDF7` | Secondary buttons (text `ink`) |
  | `secondary-hover` | `#ABC4F8` | Secondary hover |
  | `accent` | `#6D7BEC` | Highlights, active column, drop-target outline |
  | `success` / `success-soft` | `#1B7F68` / `#D8EDE5` | Success text and icons / badge background |
  | `warning` / `warning-soft` | `#B45309` / `#FBEFCF` | Warning text and icons / badge background |
  | `danger` / `danger-soft` | `#D92D20` / `#FDE3E1` | Destructive buttons, errors / badge background |
  | `info-soft` | `#CEDDF7` | Blue badge background |

  Badge color variants map to: `gray` → `bg-surface-muted text-ink-muted`; `blue` → `bg-info-soft text-ink`; `green` → `bg-success-soft text-ink`; `yellow` → `bg-warning-soft text-ink`; `red` → `bg-danger-soft text-ink`. Brand gradient: `bg-linear-to-r from-brand-violet via-brand-blue to-brand-sky`, allowed only in `components/layout/` and the `login` / `register` pages.

  Contrast targets (approximate, recompute if a hex changes): `text-white` on `bg-primary` ≈ 4.8:1; `text-white` on `bg-danger` ≈ 4.8:1; `text-ink` on `bg-surface` ≈ 14.8:1; `text-ink-muted` on `bg-surface` ≈ 6.1:1; `text-ink-muted` on `bg-surface-muted` ≈ 4.9:1.
- **RATIONALE:** One palette source keeps every screen on-brand and lets a re-theme be a one-file change; AA contrast keeps text readable on the soft Sevy backgrounds.
- **EXAMPLE:**
```css
/* app/globals.css */
@import "tailwindcss";
@theme {
  --color-brand-violet: #8A8DFB;
  --color-brand-blue: #5876EC;
  --color-brand-sky: #7BAAD6;
  --color-canvas: #F2FAF5;
  --color-surface: #FFFFFF;
  --color-surface-muted: #DFE7F3;
  --color-line: #CEDDF7;
  --color-ink: #1E2352;
  --color-ink-muted: #55608A;
  --color-primary: #4A68E0;
  --color-primary-hover: #3F5BD6;
  /* ...remaining tokens from the table */
}
```
  `BaseButton` primary variant: `'bg-primary text-white hover:bg-primary-hover'`.

### FE-13 — Mobile-first
- **RULE:** Base classes target a 375 px screen; larger screens add `sm:`, `md:`, `lg:` overrides. `max-*:` variants are forbidden. Interactive controls are at least 44 px tall (`min-h-11`). The Kanban board scrolls horizontally inside its own container; the page body never scrolls sideways.
- **RATIONALE:** The brief requires a usable mobile layout with no cut-off or overlapping content (NFR-03).
- **EXAMPLE:** `<div className="flex gap-4 overflow-x-auto p-4 md:p-6">` wraps columns; each column is `w-72 shrink-0`.

### FE-14 — Utility class order
- **RULE:** Class order is whatever `prettier-plugin-tailwindcss` outputs (Tailwind's official order: layout → box model → background and border → typography → effects, with state and responsive variants last). Never hand-order classes; run Prettier.
- **RATIONALE:** A tool-enforced order cannot drift between generations and keeps diffs small. A hand-written "layout → spacing → sizing → typography → color → interactive" order cannot be checked by any tool, so the plugin is the single authority.
- **EXAMPLE:** `className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary-hover"`

### FE-15 — Literal class names only
- **RULE:** Every Tailwind class appears as a complete literal string. Never build a class by concatenation or interpolation (`bg-${color}`). Variants (BaseButton, BaseBadge) are lookup objects of full literals.
- **RATIONALE:** Tailwind finds classes by scanning source text; assembled names are silently not generated.
- **EXAMPLE:**
```tsx
const variantClasses: Record<ButtonVariant, string> = {
  primary: 'bg-primary text-white hover:bg-primary-hover',
  secondary: 'bg-secondary text-ink hover:bg-secondary-hover',
  destructive: 'bg-danger text-white hover:opacity-90',
};
```

### FE-16 — Visible interactive states
- **RULE:** Every interactive element shows hover, keyboard-focus and disabled states. `BaseButton` defines `hover:`, `focus-visible:ring-2` and `disabled:`. `outline-none` is allowed only together with a `focus-visible:ring-*` class.
- **RATIONALE:** Keyboard users must see where they are, and disabled controls must look disabled (NFR-05).
- **EXAMPLE:** `'focus-visible:ring-2 focus-visible:ring-primary disabled:opacity-50 disabled:cursor-not-allowed'`.

### FE-17 — One typeface, scale-based type
- **RULE:** One font family, loaded with `next/font/google` in `app/layout.tsx` (Inter) and exposed as `font-sans`. Text sizes come from the scale: page title `text-2xl font-semibold`, section heading `text-lg font-semibold`, body `text-sm` or `text-base`, meta `text-xs`.
- **RATIONALE:** A short, fixed type scale keeps screens consistent and avoids layout shift from web-font loading.
- **EXAMPLE:** `<h1 className="text-2xl font-semibold text-ink">My Tasks</h1>`

---

## 4. State Management

### FE-18 — Local UI state uses `useState`
- **RULE:** Local UI state (input values, modal open/closed, which column is hovered during a drag) uses `useState` in the lowest component that needs it, lifted only to the nearest common parent. `useReducer` and browser storage (`localStorage`, `sessionStorage`) are not used; the only browser-storage mechanism is the `sevy_token` cookie written by `AuthContext` (FE-22).
- **RATIONALE:** Keeping state next to its use keeps components simple; the App Router's server fetching removes the need for a client store.
- **EXAMPLE:** `CardForm` holds `const [title, setTitle] = useState('');`; `Header` holds `const [isMenuOpen, setIsMenuOpen] = useState(false);`.

### FE-19 — Cross-page state uses one React Context
- **RULE:** The only React Context is `context/AuthContext.tsx`, exporting `AuthProvider` and `useAuth()`; its value is `{ user, token, isAuthenticated, login, logout, updateUser }`. `user` is the safe `User` of FE-25 (`id`, `name`, `username`, `email`, `created_at`; never password data) or `null`; `isAuthenticated` is true when `token` is not `null`.
  - `login(token, user)` is called with `access_token` and `user` of the login response; it stores both and writes the cookie `sevy_token` with `path=/`, `SameSite=Lax` and `max-age=3600` (FE-22).
  - `logout()` clears `user`, `token` and the cookie, then redirects to `/login`.
  - `updateUser(user)` replaces the stored `user` and leaves `token` unchanged. It is the only way profile data changes in context.
  - `/profile` keeps its inputs controlled and pre-populated from `useAuth()` (FE-21), sends `PATCH /api/users/me` with only `name` and `email` (the `username` is shown read-only), and after a successful save calls `updateUser` with the `user` returned by the API and shows a success toast.

  Board, card, comment and notification data are never global. No third-party state library (TC-03 in `tech.md`).
- **RATIONALE:** Identity is the only state every page needs; everything else is fetched per page. One explicit `updateUser` keeps the Header and the Profile form from showing different names after a save.
- **EXAMPLE:** `/profile` pre-populates `useState(user?.name ?? '')` from `useAuth()`, then runs `updateUser(response.user)`; `NotificationBell` keeps its own list through `useNotifications`.
- **VERIFY:** RTL test: `login(token, user)` sets `isAuthenticated` true and writes a `sevy_token` cookie with `max-age=3600`; `logout()` clears context and cookie. RTL test: saving a new name on `/profile` calls `updateUser`, and `Header` and the Profile form show the new name without a reload. `grep -rn "createContext" frontend --include=*.ts --include=*.tsx --exclude-dir=node_modules --exclude-dir=.next | wc -l` → `1`.

### FE-20 — Server data flows down as props
- **RULE:** Server Components fetch with `lib/apiClient.ts` and pass data to Client Components as props. A Client Component copies props into state only when it needs an optimistic copy (`useState(initialBoard)` in `KanbanBoard`). After a non-optimistic mutation (create board, column, card, comment) it calls `router.refresh()`; it does not refetch in an effect.
- **RATIONALE:** One source of truth (the server) with the minimum client state to make drag-and-drop feel instant.
- **EXAMPLE:** `app/boards/[id]/page.tsx` calls `apiClient.get`, then renders `<KanbanBoard initialBoard={board} />`; `ColumnForm` calls `router.refresh()` after `POST /api/boards/<id>/columns`.

### FE-21 — Forms use controlled inputs
- **RULE:** Every `<input>`, `<textarea>` and `<select>` is controlled (`value` + `onChange`, or `checked` + `onChange` for checkboxes) and backed by `useState`. Client-side validation runs on submit and mirrors the server rules (valid email, password ≥ 8 characters, username 3–30 letters, digits or underscore, non-empty names; limits in backend.md BE-05). Edit forms pre-populate by initialising state from props or `useAuth()`; `defaultValue` is forbidden.
- **RATIONALE:** The brief requires controlled inputs and client-side validation; pre-populated forms must stay in sync with state.
- **EXAMPLE:** `/register`: `const [password, setPassword] = useState('');` with `value={password}` and `onChange={handlePasswordChange}`; submit is blocked with an inline error while `password.length < 8`.

---

## 5. Pages, Token Transport and API Client

### FE-22 — Server Component pages and token transport
- **RULE:** `app/page.tsx` (Dashboard) and `app/boards/[id]/page.tsx` (Board Detail) are Server Components with no hooks; FE-06 owns the general `'use client'` rule and is not repeated here. They read the JWT from the `sevy_token` cookie with `cookies()`, fetch with `lib/apiClient.ts` (FE-23), and pass the data as props to Client Components. `KanbanBoard.tsx` is the first Client Component and owns drag state (FE-26).
  - `app/layout.tsx` is a Server Component. When the cookie exists it fetches `GET /api/users/me` and passes `initialToken` and `initialUser` to `AuthProvider`; both are `null` when there is no cookie or the call returns 401. This is how a reload keeps the user signed in.
  - `AuthContext` writes the JWT to the cookie `sevy_token` with `path=/`, `SameSite=Lax` and `max-age=3600` (the token expiry) on login and clears it on logout (FE-19). The cookie cannot be HttpOnly because browser JavaScript writes it (requirements.md OD-10).
  - `middleware.ts` redirects a request without the `sevy_token` cookie for `/`, `/boards/*`, `/my-tasks` and `/profile` to `/login`, with the single Guest exception defined in FE-30.
  - A server page that receives an `ApiError` shows no toast: 401 → `redirect('/login')`, 404 → `notFound()`, 403 → a permission-denied state. FE-30 changes this for Guest mode.
  - Logout is stateless: the Frontend clears context and cookie and redirects to `/login`; an unexpired JWT stays valid at the API until it expires.
- **RATIONALE:** Server Components cannot read React Context; without the cookie the Dashboard cannot be fetched on the server and a reload would log the user out.
- **EXAMPLE:** `page.tsx` calls `apiClient.get('/api/boards', { token })` with `token` from `cookies()`; `<KanbanBoard initialBoard={board} />` is the first Client Component.
- **VERIFY:** `grep -l "use client" frontend/app/page.tsx "frontend/app/boards/[id]/page.tsx"` → no output; `grep -c "cookies()" frontend/app/page.tsx` → ≥ `1`. Playwright: an unauthenticated visit to `/` lands on `/login`; an unauthenticated visit to `/boards/<id>` without further parameters lands on `/login`; reloading `/boards/<id>` while signed in stays on the board; after logout `/` redirects to `/login` and the `sevy_token` cookie is gone.

### FE-23 — One API client and `ApiError`
- **RULE:** All HTTP calls go through `lib/apiClient.ts` (named export `apiClient` with `get`, `post`, `patch`, `delete`); `fetch(` appears nowhere else.
  - **Base URL:** `API_BASE_URL` on the server, `NEXT_PUBLIC_API_BASE_URL` in the browser.
  - **Authorization:** the caller passes the JWT in the request options (`{ token }`: Server Components read it with `cookies()`, Client Components take it from `useAuth()`). The client attaches `Authorization: Bearer <token>` when a token is given and the request is not in Guest mode. In Guest mode it sends no `Authorization` header and attaches the invite token only as FE-30 defines; it never attaches the invite token to any other request.
  - **Success:** on 2xx it unwraps and returns `data`.
  - **Failure:** on any non-2xx response it throws `ApiError` (`lib/errors.ts`) with `statusCode` set to the HTTP status and `message` set to the response `error`, which is always one string (backend.md BE-07; a 400 validation message is already one normalized string, BE-04). When the body has no string `error` (for example a proxy error page), `message` is `Request failed`. When no HTTP response is received (network failure, timeout, CORS block) it throws `ApiError` with `statusCode` `0`.
  - **Shape of `ApiError`:** exactly two fields, `statusCode: number` and `message: string`. There is no field-keyed object and no extra error property.

  Response shapes are owned by backend.md BE-06 and BE-07; the client types are FE-25.
- **RATIONALE:** A single choke point makes auth headers, error shape and toasts uniform, and one error string needs no per-field parsing on the client.
- **EXAMPLE:** `throw new ApiError(res.status, body.error);` and, when `fetch` itself rejects, `throw new ApiError(0, 'Network error');`.
- **VERIFY:** `grep -rn "fetch(" frontend/app frontend/components frontend/hooks frontend/context | wc -l` → `0`; `grep -rniE "fieldErrors|field-keyed" frontend --include=*.ts --include=*.tsx --exclude-dir=node_modules --exclude-dir=.next | wc -l` → `0`; `grep -c "statusCode" frontend/lib/errors.ts` → ≥ `1`. Jest test for `apiClient`: a mocked 404 with `{"error": "x"}` throws `ApiError` with `statusCode` 404 and `message` `x`; a rejected `fetch` throws `ApiError` with `statusCode` 0; a 2xx returns the unwrapped `data`; the invite-token rules of FE-30 hold.

### FE-24 — Error-to-toast mapping
- **RULE:** `hooks/useErrorHandler.ts` returns `handleError(error: unknown)`, which maps an `ApiError` to one toast. A value that is not an `ApiError` gets the generic toast.

| `statusCode` | Toast text | Extra action |
|---|---|---|
| 401 | "Session expired, please log in" | `logout()` (clears context and cookie), redirect to `/login` |
| 403 | "You don't have permission" | none |
| 404 | "Not found" | none |
| 400, 409 | the `message` of the `ApiError` (the server string) | none |
| 500 or higher, and `0` (no response received) | "Something went wrong. Try again." | none |

  Any other non-2xx status gets the generic toast of the last row. The login request is the exception for 401: `/login` shows "Invalid credentials" (the API string) inline next to the form and does not call the 401 branch of `handleError`. Guest mode never calls the 401 branch (FE-30). Toasts are shown only through `lib/toast.ts`, which wraps `toast.success()`, `toast.error()` and `toast.loading()` from `react-hot-toast`; only `lib/toast.ts` and `app/layout.tsx` (the `<Toaster />`) import that package.
- **RATIONALE:** One mapping gives every failure the same wording, and the generic text for status 0 hides transport details from users.
- **EXAMPLE:** `PATCH /api/cards/<id>/position` answers 409 `{"error": "Order already in use"}` → toast "Order already in use"; the server is unreachable → `statusCode` 0 → toast "Something went wrong. Try again."
- **VERIFY:** `grep -rn "react-hot-toast" frontend --include=*.ts --include=*.tsx --exclude-dir=node_modules --exclude-dir=.next | grep -v "lib/toast.ts\|layout.tsx" | wc -l` → `0`. RTL test for `useErrorHandler` covers every row of the table (401, 403, 404, 400, 409, 500, and `statusCode` 0), including the 401 redirect and cookie clearing; a test shows a 401 from the login request shows "Invalid credentials" inline and no session-expired toast.

### FE-25 — API types in `types/api.ts`
- **RULE:** `types/api.ts` holds TypeScript types only. Keys keep the API's `snake_case` unchanged and there is no key-mapping layer (ST-09). These types are defined; the shapes themselves are owned by backend.md BE-06 and BE-07 and are not redefined here. Timestamps are ISO strings.
  - `User`: `id`, `name`, `username`, `email`, `created_at`.
  - `Assignee`: `id`, `name`, `username`.
  - `Card` (a Card nested in a Board response): `id`, `title`, `description`, `order`, `column_id`, `assignee_id`, `assignee`, `created_by_id`, `completed_at`, `created_at`, `updated_at`.
  - `CardListItem` (search and My Tasks item): `id`, `title`, `order`, `column_id`, `column_name`, `board_id`, `board_name`, `assignee_id`, `assignee`.
  - `Comment`: `id`, `card_id`, `parent_id`, `author_id`, `content`, `is_deleted`, `created_at`, `updated_at`.
  - `Notification` (one item): `id`, `type`, `message`, `is_read`, `created_at`, `comment_id`, `card_id`, `board_id`.
  - `NotificationPage`: `items`, `page`, `per_page`, `total`, `total_pages`, `unread_count`.
  - Supporting types: `Board`, `Column`, `BoardDetail`, `LoginResult` (`access_token`, `token_type`, `expires_in`, `user`) and `MoveCardResult` (`card`, `rebalanced`).
- **RATIONALE:** One definition per shape, mirroring the API exactly, means a renamed key is a compile error instead of a runtime `undefined`.
- **EXAMPLE:**
```ts
// types/api.ts
export interface User {
  id: string;
  name: string;
  username: string;
  email: string;
  created_at: string;
}

export interface Assignee {
  id: string;
  name: string;
  username: string;
}

export interface Card {
  id: string;
  title: string;
  description: string;
  order: number;
  column_id: string;
  assignee_id: string | null;
  assignee: Assignee | null;
  created_by_id: string;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CardListItem {
  id: string;
  title: string;
  order: number;
  column_id: string;
  column_name: string;
  board_id: string;
  board_name: string;
  assignee_id: string | null;
  assignee: Assignee | null;
}

export interface Comment {
  id: string;
  card_id: string;
  parent_id: string | null;
  author_id: string;
  content: string;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
}

export interface Notification {
  id: string;
  type: 'mention';
  message: string;
  is_read: boolean;
  created_at: string;
  comment_id: string;
  card_id: string;
  board_id: string;
}

export interface NotificationPage {
  items: Notification[];
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
  unread_count: number;
}
```
- **VERIFY:** `grep -cE "^export interface (User|Card|CardListItem|Comment|Notification|NotificationPage) " frontend/types/api.ts` → `6`; `grep -rnE "columnId|createdAt|assigneeId|boardName|unreadCount" frontend/types | wc -l` → `0`; `grep -c "username" frontend/types/api.ts` → ≥ `1`; `npx tsc --noEmit` exits 0 from `frontend/`.

---

## 6. Board and Feature Interactions

### FE-26 — Drag-and-drop with optimistic update and rollback
- **RULE:** `hooks/useDragAndDrop.ts` owns the board state copy (`useState(initialBoard)`, FE-20) and uses only native HTML5 drag-and-drop events (`draggable`, `dragstart`, `dragover`, `drop`); where the attributes may appear is fixed by FE-04. On drop it:
  1. remembers the dragged Card's original `column_id` and `order`, computes the new `order` with `lib/ordering.ts` (FE-27) from the neighbours in the target Column, and updates local state immediately;
  2. calls `PATCH /api/cards/<id>/position` with `{ column_id, order }`;
  3. on success replaces the Card with `card` from the response and, when `rebalanced` is `true`, calls `router.refresh()`;
  4. on any `ApiError` restores the original `column_id` and `order` in state and shows the error toast of FE-24. A 409 order conflict is rolled back the same way and shows the server message.

  When a new `initialBoard` prop arrives after `router.refresh()` (rebalance, or a create through FE-20), the hook replaces its state with it. Drag is unavailable in Guest mode (FE-30). Request and response shapes: backend.md BE-07 and BE-14.
- **RATIONALE:** Instant feedback with guaranteed consistency on failure is the stated behaviour; a `useState` copy would otherwise ignore the fresh server data a refresh brings.
- **EXAMPLE:** The server returns 403 → the Card visibly snaps back to its source Column. The server returns 409 `Order already in use` → the Card snaps back and the toast shows that text.
- **VERIFY:** RTL test with a mocked failing `fetch` (403, 409, and `statusCode` 0) asserts the state equals the pre-drop state; RTL test: a success response with `rebalanced: true` calls `router.refresh()` once and `false` does not; `grep -rln "draggable" frontend/app frontend/components | grep -v "CardDragHandle.tsx" | wc -l` → `0`; `grep -rln "onDrop" frontend/app frontend/components | grep -v "BoardColumn.tsx" | wc -l` → `0`; Playwright drag test passes and the Card is still in the target Column after `page.reload()`.

### FE-27 — Client-side `order` computation
- **RULE:** `lib/ordering.ts` (framework-free, named exports) exports `ORDER_STEP = 1024.0` and `computeOrder(prev: number | null, next: number | null): number`, with the same rules as backend.md BE-14: no neighbours → `1024.0`; append (`next` is `null`) → `prev + 1024.0`; insert at head (`prev` is `null`) → `next / 2`; insert between → `(prev + next) / 2`. The result is always greater than 0. The neighbours are the other displayed Cards of the target Column (the dragged Card excluded). The client never rebalances; the server rebalances and reports it with `rebalanced` (FE-26).
- **RATIONALE:** The server validates `order > 0` and rejects an equal `order`, so the client must apply the same arithmetic to propose a valid slot.
- **EXAMPLE:** Cards at `1024.0` and `2048.0`; dropping between them submits `1536.0`.
- **VERIFY:** Jest unit test: inserting at the head 60 times in a row gives values that stay strictly increasing in list order and all greater than 0; one test per rule (empty, append, head, between).

### FE-28 — Notification polling and the bell
- **RULE:** `hooks/useNotifications.ts` polls `GET /api/notifications` every `30_000` ms (constant `NOTIFICATION_POLL_MS`) with `setInterval`, clears the interval in the effect cleanup, and does not poll when `isAuthenticated` is false. The hook keeps the latest `NotificationPage` (FE-25) and returns `unreadCount` taken from `unread_count` of the payload, never from the length of `items`. A polling failure keeps the previous page and shows no toast, except 401, which follows FE-24. `NotificationBell.tsx` shows `unreadCount` in a badge and hides the badge when it is 0. Each item links to its Board and Card as `/boards/<board_id>?card=<card_id>` (using `board_id` and `card_id` of the item), and a click marks the item read through `PATCH /api/notifications/<id>/read`. `Header` shows the bell on every authenticated page; Guest mode has no bell (FE-30).
- **RATIONALE:** Leaked intervals cause duplicate requests and test flakiness, and `unread_count` counts every unread Notification of the user, not only the page shown.
- **EXAMPLE:** Twelve unread Notifications with `per_page` 10 → `items` has 10 entries and the badge shows `12`. Zero unread → no badge.
- **VERIFY:** Jest fake-timer test: 0 calls at 29 999 ms, 1 call at 30 000 ms, 0 additional calls after unmount; a test with `isAuthenticated` false makes 0 calls; RTL test: the badge shows `unread_count` (not `items.length`) and is absent at 0; a test asserts the link `href` of an item uses `board_id` and `card_id`; `grep -rnE "setInterval|clearInterval" frontend/app frontend/components | wc -l` → `0`.

### FE-29 — Card search with debounce
- **RULE:** The search input on `/boards/[id]` (`CardSearch.tsx`, controlled, FE-21, `maxLength` 100) uses `hooks/useDebouncedValue.ts` with `SEARCH_DEBOUNCE_MS = 300`, composed with the request in `hooks/useCardSearch.ts`.
  - No request is sent for empty or whitespace-only input; the trimmed term is sent.
  - The request is `GET /api/cards?q=<term>`. By default the UI searches the current Board and supplies `board_id`; the API also accepts `q` alone, which searches every Board the user can access (backend.md BE-05).
  - Search matches Card titles only, case-insensitively.
  - Results are `CardListItem` rows (FE-25): `title`, `column_name` in a `BaseBadge`, and a link to `/boards/<board_id>?card=<id>`. A 200 with an empty list shows an empty state.
  - A response for an older term is ignored when a newer term is pending.
  - Guest mode has no search (FE-30).
- **RATIONALE:** The brief requires a 300 ms debounce; a named constant makes it testable; a hook keeps the timer and request out of the component (FE-05).
- **EXAMPLE:** Typing "dep" then "deploy" within 300 ms sends one request, `GET /api/cards?q=deploy&board_id=<uuid>`.
- **VERIFY:** Jest fake-timer test: 299 ms → 0 requests; 300 ms → exactly 1 request; an empty input and a whitespace-only input send 0 requests; a test asserts the query string for the default scope contains `board_id` and for the `q`-only scope does not; `grep -rn "SEARCH_DEBOUNCE_MS = 300" frontend/hooks frontend/lib frontend/components | wc -l` → `1`.

### FE-30 — Guest mode on an invite link
- **RULE:** A valid Guest link opens `/boards/[id]?invite=<token>`. API behavior is owned by backend.md BE-08; the frontend rules are:
  1. **Route protection:** `middleware.ts` does not redirect `/boards/<id>` to `/login` when the request carries a non-empty `invite` query parameter, with or without a `sevy_token` cookie. It still redirects every other unauthenticated request for `/`, `/boards/*`, `/my-tasks` and `/profile` (FE-22).
  2. **Mode:** `BoardDetailPage` runs in Guest mode whenever `invite` is present, also for a signed-in Member (requirements.md OD-16, approved in V8); the normal Member view is `/boards/<id>` without the parameter. The page passes the token to the API client only as the `inviteToken` option.
  3. **Requests:** in Guest mode the API client sends only the header `X-Invite-Token: <token>`, never `Authorization`, and only on `GET /api/boards/<id>` and `GET /api/cards/<id>/comments`. It never attaches the token to any other request. Guest mode never writes or clears the `sevy_token` cookie, never calls `login()` or `logout()`, and creates no authenticated session.
  4. **Read-only UI:** `KanbanBoard` receives `isReadOnly` and renders no create, edit, delete or assign control, no Card or Column form, and no `CardDragHandle`, so no element has `draggable`. `CardDetailModal` shows Comments read-only (no `CommentForm`, no edit control). Guest mode has no Search, no `NotificationBell`, no My Tasks link and no Profile link: `Header` shows only the brand when the path is `/boards/*` and `invite` is present.
  5. **Errors:** a 404 (invalid or revoked token) shows the not-found state, not a redirect. A 403 (token bound to another Board) shows the same not-found state. Any other `ApiError` shows a generic error state. Guest mode never redirects to `/login` and never shows the session-expired toast.
- **RATIONALE:** An invite link must work for a visitor with no account, and keeping the invite token off every other request means a leaked token reaches only read access to one Board. Dropping `draggable` and write controls keeps the UI honest about what the API allows.
- **EXAMPLE:** An Admin creates an invite link through the API and shares `/boards/<id>?invite=<token>`; the visitor sees the Columns, Cards and Comments with no buttons or drag handles, and no `sevy_token` cookie is set. A revoked link shows "not found".
- **VERIFY:** `grep -rn "X-Invite-Token" frontend/app frontend/components frontend/hooks frontend/context | wc -l` → `0` (the header name appears only in `lib/apiClient.ts`). Jest test for `apiClient` with a `fetch` spy: in Guest mode both permitted requests carry the invite header and no `Authorization`; any other call made with an `inviteToken` carries no invite header; a normal request carries no invite header. Playwright (users and invite link created through the API): an unauthenticated visit to `/boards/<id>?invite=<token>` stays on that URL, shows Columns and Cards, `page.locator('[draggable="true"]')` has count 0, no create button is visible, and no `sevy_token` cookie exists; an invalid token shows the not-found state and the URL does not change; `/boards/<id>` without the parameter redirects to `/login`; a signed-in Member opening the link sees the read-only view.

### FE-31 — My Tasks and the Comment thread
- **RULE:**
  - **My Tasks:** `app/my-tasks/page.tsx` is a Server Component that calls `GET /api/cards?assignee=me` and groups the `CardListItem` rows by `board_name` under one heading per Board. Each row shows the `title`, the `column_name` in a `BaseBadge`, and a `BaseButton` that opens `/boards/<board_id>?card=<id>`; because the button needs a handler, the row is the Client Component `components/card/MyTaskRow.tsx`. When there are no Cards the page shows an empty-state message.
  - **Thread:** `CommentList` receives the flat list ordered by `created_at` ascending (backend.md BE-06) and renders replies under their parent by `parent_id`. A Comment with `is_deleted` true renders as a tombstone placeholder, "This comment was deleted", showing no author content, and its replies stay in the thread. A Comment whose `updated_at` is later than `created_at` shows an "edited" indicator.
  - **Create and edit:** `CommentForm` and the edit form use controlled inputs (FE-21). Comments are not part of the Board page props, so `CardDetailModal` holds them in local state: the click handler that opens the modal loads `GET /api/cards/<id>/comments`, a create appends the returned Comment, and an edit replaces it, with no full page reload. Edit controls appear only on Comments where `author_id` equals the signed-in user's `id`, and an icon-only edit control has an `aria-label`.
- **RATIONALE:** Grouping and tombstones are presentation of data the API already shapes; keeping them in the UI layer keeps the API contracts untouched. A tombstone keeps a thread readable when a parent Comment is deleted.
- **EXAMPLE:** A deleted Comment with two replies shows "This comment was deleted" with both replies indented under it. A user with no assigned Cards sees "No tasks assigned to you yet" on `/my-tasks`.
- **VERIFY:** RTL test: `CommentList` with a tombstone and two replies renders the placeholder text, no `content`, and both replies; an edited Comment shows the indicator and an unedited one does not; creating and editing a Comment updates the list without navigation; Playwright: an assigned Card appears under its Board name on `/my-tasks`, and the empty state shows when none is assigned; `grep -c "BaseButton" frontend/components/card/MyTaskRow.tsx` → ≥ `1`.

### FE-32 — Team members and Invite Links are API-only in V1
- **RULE:** Team member management and Invite Link creation and revocation have no UI in V1 (requirements.md OD-14). The Frontend has no member panel, no member form and no invite-link components, and FE-02's component folders stay as they are; the only Frontend use of an Invite Link is the Guest view of FE-30.
- **RATIONALE:** The requirements define these as API features only; UI for them would be unrequested scope.
- **EXAMPLE:** An Admin adds a member through `POST /api/boards/<id>/members` with an API client; no screen in `app/` exists for it.
- **VERIFY:** `grep -rniE "member panel|MemberForm|InviteLink" frontend/app frontend/components | wc -l` → `0`; `ls frontend/components` lists exactly the six folders of FE-02.

### FE-33 — Board Detail role, analytics panel and Board creation
- **RULE:**
  - **Role source:** the Board payload carries no role. `app/boards/[id]/page.tsx` reads the signed-in user's role from `GET /api/boards/<id>/members`, taking the row whose `user_id` equals the user's own id, and passes `role` to Client Components.
  - **Guest_Mode:** the role is `guest` and the page makes no members request (a Guest has no JWT; FE-30).
  - **AnalyticsPanel:** `components/board/AnalyticsPanel.tsx` renders only when `role` is `admin` and calls `GET /api/boards/<id>/analytics`; for `member` and `guest` it is not rendered and the request is not made.
  - **Board creation:** `BoardForm` sends no `team_id`, so a Board created in the UI belongs to the requester's personal Team. The Dashboard lists the Boards of all Teams of the user.
- **RATIONALE:** No route lists Teams and the Board payload has no role field; the members route is the one source of the user's role, and a Guest has no JWT to call it with.
- **EXAMPLE:** An Admin opens `/boards/<id>`: the members response has a row with their `user_id` and role `admin`, and the analytics panel appears. A Member sees no panel. The Guest view at `/boards/<id>?invite=<token>` sends no members request.
- **VERIFY:** (not run) RTL test: `AnalyticsPanel` is rendered for role `admin` and absent for `member` and `guest`. Jest test with a `fetch` spy: Guest_Mode sends no request to `/members`; a signed-in page sends one and derives the role from the row with the user's own `user_id`. `grep -rn "team_id" frontend/components/board/BoardForm.tsx | wc -l` → `0`. `ls frontend/components/board | grep -c "AnalyticsPanel.tsx"` → `1`.
