# Sevy Design System

> **Canonical UI specification** for Sevy's web application and related webpages. This document consolidates the existing Sevy HTML reference and the supplied Sevy palette image into implementation-ready tokens and component rules.

**Relationship to `DESIGN.md`:** This file is the source of truth for exact design tokens, component dimensions, interaction states, and responsive breakpoints. `DESIGN.md` defines product experience, page composition, and visual direction. If guidance appears to conflict, use this file for exact UI values and update `DESIGN.md` to match.

---

## 1. Design Philosophy

### Visual identity

**Simple, flat, friendly.** Sevy uses a calm blue-to-mint identity, warm neutral canvas, white surfaces, compact Inter typography, and clear board/card metaphors.

- Calm, focused, and approachable
- Flat surfaces separated by tone and borders
- Cornflower blue for primary actions and active states
- Soft pastel colors for task labels and semantic feedback
- Minimal depth; shadows are reserved for overlays and active dragging

### Core principles

1. **Neutral first:** Canvas, surfaces, and text carry most of the interface.
2. **Blue marks action:** Primary blue identifies the next action, active selection, and focus.
3. **Gradient is atmospheric:** The supplied gradient is a brand treatment, not a functional UI color or default page fill.
4. **Borders create structure:** Use 1px borders and subtle surface differences before considering shadows.
5. **Board-first:** Boards, columns, and cards remain recognizable and easy to scan.
6. **Accessible by default:** Include visible focus, readable contrast, semantic feedback, and reduced-motion support.

---

## 2. Brand Palette Reference

### Supplied gradient

The supplied `SevyPallete.webp` is a wide, soft horizontal gradient that transitions through:

**Periwinkle → cornflower blue → sky blue → cyan → pale mint → cool near-white → icy blue.**

Approximate sampled reference colors (the source is a continuous gradient, not a set of discrete brand tokens):

| Reference stop | Approx. hex | Intended use |
|---|---|---|
| Periwinkle haze | `#888FDD` | Ambient brand accent |
| Cornflower blue | `#738CD9` | Brand emphasis |
| Soft sky blue | `#77A1D5` | Gradient transition |
| Cyan blue | `#92C4D8` | Gradient transition |
| Pale aqua | `#C8E9E6` | Soft atmosphere |
| Mint white | `#E3F7EE` | Light gradient region |
| Cool near-white | `#EDF7F7` | Light gradient region |
| Icy blue | `#D3E3F4` | Gradient transition |
| Light blue | `#89B0E6` | Gradient transition |
| Blue edge | `#6999DE` | Gradient edge accent |

These are visual reference samples, not replacements for the functional tokens below. Do not use them to create an unofficial second primary palette.

### Recommended CSS brand gradient

```css
:root {
  --brand-gradient: linear-gradient(
    105deg,
    #888FDD 0%,
    #738CD9 18%,
    #77A1D5 30%,
    #92C4D8 42%,
    #C8E9E6 55%,
    #E3F7EE 66%,
    #EDF7F7 76%,
    #D3E3F4 88%,
    #6999DE 100%
  );
}
```

**Usage:** restrained marketing hero/feature atmosphere, decorative glows, and selected brand illustrations. Keep text on a neutral/high-contrast content area. Do not use this gradient for task cards, form controls, labels, status badges, modal surfaces, or the default application canvas.

---

## 3. Canonical Color Tokens

The following values are sourced from the existing Sevy design-system HTML. Use these names and values consistently.

### Primary and accents

| Token | Hex | Role |
|---|---|---|
| `--primary-50` | `#F4F6FF` | Very soft selected/primary tint |
| `--primary-100` | `#CEDDF7` | Pale ice blue; soft informational tint |
| `--primary-200` | `#97B3F8` | Light blue; subtle emphasis and drag/drop outline |
| `--primary-500` | `#6D7BEC` | Primary brand/action color |
| `--primary-600` | `#5876EC` | Primary hover / vibrant cornflower |
| `--primary-700` | `#455BCA` | Primary active / deeper blue |
| `--periwinkle` | `#8A8DFB` | Decorative/supporting accent |

### Neutrals and backgrounds

| Token | Hex | Role |
|---|---|---|
| `--canvas` | `#F1EFEB` | Warm alabaster page background |
| `--surface` | `#FFFFFF` | Cards, inputs, navigation, dialogs |
| `--sunken` | `#F2FAF5` | Off-white mint inset regions and column backgrounds |
| `--line` | `#E5E1DA` | Default borders and dividers |
| `--line-strong` | `#D2CEC7` | Stronger borders and secondary button outlines |
| `--field` | `#A0A5B5` | Form-control border |
| `--ink` | `#1F2430` | Primary text |
| `--ink-muted` | `#4F586A` | Secondary text and metadata |
| `--ink-subtle` | `#6B7385` | Placeholder and disabled text |

### Semantic colors

| Token | Hex | Role |
|---|---|---|
| `--success` | `#1C6C55` | Success foreground |
| `--success-soft` | `#B8E2D8` | Soft success background |
| `--warning` | `#F5B63D` | Warning accent |
| `--warning-soft` | `#FFF4DB` | Warning background |
| `--warning-ink` | `#7A5200` | Warning foreground |
| `--danger` | `#D13438` | Destructive/error action |
| `--danger-hover` | `#B52B2F` | Destructive hover |
| `--danger-ink` | `#A6262A` | Destructive/error foreground |
| `--danger-soft` | `#FDECEC` | Error background |

### Label color pairs

| Pair | Background | Foreground | Typical use |
|---|---|---|---|
| Green | `--green-bg: #B8E2D8` | `--green-fg: #1C6C55` | Completed / positive |
| Yellow | `--yellow-bg: #FFF1C2` | `--yellow-fg: #7A5200` | Due soon / attention |
| Orange | `--orange-bg: #FFE3CC` | `--orange-fg: #8F4300` | Priority / in review |
| Red | `--red-bg: #FDE0E0` | `--red-fg: #A6262A` | Bug / overdue |
| Purple | `--purple-bg: #E8E9FF` | `--purple-fg: #4A4FB5` | Design / creative |
| Blue | `--blue-bg: #CEDDF7` | `--blue-fg: #3F51B5` | Planning / information |
| Teal | `--teal-bg: #D5F3F1` | `--teal-fg: #0B6B66` | Research / secondary category |
| Pink | `--pink-bg: #FCE1EF` | `--pink-fg: #9C2A66` | Supporting category |

### CSS token foundation

```css
:root {
  /* Primary */
  --primary-50: #F4F6FF;
  --primary-100: #CEDDF7;
  --primary-200: #97B3F8;
  --primary-500: #6D7BEC;
  --primary-600: #5876EC;
  --primary-700: #455BCA;
  --periwinkle: #8A8DFB;

  /* Neutrals */
  --canvas: #F1EFEB;
  --surface: #FFFFFF;
  --sunken: #F2FAF5;
  --line: #E5E1DA;
  --line-strong: #D2CEC7;
  --field: #A0A5B5;

  /* Text */
  --ink: #1F2430;
  --ink-muted: #4F586A;
  --ink-subtle: #6B7385;

  /* Semantic */
  --success: #1C6C55;
  --success-soft: #B8E2D8;
  --warning: #F5B63D;
  --warning-soft: #FFF4DB;
  --warning-ink: #7A5200;
  --danger: #D13438;
  --danger-hover: #B52B2F;
  --danger-ink: #A6262A;
  --danger-soft: #FDECEC;

  /* Label pairs */
  --green-bg: #B8E2D8; --green-fg: #1C6C55;
  --yellow-bg: #FFF1C2; --yellow-fg: #7A5200;
  --orange-bg: #FFE3CC; --orange-fg: #8F4300;
  --red-bg: #FDE0E0; --red-fg: #A6262A;
  --purple-bg: #E8E9FF; --purple-fg: #4A4FB5;
  --blue-bg: #CEDDF7; --blue-fg: #3F51B5;
  --teal-bg: #D5F3F1; --teal-fg: #0B6B66;
  --pink-bg: #FCE1EF; --pink-fg: #9C2A66;

  /* Shape and elevation */
  --r-sm: 6px;
  --r-md: 8px;
  --r-lg: 12px;
  --r-full: 9999px;
  --shadow-overlay: 0 8px 24px rgb(31 36 48 / 0.12);

  /* Brand atmosphere */
  --brand-gradient: linear-gradient(
    105deg,
    #888FDD 0%,
    #738CD9 18%,
    #77A1D5 30%,
    #92C4D8 42%,
    #C8E9E6 55%,
    #E3F7EE 66%,
    #EDF7F7 76%,
    #D3E3F4 88%,
    #6999DE 100%
  );
}
```

---

## 4. Typography

### Font family

```css
--font-sans: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
--font-mono: ui-monospace, SFMono-Regular, Menlo, monospace;
```

Use Inter at weights **400, 500, and 600**. Sentence case is the default.

### Type scale

| Role | Size / line height | Weight | Usage |
|---|---:|---:|---|
| Display | 30 / 36 px | 600 | Marketing/product display heading |
| H1 | 24 / 32 px | 600 | Page title |
| H2 | 20 / 28 px | 600 | Section title |
| H3 | 16 / 24 px | 600 | Card/column subsection title |
| Body | 14 / 20 px | 400 | Default interface copy |
| Strong | 14 / 20 px | 500 | Emphasized body and control labels |
| Muted | 14 / 20 px | 400 | Secondary copy |
| Caption | 12 / 16 px | 400 | Metadata, helper text, timestamps |

### Base CSS

```css
html {
  background: var(--canvas);
  scroll-behavior: smooth;
}

body {
  font-family: var(--font-sans);
  font-size: 14px;
  line-height: 20px;
  color: var(--ink);
  -webkit-font-smoothing: antialiased;
}

:focus-visible {
  outline: 2px solid var(--primary-500);
  outline-offset: 2px;
}

a {
  color: var(--primary-600);
  text-decoration: none;
}

a:hover {
  color: var(--primary-700);
  text-decoration: underline;
}
```

---

## 5. Spacing, Radius & Elevation

### Spacing scale

Use a 4px grid.

| Step | Value | Typical use |
|---|---:|---|
| 1 | 4px | Tight icon/text or label gap |
| 2 | 8px | Default compact gap; card content gap |
| 3 | 12px | Input padding / compact component spacing |
| 4 | 16px | Standard component and column gap |
| 6 | 24px | Panel padding and related groups |
| 8 | 32px | Module separation |
| 12 | 48px | Section separation |

### Radius

| Token | Value | Usage |
|---|---:|---|
| `--r-sm` | 6px | Chips and labels |
| `--r-md` | 8px | Buttons, inputs, task cards |
| `--r-lg` | 12px | Columns, panels, modals |
| `--r-full` | 9999px | Pills, avatars, switches |

### Elevation

Resting surfaces are flat. Use border and background tone to distinguish levels.

| Layer | Treatment |
|---|---|
| Base | `--canvas` |
| Inset | `--sunken` |
| Raised/resting | `--surface` + 1px `--line` border |
| Overlay | `--surface` + `--shadow-overlay` |
| Dragging card | Overlay shadow while actively dragged |

```css
/* The only standard elevation shadow */
--shadow-overlay: 0 8px 24px rgb(31 36 48 / 0.12);
```

Do not add shadows to ordinary cards, columns, panels, or navigation.

---

## 6. Component Specifications

### Buttons

**Variants**
- Primary: `--primary-500`, white text; hover `--primary-600`; active `--primary-700`.
- Secondary: white surface, `--ink` text, `--line-strong` border; hover `--sunken`.
- Ghost: transparent surface, muted text; hover `--sunken`.
- Danger: `--danger`, white text; hover `--danger-hover`.

**Sizes**
- Small: 32px high, 12px horizontal padding.
- Medium: 36px high, 16px horizontal padding.
- Large: 44px high, 20px horizontal padding, 16px text.
- Icon-only: 36px (small icon-only: 32px).

**Rules**
- One primary action per region.
- Use verbs for labels.
- Icon-only buttons require an accessible name (`aria-label`).
- Include hover, active, focus, disabled, and loading states.
- Disabled controls must not look actionable.

```css
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 36px;
  padding: 0 16px;
  border-radius: var(--r-md);
  font: inherit;
  font-weight: 500;
  border: 1px solid transparent;
  white-space: nowrap;
}

.btn-primary { background: var(--primary-500); color: #fff; }
.btn-primary:hover { background: var(--primary-600); }
.btn-primary:active { background: var(--primary-700); }

.btn-secondary {
  background: var(--surface);
  color: var(--ink);
  border-color: var(--line-strong);
}
.btn-secondary:hover { background: var(--sunken); }

.btn-ghost { background: transparent; color: var(--ink-muted); }
.btn-ghost:hover { background: var(--sunken); color: var(--ink); }

.btn-danger { background: var(--danger); color: #fff; }
.btn-danger:hover { background: var(--danger-hover); }
```

### Form controls

- Labels sit above fields.
- Standard input/select height: **36px**.
- Standard horizontal padding: **12px**.
- Border radius: **8px**.
- Default border: `--field`; hover border: `--ink-subtle`.
- Focus: 2px `--primary-500` outline.
- Disabled: `--sunken` background, muted text, neutral border.
- Error: `--danger` border plus explanatory text and icon.
- Textarea minimum height: **80px**, with 8px vertical and 12px horizontal padding.
- Inline edit: transparent at rest, subtle inset background on hover, white surface and primary border on focus.

```css
.input, .select, .textarea {
  width: 100%;
  height: 36px;
  padding: 0 12px;
  border-radius: var(--r-md);
  border: 1px solid var(--field);
  background: var(--surface);
  color: var(--ink);
  font: inherit;
}

.textarea {
  height: auto;
  min-height: 80px;
  padding: 8px 12px;
  resize: vertical;
}
```

### Checkboxes, radios, and switches

- Checkbox/radio control size: **16px**.
- Checkbox radius: **6px**; radio is circular.
- Checked state uses `--primary-500`.
- Switch size: **36 × 20px**, with a 16px thumb.
- All controls require visible keyboard focus and a usable label.
- Disabled controls must have a distinct disabled treatment.

### Labels and status badges

- Task labels use the eight pastel foreground/background pairs defined in the token section.
- Label height: **20px**, horizontal padding: **8px**, radius: **6px**.
- Status badges are pill-shaped, **20px** high, with a short text label and optional 6px status dot.
- Badge padding: 10px horizontal; use neutral, info, success, warning, and danger semantic styles.
- Keep text legible; never use saturated fills as the default label style.

### Avatars

- Supported sizes: **24px, 32px, 40px**.
- Circular shape.
- Stacked avatars overlap slightly and retain a 2px surface-colored separation ring.
- Provide initials or an accessible alternative when no image is available.

### Task cards

- Background: `--surface`.
- Border: 1px solid `--line`.
- Radius: `--r-md` (8px).
- Padding: 12px.
- Internal gap: 8px.
- Hover: strengthen border to `--line-strong`.
- Selected: `--primary-50` background and `--primary-500` border.
- Dragging: slight 2-degree tilt and `--shadow-overlay`; this is the intentional exception to flat resting surfaces.
- Drop placeholder: 2px dashed `--primary-200` border and `--primary-50` background.
- Metadata uses 12px/16px muted text.

### Board and columns

- Navigation bar: **56px** high.
- Board: horizontal flex layout, **16px** gap, horizontal overflow enabled.
- Column width: **288px**, non-shrinking.
- Column background: `--sunken`.
- Column radius: `--r-lg` (12px).
- Column padding: 8px; card stack gap: 8px.
- Column header: 16px/24px semibold; count uses a neutral pill.
- Board columns scroll horizontally; the overall page must not acquire unintended horizontal overflow.

### Overlays and feedback

- Modal: maximum width **560px**, white surface, 1px border, 12px radius, 24px padding, overlay shadow.
- Modal backdrop: solid ink tint at approximately 40%; no backdrop blur by default.
- Menu: white surface, border, 12px radius, overlay shadow; compact 32px menu rows.
- Toast: white surface, border, 12px radius, overlay shadow; max width 320px.
- Tooltip: ink background, white text, 12px/16px, 8px radius.
- Banners: compact 8px × 12px padding, 8px radius, semantic background/foreground.
- Use shadow only for elements that float above the page.

### Tabs, progress, empty, and loading states

- Tabs: 40px high; active tab uses ink text and a 2px primary underline.
- Progress track: 8px high; primary fill, success fill when complete.
- Empty states: centered content with concise explanation and one clear next action.
- Skeletons: use `--sunken` with a subtle pulse; disable animation when reduced motion is requested.
- Loading states must preserve layout and communicate that work is in progress.

---

## 7. Layout & Responsive Rules

### Application layout

| Element | Standard |
|---|---|
| Top navigation | 56px high |
| Main page background | `--canvas` |
| Main content surface | `--surface` |
| Board column width | 288px |
| Board/column gap | 16px |
| Column internal padding | 8px |
| Task card padding | 12px |

### Responsive breakpoints

These breakpoints reflect the existing Sevy HTML reference. Use them consistently rather than introducing competing breakpoint systems.

| Range | Behavior |
|---|---|
| `> 860px` | Full multi-column layouts where content permits |
| `761–860px` | Three- and four-column content grids reduce to two columns |
| `561–760px` | Compact horizontal structures; state tables may scroll |
| `≤ 700px` | Hide the optional fixed-width search field when space is constrained |
| `≤ 560px` | Two-/three-/four-column grids become one column; page padding reduces to 16px; type-spec rows stack |

### Responsive implementation notes

- Main desktop content can use a centered max-width container (the HTML reference uses **1080px**) with 24px side padding.
- At widths up to 560px, use 32px vertical and 16px horizontal main padding.
- Keep board columns at a usable fixed width and allow horizontal board scrolling.
- Do not shrink task cards or columns into unreadable layouts.
- On small screens, stack marketing sections and use full-width controls.
- Keep primary actions accessible when navigation collapses.
- Avoid page-level horizontal overflow.

---

## 8. Motion & Interaction

- Use short, restrained transitions for color, border, and background changes (approximately 150ms in the HTML reference).
- Dragging cards may tilt slightly; remove the tilt when reduced motion is enabled.
- Loading skeletons may pulse gently.
- Respect `prefers-reduced-motion: reduce` by disabling non-essential animation and transitions.
- Hover states must have equivalent keyboard focus states.
- Provide clear feedback for save, move, delete, validation, and network states.

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation: none !important;
    transition: none !important;
  }

  .card.dragging {
    transform: none;
  }
}
```

---

## 9. Accessibility Requirements

- Use semantic HTML landmarks and logical heading order.
- Ensure keyboard access to all interactive elements.
- Provide a visible 2px focus outline using `--primary-500`.
- Icon-only controls require accessible names.
- Associate labels, helper text, and validation messages with their form controls.
- Do not rely on color alone for status, errors, or selection.
- Maintain sufficient contrast for text and control boundaries.
- Support reduced motion.
- Ensure controls remain usable at narrow viewport widths and with touch input.

---

## 10. Do / Don't

### Do

- Use warm neutral canvas, white bordered surfaces, and mint-tinted inset regions.
- Use `--primary-500` for the main action and active state.
- Use the brand gradient sparingly for marketing atmosphere.
- Keep labels pastel with dark paired text.
- Use borders and surface tones to create hierarchy.
- Reserve shadows for overlays and actively dragged cards.
- Keep board columns horizontally scrollable on narrow screens.

### Don't

- Do not apply the gradient to every card, button, or page section.
- Do not use shadows on resting cards, columns, or panels.
- Do not add unapproved colors that compete with the canonical palette.
- Do not use saturated label fills or gradient status indicators.
- Do not use color as the only status signal.
- Do not force board columns into narrow mobile grids.
- Do not create inconsistent radii, spacing, or type scales.

---

## 11. Implementation Checklist

Before shipping a page or component, verify:

- [ ] It uses the canonical Sevy tokens rather than duplicated hard-coded colors.
- [ ] The gradient is decorative/brand-led, not a functional surface color.
- [ ] Typography uses Inter and the defined scale.
- [ ] Spacing follows the 4px grid.
- [ ] Component radius and dimensions match this document.
- [ ] Resting surfaces use borders, not shadows.
- [ ] Only one primary action dominates each local region.
- [ ] Hover, active, focus, disabled, loading, and error states are covered where applicable.
- [ ] Status and validation are understandable without color alone.
- [ ] Board columns remain usable on mobile through horizontal scrolling.
- [ ] Reduced-motion preferences are respected.

---

## 12. Source & Change Control

- **Existing source:** uploaded `design system sevy.html` (Sevy component and token reference).
- **Brand reference:** uploaded `SevyPallete.webp` (visual gradient direction; sampled stops are approximate).
- **Experience guide:** [`DESIGN.md`](./DESIGN.md).

When changing a token or component:
1. Update the canonical value/specification in this file.
2. Update the corresponding implementation in the HTML/CSS source.
3. Update `DESIGN.md` only if the product experience or page-level guidance changes.
4. Check that no duplicate or conflicting values remain.
